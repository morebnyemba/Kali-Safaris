# whatsappcrm_backend/flows/whatsapp_flow_response_processor.py
"""
Service for processing WhatsApp Flow responses and mapping them to existing models.
Handles the conversion of flow response data into InstallationRequest, SolarCleaningRequest, etc.
"""

import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from .models import WhatsAppFlow, WhatsAppFlowResponse
from conversations.models import Contact
from customer_data.models import InstallationRequest, SolarCleaningRequest, CustomerProfile, SiteAssessmentRequest, LoanApplication, Order
from meta_integration.utils import send_whatsapp_message

logger = logging.getLogger(__name__)

class WhatsAppFlowResponseProcessor:
    """
    Processes WhatsApp Flow responses and creates appropriate business entities.
    """
    
    @staticmethod
    def process_response(whatsapp_flow: WhatsAppFlow, contact: Contact, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Pure data processor: Updates the contact's flow context with WhatsApp flow response data.
        Should be called as a task from services.py when a flow response is received.
        Args:
            whatsapp_flow: The WhatsAppFlow instance
            contact: The contact who submitted the response
            response_data: The response payload from Meta
        Returns:
            Dict with status and notes, or None if failed
        """
        try:
            # Save the flow response for audit/history
            with transaction.atomic():
                WhatsAppFlowResponse.objects.create(
                    whatsapp_flow=whatsapp_flow,
                    contact=contact,
                    flow_token=response_data.get('flow_token', ''),
                    response_data=response_data,
                    is_processed=True
                )

            # Update the flow context for the contact (if in a flow)
            from .models import ContactFlowState
            flow_state = ContactFlowState.objects.filter(contact=contact).first()
            if flow_state:
                # Merge WhatsApp flow data into the flow context (top-level and under a subkey for compatibility)
                context = flow_state.flow_context_data or {}
                wa_data = response_data.get('data', response_data)
                # Merge at top level
                context.update(wa_data)
                # Also keep under a subkey for backward compatibility
                context['whatsapp_flow_data'] = wa_data
                # Set the flag for transition condition
                context['whatsapp_flow_response_received'] = True
                flow_state.flow_context_data = context
                flow_state.last_updated_at = timezone.now()
                flow_state.save(update_fields=["flow_context_data", "last_updated_at"])
                logger.info(f"Updated flow context for contact {contact.id} with WhatsApp flow data and set whatsapp_flow_response_received=True.")
                return {"success": True, "notes": "Flow context updated with WhatsApp flow data and response flag set."}
            else:
                logger.info(f"No active flow state for contact {contact.id} when processing WhatsApp flow response.")
                return {"success": False, "notes": "No active flow state for contact."}
        except Exception as e:
            logger.error(f"Error processing WhatsApp flow response: {e}", exc_info=True)
            return None

    # --- Handler stubs for all WhatsApp-based flows ---

    @staticmethod
    def _handle_site_inspection_whatsapp(flow_response, contact, response_data):
        """Process Site Inspection WhatsApp flow response and resume conversational flow for extra info (e.g., location pin)."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'assessment_full_name', 'assessment_address', 'assessment_contact_info', 'assessment_type'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[SiteInspection] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            # Example: Save or update SiteAssessmentRequest here
            logger.info(f"[SiteInspection] Processed for {data.get('assessment_full_name')}")

            feedback = (
                f"Your *site inspection* request has been submitted!\n"
                f"We will contact you to confirm details."
            )
            # If location pin is required but not collected in WhatsApp flow, resume conversational flow to collect it
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "site_assessment_request": data.get('assessment_full_name')}, None)
                    logger.info(f"[SiteInspection] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[SiteInspection] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[SiteInspection] Error: {e}", exc_info=True)
            return False, str(e)



    @staticmethod
    def _handle_custom_furniture_installation_whatsapp(flow_response, contact, response_data):
        """Process Custom Furniture Installation WhatsApp flow response: create InstallationRequest, feedback, and resume conversational flow for extra info (e.g., location pin)."""
        from customer_data.models import InstallationRequest, CustomerProfile
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'order_number', 'furniture_type', 'full_name', 'contact_phone', 'address'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[CustomFurniture] Missing required field: {field}")
                    return False, f"Missing required field: {field}"

            # Find or create customer profile
            customer, _ = CustomerProfile.objects.get_or_create(
                phone_number=data['contact_phone'],
                defaults={
                    'full_name': data['full_name'],
                }
            )

            # Create InstallationRequest
            inst = InstallationRequest.objects.create(
                customer=customer,
                installation_type='custom_furniture',
                order_number=data['order_number'],
                full_name=data['full_name'],
                address=data['address'],
                contact_phone=data['contact_phone'],
                alternative_contact_name=data.get('alt_contact_name') or '',
                alternative_contact_number=data.get('alt_contact_phone') or '',
                preferred_datetime=data.get('preferred_date') or '',
                availability=data.get('availability') or '',
                notes=data.get('specifications') or '',
            )
            logger.info(f"[CustomFurniture] Created InstallationRequest {inst.id} for {customer.full_name}")

            # Feedback message
            feedback = (
                f"Your *custom furniture installation* request has been submitted!\n"
                f"Order: {inst.order_number}\n"
                f"Type: {data['furniture_type']}\n"
                f"We will contact you at {inst.contact_phone} to confirm details."
            )

            # If location pin is required but not collected in WhatsApp flow, resume conversational flow to collect it
            if not data.get('location_pin'):
                # Pseudo-function: resume the original conversational flow to collect missing info
                try:
                    from flows.services import process_message_for_flow
                    # You may want to set a context flag or message to trigger the next step for location pin
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "installation_request_id": inst.id}, None)
                    logger.info(f"[CustomFurniture] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[CustomFurniture] Failed to resume conversational flow for location pin: {resume_exc}")

            return True, feedback
        except Exception as e:
            logger.error(f"[CustomFurniture] Error: {e}", exc_info=True)
            return False, str(e)


    @staticmethod
    def _handle_solar_installation_whatsapp(flow_response, contact, response_data):
        """Process Solar Installation WhatsApp flow response and resume conversational flow for extra info (e.g., location pin)."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'installation_type', 'order_number', 'branch', 'sales_person', 'full_name', 'contact_phone', 'address'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[SolarInstallation] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            logger.info(f"[SolarInstallation] Processed for {data.get('full_name')}")

            feedback = (
                f"Your *solar installation* request has been submitted!\n"
                f"Order: {data.get('order_number')}\n"
                f"We will contact you at {data.get('contact_phone')} to confirm details."
            )
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "order_number": data.get('order_number')}, None)
                    logger.info(f"[SolarInstallation] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[SolarInstallation] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[SolarInstallation] Error: {e}", exc_info=True)
            return False, str(e)


    @staticmethod
    def _handle_solar_cleaning_whatsapp(flow_response, contact, response_data):
        """Process Solar Cleaning WhatsApp flow response and resume conversational flow for extra info (e.g., location pin)."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'full_name', 'contact_phone', 'roof_type', 'panel_type', 'panel_count', 'preferred_date', 'address'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[SolarCleaning] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            logger.info(f"[SolarCleaning] Processed for {data.get('full_name')}")

            feedback = (
                f"Your *solar cleaning* request has been submitted!\n"
                f"We will contact you at {data.get('contact_phone')} to confirm details."
            )
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "full_name": data.get('full_name')}, None)
                    logger.info(f"[SolarCleaning] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[SolarCleaning] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[SolarCleaning] Error: {e}", exc_info=True)
            return False, str(e)


    @staticmethod
    def _handle_loan_application_whatsapp(flow_response, contact, response_data):
        """Process Loan Application WhatsApp flow response and resume conversational flow for extra info (e.g., location pin)."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'loan_type', 'loan_applicant_name', 'loan_national_id', 'loan_employment_status', 'loan_monthly_income', 'loan_request_amount', 'loan_product_interest'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[LoanApplication] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            logger.info(f"[LoanApplication] Processed for {data.get('loan_applicant_name')}")

            feedback = (
                f"Your *loan application* has been submitted!\n"
                f"We will contact you to confirm details."
            )
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "loan_applicant_name": data.get('loan_applicant_name')}, None)
                    logger.info(f"[LoanApplication] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[LoanApplication] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[LoanApplication] Error: {e}", exc_info=True)
            return False, str(e)


    @staticmethod
    def _handle_hybrid_installation_whatsapp(flow_response, contact, response_data):
        """Process Hybrid Installation WhatsApp flow response and resume conversational flow for extra info (e.g., location pin)."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'order_number', 'branch', 'sales_person', 'full_name', 'contact_phone', 'address', 'starlink_kit_type', 'solar_capacity', 'mount_location'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[HybridInstallation] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            logger.info(f"[HybridInstallation] Processed for {data.get('full_name')}")

            feedback = (
                f"Your *hybrid installation* request has been submitted!\n"
                f"Order: {data.get('order_number')}\n"
                f"We will contact you at {data.get('contact_phone')} to confirm details."
            )
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "order_number": data.get('order_number')}, None)
                    logger.info(f"[HybridInstallation] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[HybridInstallation] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[HybridInstallation] Error: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def _handle_admin_add_order_whatsapp(flow_response, contact, response_data):
        try:
            data = response_data.get('data', response_data)
            feedback = "Your *admin add order* request has been submitted! We will contact you to confirm details."
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "context": "admin_add_order"}, None)
                    logger.info(f"[AdminAddOrder] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[AdminAddOrder] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[AdminAddOrder] Error: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def _handle_admin_main_menu_whatsapp(flow_response, contact, response_data):
        try:
            data = response_data.get('data', response_data)
            feedback = "Your *admin main menu* request has been submitted! We will contact you to confirm details."
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "context": "admin_main_menu"}, None)
                    logger.info(f"[AdminMainMenu] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[AdminMainMenu] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[AdminMainMenu] Error: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def _handle_admin_update_assessment_status_whatsapp(flow_response, contact, response_data):
        try:
            data = response_data.get('data', response_data)
            feedback = "Your *admin update assessment status* request has been submitted! We will contact you to confirm details."
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "context": "admin_update_assessment_status"}, None)
                    logger.info(f"[AdminUpdateAssessmentStatus] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[AdminUpdateAssessmentStatus] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[AdminUpdateAssessmentStatus] Error: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def _handle_admin_update_order_status_whatsapp(flow_response, contact, response_data):
        try:
            data = response_data.get('data', response_data)
            feedback = "Your *admin update order status* request has been submitted! We will contact you to confirm details."
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "context": "admin_update_order_status"}, None)
                    logger.info(f"[AdminUpdateOrderStatus] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[AdminUpdateOrderStatus] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[AdminUpdateOrderStatus] Error: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def _handle_admin_update_warranty_claim_whatsapp(flow_response, contact, response_data):
        try:
            data = response_data.get('data', response_data)
            feedback = "Your *admin update warranty claim* request has been submitted! We will contact you to confirm details."
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "context": "admin_update_warranty_claim"}, None)
                    logger.info(f"[AdminUpdateWarrantyClaim] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[AdminUpdateWarrantyClaim] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[AdminUpdateWarrantyClaim] Error: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def _handle_main_menu_whatsapp(flow_response, contact, response_data):
        try:
            data = response_data.get('data', response_data)
            feedback = "Your *main menu* request has been submitted! We will contact you to confirm details."
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "context": "main_menu"}, None)
                    logger.info(f"[MainMenu] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[MainMenu] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[MainMenu] Error: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def _handle_simple_add_order_whatsapp(flow_response, contact, response_data):
        try:
            data = response_data.get('data', response_data)
            feedback = "Your *simple add order* request has been submitted! We will contact you to confirm details."
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "context": "simple_add_order"}, None)
                    logger.info(f"[SimpleAddOrder] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[SimpleAddOrder] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[SimpleAddOrder] Error: {e}", exc_info=True)
            return False, str(e)


    @staticmethod
    def _handle_starlink_installation_whatsapp(flow_response, contact, response_data):
        """Process Starlink Installation WhatsApp flow response and resume conversational flow for extra info (e.g., location pin)."""
        try:
            data = response_data.get('data', response_data)
            required_fields = [
                'full_name', 'contact_phone', 'kit_type', 'mount_location', 'preferred_date', 'availability'
            ]
            for field in required_fields:
                if not data.get(field):
                    logger.warning(f"[StarlinkInstallation] Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            logger.info(f"[StarlinkInstallation] Processed for {data.get('full_name')}")

            feedback = (
                f"Your *starlink installation* request has been submitted!\n"
                f"We will contact you at {data.get('contact_phone')} to confirm details."
            )
            if not data.get('location_pin'):
                try:
                    from flows.services import process_message_for_flow
                    process_message_for_flow(contact, {"type": "internal_resume_for_location_pin", "full_name": data.get('full_name')}, None)
                    logger.info(f"[StarlinkInstallation] Resumed conversational flow for location pin for contact {contact.id}")
                except Exception as resume_exc:
                    logger.error(f"[StarlinkInstallation] Failed to resume conversational flow for location pin: {resume_exc}")
            return True, feedback
        except Exception as e:
            logger.error(f"[StarlinkInstallation] Error: {e}", exc_info=True)
            return False, str(e)
