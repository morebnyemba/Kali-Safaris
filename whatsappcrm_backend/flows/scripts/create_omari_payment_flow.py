"""
Example flow script to create a payment flow using Omari integration.

This demonstrates how to create a flow that:
1. Asks for booking reference
2. Asks for amount to pay
3. Initiates Omari payment
4. Collects OTP (handled automatically by message processor)
5. Confirms payment success

Usage:
    python manage.py shell < flows/scripts/create_omari_payment_flow.py
"""

from flows.models import Flow, FlowStep, FlowTransition

# Create the flow
flow, created = Flow.objects.get_or_create(
    name='omari_payment_flow',
    defaults={
        'friendly_name': 'Omari Payment Flow',
        'description': 'Process payments through Omari with OTP verification',
        'is_active': True,
        'trigger_keywords': ['pay', 'payment', 'make payment']
    }
)

if created:
    print(f"✓ Created flow: {flow.friendly_name}")
else:
    print(f"✓ Flow already exists: {flow.friendly_name}")
    # Clear existing steps for fresh setup
    flow.steps.all().delete()

# Step 1: Welcome and ask for booking reference
step_welcome = FlowStep.objects.create(
    flow=flow,
    name='welcome_payment',
    step_type='send_message',
    is_entry_point=True,
    config={
        'message_type': 'text',
        'text': {
            'body': '💳 *Payment Gateway*\\n\\nWelcome! I can help you make a payment for your booking.\\n\\nPlease provide your booking reference number:',
            'preview_url': False
        }
    }
)

# Step 2: Ask for booking reference
step_ask_booking = FlowStep.objects.create(
    flow=flow,
    name='ask_booking_reference',
    step_type='question',
    config={
        'message_config': {
            'message_type': 'text',
            'text': {
                'body': 'Please enter your booking reference (e.g., KS-2024-001):',
                'preview_url': False
            }
        },
        'reply_config': {
            'save_to_variable': 'booking_reference',
            'expected_type': 'text'
        }
    }
)

# Step 3: Ask for amount
step_ask_amount = FlowStep.objects.create(
    flow=flow,
    name='ask_amount',
    step_type='question',
    config={
        'message_config': {
            'message_type': 'text',
            'text': {
                'body': 'How much would you like to pay (in USD)?\\n\\nExamples:\\n- 100\\n- 50.50',
                'preview_url': False
            }
        },
        'reply_config': {
            'save_to_variable': 'amount_to_pay',
            'expected_type': 'text',
            'validation_regex': r'^\\d+(\\.\\d{1,2})?$'
        },
        'fallback_config': {
            'action': 're_prompt',
            'max_retries': 3,
            're_prompt_message_text': '❌ Please enter a valid amount (e.g., 100 or 50.50)'
        }
    }
)

# Step 4: Initiate payment
step_initiate = FlowStep.objects.create(
    flow=flow,
    name='initiate_payment',
    step_type='action',
    config={
        'actions_to_run': [
            {
                'action_type': 'initiate_omari_payment',
                'params_template': {
                    'booking_reference': '{{ booking_reference }}',
                    'amount': '{{ amount_to_pay }}',
                    'currency': 'USD',
                    'channel': 'WEB'
                }
            }
        ]
    }
)

# Step 5: Payment completed successfully
step_success = FlowStep.objects.create(
    flow=flow,
    name='payment_success',
    step_type='end_flow',
    config={
        'message_config': {
            'message_type': 'text',
            'text': {
                'body': '🎉 *Thank You!*\\n\\nYour payment has been processed successfully. You will receive a confirmation shortly.\\n\\nType *menu* to return to the main menu.',
                'preview_url': False
            }
        }
    }
)

# Create transitions
FlowTransition.objects.create(
    current_step=step_welcome,
    next_step=step_ask_booking,
    priority=1,
    condition_config={'type': 'always_true'}
)

FlowTransition.objects.create(
    current_step=step_ask_booking,
    next_step=step_ask_amount,
    priority=1,
    condition_config={
        'type': 'variable_exists',
        'variable_name': 'booking_reference'
    }
)

FlowTransition.objects.create(
    current_step=step_ask_amount,
    next_step=step_initiate,
    priority=1,
    condition_config={
        'type': 'variable_exists',
        'variable_name': 'amount_to_pay'
    }
)

FlowTransition.objects.create(
    current_step=step_initiate,
    next_step=step_success,
    priority=1,
    condition_config={'type': 'always_true'}
)

print(f"\\n✓ Created {flow.steps.count()} steps")
print(f"✓ Created {FlowTransition.objects.filter(current_step__flow=flow).count()} transitions")
print(f"\\n🎉 Payment flow setup complete!")
print(f"\\nTrigger keywords: {', '.join(flow.trigger_keywords)}")
print(f"Status: {'Active' if flow.is_active else 'Inactive'}")
