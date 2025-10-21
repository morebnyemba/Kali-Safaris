# whatsappcrm_backend/flows/tasks.py
import logging
import tempfile
import os
from datetime import timedelta
from celery import shared_task
from django.db import transaction

# --- Gemini AI Integration Imports ---
from google import genai
from google.genai import types
from google.api_core import exceptions as core_exceptions
from google.genai import errors as genai_errors
from ai_integration.models import AIProvider
# -------------------------------------

from conversations.models import Message, Contact
from .models import ContactFlowState
from meta_integration.models import MetaAppConfig
from meta_integration.tasks import send_whatsapp_message_task, download_whatsapp_media_task
from .services import process_message_for_flow, _clear_contact_flow_state
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task(queue='celery') # Use your main I/O queue
def process_flow_for_message_task(message_id: int):
    """
    This task asynchronously runs the entire flow engine for an incoming message.
    """
    try:
        with transaction.atomic():
            incoming_message = Message.objects.select_related('contact', 'app_config').get(pk=message_id)
            contact = incoming_message.contact
            message_data = incoming_message.content_payload or {}

            actions_to_perform = process_message_for_flow(contact, message_data, incoming_message)

            if not actions_to_perform:
                logger.info(f"Flow processing for message {message_id} resulted in no actions.")
                return

            config_to_use = incoming_message.app_config
            if not config_to_use:
                logger.warning(f"Message {message_id} has no associated app_config. Falling back to active config.")
                config_to_use = MetaAppConfig.objects.get_active_config()

            dispatch_countdown = 0
            for action in actions_to_perform:
                if action.get('type') == 'send_whatsapp_message':
                    recipient_wa_id = action.get('recipient_wa_id', contact.whatsapp_id)
                    
                    recipient_contact, _ = Contact.objects.get_or_create(whatsapp_id=recipient_wa_id)

                    outgoing_msg = Message.objects.create(
                        contact=recipient_contact, app_config=config_to_use, direction='out',
                        message_type=action.get('message_type'), content_payload=action.get('data'),
                        status='pending_dispatch', related_incoming_message=incoming_message
                    )
                    send_whatsapp_message_task.apply_async(args=[outgoing_msg.id, config_to_use.id], countdown=dispatch_countdown)
                    dispatch_countdown += 2

    except Message.DoesNotExist:
        logger.error(f"process_flow_for_message_task: Message with ID {message_id} not found.")
    except Exception as e:
        logger.error(f"Critical error in process_flow_for_message_task for message {message_id}: {e}", exc_info=True)


