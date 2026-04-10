# whatsappcrm_backend/flows/booking_flow_enhancements.py
"""
Enhancements for the booking flow with progress indicators.

This file contains helper text and templates for adding progress indicators
to the booking flow without completely rewriting it.

To apply these enhancements:
1. Import the functions from this module
2. Use format_booking_message() to wrap existing messages
3. Add progress headers using get_booking_step_header()
"""

from flows.progress_indicators import (
    get_step_header,
    get_multi_traveler_progress,
    get_booking_flow_progress,
    format_booking_step_message
)


# Enhanced message templates for key booking flow steps

def get_traveler_count_message(tour_name):
    """Enhanced message for asking traveler count with progress."""
    progress = get_booking_flow_progress('travelers')
    header = get_step_header(
        progress['name'],
        progress['step'],
        progress['total'],
        progress['time']
    )
    
    return f"""{header}Great choice! You're booking the *{tour_name}* tour.

👥 *Traveler Information*

How many adults (12+) will be traveling?

💡 *Tip:* Count yourself if you're traveling too!

Example: 2"""


def get_children_count_message():
    """Enhanced message for asking children count."""
    return """And how many children (under 12) will be traveling?

💡 *Tip:* Enter 0 if no children

Example: 0, 1, or 2"""


def get_date_selection_message():
    """Enhanced message for date selection."""
    progress = get_booking_flow_progress('dates')
    header = get_step_header(
        progress['name'],
        progress['step'],
        progress['total'],
        progress['time']
    )
    
    return f"""{header}📅 *Select Your Tour Dates*

When would you like to start your adventure?

Use the date picker to select your preferred start date.

💡 *Tips:*
• Choose a date at least 7 days from now
• Check weather seasons for best experience
• Popular dates book quickly!"""


def get_traveler_details_intro(current_traveler, total_travelers):
    """Enhanced intro for collecting individual traveler details."""
    progress = get_booking_flow_progress('traveler_details')
    header = get_step_header(
        progress['name'],
        progress['step'],
        progress['total'],
        progress['time']
    )
    
    traveler_progress = get_multi_traveler_progress(current_traveler, total_travelers)
    
    return f"""{header}{traveler_progress}📋 *Traveler Information*

Now let's collect details for each traveler.

*You'll provide:*
• Full name (as on ID/Passport)
• Age
• Nationality
• Medical conditions (if any)
• ID/Passport photo

⏱️ This takes about 2-3 minutes per person.

Ready? Let's start!"""


def get_payment_info_message(booking_reference, total_amount, amount_paid):
    """Enhanced message for payment information."""
    progress = get_booking_flow_progress('payment')
    header = get_step_header(
        progress['name'],
        progress['step'],
        progress['total'],
        progress['time']
    )
    
    balance = total_amount - amount_paid
    
    return f"""{header}💰 *Payment Information*

📋 Booking Reference: {booking_reference}

*Cost Breakdown:*
Total Cost: ${total_amount:,.2f}
Already Paid: ${amount_paid:,.2f}
━━━━━━━━━━━━━━━━
Balance Due: ${balance:,.2f}

*Payment Options:*
• Pay full amount now
• Pay deposit (minimum 30%)
• Pay via Omari, Bank Transfer, or Ecocash

How would you like to proceed?"""


def get_booking_confirmation_message(booking_details):
    """Enhanced confirmation message."""
    progress = get_booking_flow_progress('confirmation')
    header = get_step_header(
        progress['name'],
        progress['step'],
        progress['total'],
        progress['time']
    )
    
    return f"""{header}🎉 *Review Your Booking*

Please confirm all details are correct:

━━━━━━━━━━━━━━━━
📋 *Booking Summary*

🌍 Tour: {booking_details.get('tour_name', 'N/A')}
📅 Date: {booking_details.get('date', 'N/A')}
👥 Travelers: {booking_details.get('num_travelers', 'N/A')}
💰 Total: ${booking_details.get('total_amount', 0):,.2f}

━━━━━━━━━━━━━━━━

Everything look good?

[✅ Confirm Booking] [✏️ Edit] [❌ Cancel]"""


# Helper function to add progress to any message
def add_progress_to_message(message, stage):
    """
    Add progress indicator to any existing message.
    
    Args:
        message: Original message text
        stage: Current stage in booking flow
    
    Returns:
        Message with progress header prepended
    """
    return format_booking_step_message(stage, message)


# Dictionary of enhanced messages for easy reference
ENHANCED_MESSAGES = {
    'traveler_count': get_traveler_count_message,
    'children_count': get_children_count_message,
    'date_selection': get_date_selection_message,
    'traveler_details_intro': get_traveler_details_intro,
    'payment_info': get_payment_info_message,
    'confirmation': get_booking_confirmation_message,
}


def get_enhanced_message(message_type, **kwargs):
    """
    Get an enhanced message by type.
    
    Args:
        message_type: Type of message to get
        **kwargs: Arguments for the message function
    
    Returns:
        Enhanced message string
    """
    if message_type in ENHANCED_MESSAGES:
        return ENHANCED_MESSAGES[message_type](**kwargs)
    return None
