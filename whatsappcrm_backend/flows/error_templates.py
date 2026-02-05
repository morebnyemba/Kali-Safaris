# whatsappcrm_backend/flows/error_templates.py
"""
Standardized error message templates for conversational flows.
Provides consistent, user-friendly error handling across all flows.
"""

def get_error_message(error_type, **context):
    """
    Get a standardized error message based on error type.
    
    Args:
        error_type: Type of error (e.g., 'invalid_input', 'not_found', 'system_error')
        **context: Additional context for the error message (e.g., field_name, example)
    
    Returns:
        Formatted error message string
    """
    
    templates = {
        'invalid_input': {
            'message': """❌ *Invalid Input*

{explanation}

💡 *Example:* {example}

🔄 Please try again
📱 Type *menu* to return to main menu""",
            'defaults': {
                'explanation': "The value you entered doesn't match the expected format.",
                'example': "Please provide a valid input"
            }
        },
        
        'invalid_number': {
            'message': """❌ *Invalid Number*

Please enter a valid number.

💡 *Example:* {example}

🔄 Try again
📱 Type *menu* to cancel""",
            'defaults': {
                'example': "123 or 1.50"
            }
        },
        
        'invalid_date': {
            'message': """❌ *Invalid Date*

The date you entered is not valid.

💡 *Tips:*
• Use the date picker if available
• Format: YYYY-MM-DD (e.g., 2026-02-10)
• Make sure the date is in the future

🔄 Try again
📱 Type *menu* to cancel""",
            'defaults': {}
        },
        
        'not_found': {
            'message': """❌ *{item_type} Not Found*

I couldn't find {item_description}.

💡 *Tips:*
• Check for typos
• Make sure you have the complete {field_name}
• {format_hint}

🔄 Type *{retry_command}* to try again
📱 Type *menu* to return to main menu""",
            'defaults': {
                'item_type': 'Item',
                'item_description': 'the item you're looking for',
                'field_name': 'reference',
                'format_hint': 'Double-check the format',
                'retry_command': 'retry'
            }
        },
        
        'booking_not_found': {
            'message': """❌ *Booking Not Found*

I couldn't find a booking with reference: *{booking_reference}*

💡 *Tips:*
• Check the reference number for typos
• Make sure you have the complete reference
• Reference format: BK-XXX-XXX-XXXXXXXX

🔄 Type *{retry_command}* to try again
📧 Contact support: bookings@kalaisafaris.com
📱 Type *menu* to return to main menu""",
            'defaults': {
                'booking_reference': '[not provided]',
                'retry_command': 'manual payment'
            }
        },
        
        'system_error': {
            'message': """⚠️ *System Error*

Sorry, something went wrong on our end.

We've been notified and will fix this shortly.

🔄 *What you can do:*
• Try again in a few moments
• Type *menu* to explore other options
• Contact support if issue persists

📧 Email: bookings@kalaisafaris.com
📱 WhatsApp: We're here to help!""",
            'defaults': {}
        },
        
        'payment_failed': {
            'message': """❌ *Payment Failed*

{reason}

💡 *What to do:*
• Check your payment details
• Ensure sufficient funds
• Try a different payment method

🔄 Type *{retry_command}* to try again
📧 Contact support: bookings@kalaisafaris.com
📱 Type *menu* for other options""",
            'defaults': {
                'reason': 'Your payment could not be processed.',
                'retry_command': 'payment'
            }
        },
        
        'unauthorized': {
            'message': """🔒 *Access Denied*

You don't have permission to perform this action.

💡 *Possible reasons:*
• You're not logged in
• This is not your booking
• Action not available for this booking status

📧 Contact support: bookings@kalaisafaris.com
📱 Type *menu* to return to main menu""",
            'defaults': {}
        },
        
        'validation_failed': {
            'message': """❌ *Validation Error*

{field_name}: {error_message}

💡 *Requirements:*
{requirements}

🔄 Please try again
📱 Type *menu* to cancel""",
            'defaults': {
                'field_name': 'Field',
                'error_message': 'is invalid',
                'requirements': '• Please check the format and try again'
            }
        },
        
        'timeout': {
            'message': """⏱️ *Session Timeout*

Your session has expired for security reasons.

💡 *To continue:*
Type *menu* to start over and try again.

We keep you safe by limiting session time! 🔒""",
            'defaults': {}
        },
        
        'cancelled': {
            'message': """❌ *{action} Cancelled*

No worries! Your {item} has been cancelled.

🔄 *Want to try again?*
Type *{retry_command}* to start over

📱 Type *menu* to explore other options

We're here whenever you're ready! 🌍✨""",
            'defaults': {
                'action': 'Action',
                'item': 'request',
                'retry_command': 'menu'
            }
        }
    }
    
    if error_type not in templates:
        # Fallback to generic error
        return """⚠️ *Something went wrong*

Please try again or contact support.

📱 Type *menu* to return to main menu
📧 Email: bookings@kalaisafaris.com"""
    
    template = templates[error_type]
    message_template = template['message']
    defaults = template['defaults']
    
    # Merge defaults with provided context
    params = {**defaults, **context}
    
    try:
        return message_template.format(**params)
    except KeyError as e:
        # If a required parameter is missing, return basic version
        return message_template.format(**defaults)