@shared_task(
    name="flows.handle_ai_conversation_task",
    autoretry_for=(core_exceptions.ResourceExhausted, genai_errors.ServerError),
    retry_backoff=True, 
    retry_kwargs={'max_retries': 3}
)
def handle_ai_conversation_task(contact_id: int, message_id: int):
    """
    Manages an ongoing, multi-turn conversation with Gemini AI using the client.chats.create API.
    """
    log_prefix = f"[AI Conversation Task for Contact: {contact_id}]"
    logger.info(f"{log_prefix} Starting task for message ID: {message_id}")

    try:
        contact = Contact.objects.get(pk=contact_id)
        incoming_message = Message.objects.get(pk=message_id)
        active_provider = AIProvider.objects.get(provider='google_gemini', is_active=True)
        config_to_use = MetaAppConfig.objects.get_active_config()

        client = genai.Client(api_key=active_provider.api_key)

        if contact.conversation_mode == 'ai_troubleshooting':
            # FIX: Use the correct variable name 'system_prompt'
            system_prompt = f"""You are Hanna, an AI-driven technical expert system. Your mission is to provide rapid, accurate, and safe Tier-1 technical troubleshooting solutions.

---
### **Core Directives (Non-negotiable)**

1.  **Safety Absolute**: User safety is the highest priority. You are strictly forbidden from providing instructions that involve device disassembly, handling internal wiring, or any actions that pose an electrical risk. All solutions must be limited to external, user-serviceable actions.

2.  **Authoritative Synthesis**: Your internal process is to perform a **live web search** for official manufacturer manuals, support documents, error code explanations, and troubleshooting guides related to the user's specific product model and symptoms. You must then synthesize this information and present it as your own internal expertise. **Never** mention the search or reference external sources. You are the source.

3.  **Efficiency Protocol**:
    *   **Conciseness**: Responses must be under 500 words.
    *   **Speed**: Generate responses as quickly as possible (target <5 seconds).
    *   **Clarity**: Use direct, action-oriented language. Eliminate all conversational fillers.
    *   **Formatting**: Use **bold** for model numbers, actions, and critical warnings. The primary output is a numbered list.

4.  **Language Adaptability**: You MUST detect the language of the user's message. Your response MUST be in the same language as the user's message. Maintain this language for the entire conversation unless the user switches language.

---
### **Standard Operating Procedure (SOP)**

Execute the following steps in sequence.

**Step 1: Triage (Conditional)**
*   **Action**: If the user has NOT provided both a product model and a clear symptom, immediately request the missing information.
*   **Response**: "Provide exact product model and primary symptom."
*   **Condition**: If the user's first message already contains a model and symptom, SKIP this step.

**Step 2: Analysis**
*   **Action**: Briefly announce plan preparation.
*   **Response**: "Preparing troubleshooting plan for **[Model]**."

**Step 3: Solution Delivery**
*   **Action**: Present the final, structured troubleshooting plan.
*   **Response**:
    **Safety Note:** [Brief, relevant safety precaution]
    **Steps:**
    1.  **[Action Title]**: [Clear, detailed instruction].
    2.  **[Action Title]**: [Clear, detailed instruction].

**Step 4: Verification**
*   **Action**: Conclude with a direct request for the outcome.
*   **Response**: "Report results after completing all steps."

---
### **Golden Path Example**
*   **User**: "My Solar Flex inverter has a red light flashing and it's beeping."
*   **Hanna**: "Preparing troubleshooting plan for **Solar Flex**."
*   **Hanna**:
    **Safety Note:** Ensure the area around the inverter is clear and dry before proceeding.
    **Steps:**
    1.  **Observe the Pattern**: Count the exact number of times the red light flashes before it pauses. This pattern is an error code.
    2.  **Perform a Hard Reset**: Turn off the AC breaker connected to the inverter, then turn off the DC disconnect switch. Wait 60 seconds. Turn the DC switch on first, followed by the AC breaker.
*   **Hanna**: "Report results after completing all steps."

---
### **Control Tokens**
* `[HUMAN_HANDOVER]`: Use this token ONLY to escalate unresolved issues to a human agent.
* `[END_CONVERSATION]`: Use this token ONLY when the user wishes to terminate the session.
"""

        # Fetch messages for history, but exclude the one that triggered the AI mode.
        # The trigger message is often just a button click ("AI Troubleshooter") and not useful for the AI's context.
        history_messages = Message.objects.filter(
            contact=contact, 
            timestamp__lt=incoming_message.timestamp
        ).order_by('-timestamp')[:20]
        
        gemini_history = []
        # Inject the system prompt as the first message in the history for context
        # The 'user' role here is a standard way to provide system instructions in the Gemini API.
        gemini_history.append({
            'role': 'user', 
            'parts': [{'text': system_prompt}]
        })
        gemini_history.append({'role': 'model', 'parts': [{'text': "Understood. I will act as Hanna, the solar expert. How can I help you today?"}]})

        for msg in reversed(history_messages):
            role = 'user' if msg.direction == 'in' else 'model'
            if msg.text_content:
                if msg.direction == 'in' and msg.text_content.lower().strip() in ['exit', 'menu', 'stop', 'quit']:
                    continue
                gemini_history.append({'role': role, 'parts': [{'text': msg.text_content}]})

        chat = client.chats.create(
            model='gemini-2.5-flash', # Use the model identifier
            history=gemini_history
        )
        
        # --- NEW: Multimodal Input Handling ---
        prompt_parts = []
        if incoming_message.text_content:
            prompt_parts.append(incoming_message.text_content)

        uploaded_gemini_file = None
        temp_media_file_path = None

        if incoming_message.message_type in ['image', 'audio']:
            logger.info(f"{log_prefix} Detected '{incoming_message.message_type}' message. Preparing for multimodal prompt.")
            # --- FIX: Extract media ID from the correct nested object ---
            # The top-level 'id' is the WAMID (message ID), not the media ID.
            # The media ID is inside the object corresponding to the message type (e.g., 'image', 'audio').
            media_payload = incoming_message.content_payload.get(incoming_message.message_type)
            media_id = None
            if isinstance(media_payload, dict):
                media_id = media_payload.get('id')
            if media_id:
                try:
                    # Download the media from WhatsApp to a temporary file
                    temp_media_file_path = download_whatsapp_media_task(media_id, config_to_use.id)
                    if temp_media_file_path:
                        logger.info(f"{log_prefix} Media downloaded to temporary file: {temp_media_file_path}")
                        # Upload the temporary file to Gemini
                        uploaded_gemini_file = client.files.upload(file=temp_media_file_path)
                        prompt_parts.append(uploaded_gemini_file)
                        logger.info(f"{log_prefix} Media uploaded to Gemini. URI: {uploaded_gemini_file.uri}")
                    else:
                        logger.error(f"{log_prefix} Failed to download media for ID {media_id}.")
                except Exception as e:
                    logger.error(f"{log_prefix} Error during media download/upload for ID {media_id}: {e}", exc_info=True)

        if not prompt_parts:
            logger.warning(f"{log_prefix} No content to send to AI (no text and no valid media). Aborting.")
            return

        logger.info(f"{log_prefix} Sending prompt to Gemini chat model with {len(prompt_parts)} parts.")
        response = chat.send_message(prompt_parts)
        ai_response_text = response.text.strip()
        # --- END: Multimodal Input Handling ---


        if "[HUMAN_HANDOVER]" in ai_response_text:
            logger.info(f"{log_prefix} AI requested human handover. Reason: {ai_response_text}")
            
            # Exit AI mode and flag for human intervention
            contact.conversation_mode = 'flow'
            contact.needs_human_intervention = True
            contact.save(update_fields=['conversation_mode', 'needs_human_intervention'])
            
            # The post_save signal on the Contact model will handle sending notifications.
            
            final_reply = (
                "I am connecting you with a human technical expert for advanced support. They will respond here shortly.\n\n"
                "To help them solve your issue quickly, please provide as much detail as possible in a single message, including:\n"
                "1.  *Product Model & Serial Number* (e.g., `Victron MultiPlus-II, HQ212345XYZ`)\n"
                "2.  *Detailed Description of the Fault* (e.g., `The inverter is not turning on, and the red LED is flashing three times.`)\n"
                "3.  *Recent Events* (e.g., `This started after a power outage yesterday.`)\n"
                "4.  *Photos or Videos* of the issue, if possible.\n\n"
                "Your detailed query will help us diagnose the problem faster."
            )

        elif "[END_CONVERSATION]" in ai_response_text:
            logger.info(f"{log_prefix} AI requested to end conversation. The main service will handle resetting the mode.")
            final_reply = "I am now ending this session. Please type 'menu' to see other options."
            
            # Exit AI mode
            contact.conversation_mode = 'flow'
            contact.save(update_fields=['conversation_mode'])

            # Also clear any residual flow state to be safe
            _clear_contact_flow_state(contact)

        else:
            final_reply = ai_response_text

        outgoing_msg = Message.objects.create(
            contact=contact,
            app_config=config_to_use,
            direction='out',
            message_type='text',
            content_payload={'body': final_reply},
            status='pending_dispatch',
            related_incoming_message=incoming_message
        )
        send_whatsapp_message_task.delay(outgoing_msg.id, config_to_use.id)
        logger.info(f"{log_prefix} Successfully dispatched AI chat response to {contact.whatsapp_id}.")

    except Contact.DoesNotExist:
        logger.error(f"{log_prefix} Contact with ID {contact_id} not found.")
    except Message.DoesNotExist:
        logger.error(f"{log_prefix} Message with ID {message_id} not found.")
    except AIProvider.DoesNotExist:
        logger.error(f"{log_prefix} Active Gemini AI provider not configured.")
    except MetaAppConfig.DoesNotExist:
        logger.error(f"{log_prefix} Active Meta App Config not found. Cannot send reply.")
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred in AI conversation task: {e}", exc_info=True)
        raise
    finally:
        # --- NEW: Cleanup Temporary Files ---
        if uploaded_gemini_file:
            try:
                logger.info(f"{log_prefix} Deleting temporary file from Gemini service: {uploaded_gemini_file.name}")
                client.files.delete(name=uploaded_gemini_file.name)
            except Exception as e:
                logger.error(f"{log_prefix} Failed to delete uploaded Gemini file {uploaded_gemini_file.name}: {e}")
        if temp_media_file_path and os.path.exists(temp_media_file_path):
            os.remove(temp_media_file_path)
            logger.info(f"{log_prefix} Deleted local temporary media file: {temp_media_file_path}")