def get_retry_prompt(action_name, max_retries=3, current_retry=1):
    """
    Get an encouraging retry prompt with attempt counter.
    
    Args:
        action_name: Name of the action being retried (e.g., 'enter amount', 'select date')
        max_retries: Maximum number of retries allowed
        current_retry: Current retry attempt number
    
    Returns:
        Formatted retry prompt string
    """
    
    encouragements = [
        "Let's try that again! 💪",
        "No problem, give it another shot! 🎯",
        "Almost there, try once more! ⭐"
    ]
    
    if current_retry >= max_retries:
        return f"""⚠️ *Maximum Attempts Reached*

You've tried {max_retries} times.

💡 *What to do:*
• Type *menu* to start over
• Contact support for help

📧 Email: bookings@kalaisafaris.com"""
    
    encouragement = encouragements[min(current_retry - 1, len(encouragements) - 1)]
    attempts_left = max_retries - current_retry
    
    return f"""{encouragement}

Please {action_name}.

📊 *Attempts remaining:* {attempts_left}

Type *menu* to cancel"""


def get_success_message(action_type, **context):
    """
    Get a standardized success message.
    
    Args:
        action_type: Type of successful action
        **context: Additional context for the message
    
    Returns:
        Formatted success message string
    """
    
    templates = {
        'payment_recorded': """✅ *Payment Recorded Successfully!*

We've received your payment submission:

💰 Amount: ${amount}
📋 Booking: #{booking_reference}
💳 Method: {payment_method}

🔍 *What happens next?*
1. Our finance team will verify your payment
2. You'll receive a confirmation once approved
3. A receipt will be sent to you

⏱️ *Processing Time:* Usually within 24 hours

Thank you! Type *menu* to return to main menu.""",
        
        'booking_created': """✅ *Booking Created Successfully!*

Your booking has been confirmed:

📋 Reference: #{booking_reference}
🌍 Tour: {tour_name}
📅 Date: {tour_date}
👥 Travelers: {num_travelers}

🎯 *What happens next?*
{next_steps}

Thank you for choosing us! Type *menu* to explore more.""",
        
        'travelers_added': """✅ *Traveler Details Saved!*

You've successfully added {num_travelers} traveler(s).

📋 *Next Steps:*
{next_steps}

Type *menu* to return to main menu.""",
        
        'generic_success': """✅ *Success!*

{message}

Type *menu* to continue."""
    }
    
    template = templates.get(action_type, templates['generic_success'])
    
    try:
        return template.format(**context)
    except KeyError:
        return f"✅ Success! Type *menu* to continue."


# Helper function to format field requirements
def format_requirements(requirements_list):
    """
    Format a list of requirements into bullet points.
    
    Args:
        requirements_list: List of requirement strings
    
    Returns:
        Formatted string with bullet points
    """
    return '\n'.join([f"• {req}" for req in requirements_list])