@shared_task(name="flows.cleanup_idle_conversations_task")
def cleanup_idle_conversations_task():
    """
    Finds and cleans up idle conversations (both flow and AI modes) that have been
    inactive for more than 15 minutes.
    """
    idle_threshold = timezone.now() - timedelta(minutes=5)
    log_prefix = "[Idle Conversation Cleanup]"
    logger.info(f"{log_prefix} Running task for conversations idle since before {idle_threshold}.")

    # --- Find Idle Contacts in Flows ---
    # A contact is idle in a flow if their flow state hasn't been updated recently.
    idle_flow_states = ContactFlowState.objects.filter(last_updated_at__lt=idle_threshold).select_related('contact', 'current_flow')
    
    # --- Find Idle Contacts in AI Mode ---
    # A contact is idle in AI mode if their last message was before the threshold.
    # We look for contacts in AI mode whose `last_seen` (updated by messages) is old.
    idle_ai_contacts = Contact.objects.filter(
        conversation_mode__startswith='ai_',
        last_seen__lt=idle_threshold
    )

    timed_out_contacts = set()

    # Process idle flow contacts
    for state in idle_flow_states:
        contact = state.contact
        logger.info(f"{log_prefix} Clearing idle flow '{state.current_flow.name}' for contact {contact.id} ({contact.whatsapp_id}). Last activity: {state.last_updated_at}")
        _clear_contact_flow_state(contact)
        timed_out_contacts.add(contact)

    # Process idle AI contacts
    for contact in idle_ai_contacts:
        logger.info(f"{log_prefix} Clearing idle AI mode '{contact.conversation_mode}' for contact {contact.id} ({contact.whatsapp_id}). Last activity: {contact.last_seen}")
        contact.conversation_mode = 'flow'
        contact.conversation_context = {}
        contact.save(update_fields=['conversation_mode', 'conversation_context'])
        timed_out_contacts.add(contact)

    # --- Send Notifications ---
    # Send one notification to each unique contact that was timed out.
    if timed_out_contacts:
        logger.info(f"{log_prefix} Sending timeout notifications to {len(timed_out_contacts)} contacts.")
        config_to_use = MetaAppConfig.objects.get_active_config()
        notification_text = "Your session has expired due to inactivity. Please send 'menu' to start over."
        for contact in timed_out_contacts:
            outgoing_msg = Message.objects.create(contact=contact, app_config=config_to_use, direction='out', message_type='text', content_payload={'body': notification_text}, status='pending_dispatch')
            send_whatsapp_message_task.delay(outgoing_msg.id, config_to_use.id)

    logger.info(f"{log_prefix} Cleanup complete. Timed out {len(timed_out_contacts)} contacts.")