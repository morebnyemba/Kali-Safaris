# whatsappcrm_backend/flows/progress_indicators.py
"""
Progress indicator utilities for multi-step conversational flows.
Helps users understand where they are in the process.
"""

def get_progress_bar(current_step, total_steps, style='dots'):
    """
    Generate a visual progress bar.
    
    Args:
        current_step: Current step number (1-indexed)
        total_steps: Total number of steps
        style: Style of progress bar ('dots', 'bars', 'emojis')
    
    Returns:
        Formatted progress bar string
    """
    
    if style == 'dots':
        completed = '●' * (current_step - 1)
        current = '◉'
        pending = '○' * (total_steps - current_step)
        return f"{completed}{current}{pending}"
    
    elif style == 'bars':
        completed = '█' * (current_step - 1)
        current = '▓'
        pending = '░' * (total_steps - current_step)
        return f"{completed}{current}{pending}"
    
    elif style == 'emojis':
        completed = '✅' * (current_step - 1)
        current = '🔹'
        pending = '⚪' * (total_steps - current_step)
        return f"{completed}{current}{pending}"
    
    else:
        # Default to simple text
        return f"[{current_step}/{total_steps}]"


def get_step_header(step_name, current_step, total_steps, estimated_time=None):
    """
    Generate a formatted step header with progress.
    
    Args:
        step_name: Name/description of the current step
        current_step: Current step number
        total_steps: Total number of steps
        estimated_time: Optional estimated time remaining (in minutes)
    
    Returns:
        Formatted header string
    """
    
    progress_bar = get_progress_bar(current_step, total_steps, style='emojis')
    
    header = f"""📋 *{step_name}*

{progress_bar} Step {current_step} of {total_steps}"""
    
    if estimated_time:
        header += f"\n⏱️ ~{estimated_time} min remaining"
    
    return header + "\n\n"


def get_section_header(section_name, icon='📌'):
    """
    Generate a section header for grouping related questions.
    
    Args:
        section_name: Name of the section
        icon: Emoji icon for the section
    
    Returns:
        Formatted section header
    """
    
    return f"""{icon} *{section_name}*
━━━━━━━━━━━━━━━━

"""


def get_booking_flow_progress(stage):
    """
    Get progress information specific to the booking flow.
    
    Args:
        stage: Current stage in booking flow
               ('travelers', 'dates', 'payment', 'details', 'confirmation')
    
    Returns:
        Dictionary with step number, total steps, and estimated time
    """
    
    stages = {
        'travelers': {'step': 1, 'total': 5, 'time': 4, 'name': 'Traveler Count'},
        'dates': {'step': 2, 'total': 5, 'time': 3, 'name': 'Select Dates'},
        'traveler_details': {'step': 3, 'total': 5, 'time': 3, 'name': 'Traveler Details'},
        'payment': {'step': 4, 'total': 5, 'time': 2, 'name': 'Payment Information'},
        'confirmation': {'step': 5, 'total': 5, 'time': 1, 'name': 'Confirmation'}
    }
    
    return stages.get(stage, {'step': 1, 'total': 5, 'time': 5, 'name': 'Booking'})


def format_booking_step_message(stage, base_message):
    """
    Format a booking flow message with progress indicator.
    
    Args:
        stage: Current stage in booking flow
        base_message: The original message text
    
    Returns:
        Formatted message with progress header
    """
    
    progress = get_booking_flow_progress(stage)
    header = get_step_header(
        progress['name'],
        progress['step'],
        progress['total'],
        progress['time']
    )
    
    return header + base_message


def get_multi_traveler_progress(current_traveler, total_travelers):
    """
    Get progress for entering multiple travelers' details.
    
    Args:
        current_traveler: Current traveler number (1-indexed)
        total_travelers: Total number of travelers
    
    Returns:
        Formatted progress string
    """
    
    if total_travelers == 1:
        return "👤 *Traveler Details*\n\n"
    
    progress_bar = get_progress_bar(current_traveler, total_travelers, style='emojis')
    
    return f"""👥 *Traveler {current_traveler} of {total_travelers}*

{progress_bar}

"""


def get_completion_summary(flow_name, key_details):
    """
    Generate a completion summary at the end of a flow.
    
    Args:
        flow_name: Name of the completed flow
        key_details: Dictionary of key information to display
    
    Returns:
        Formatted completion summary
    """
    
    details_text = '\n'.join([f"• {key}: {value}" for key, value in key_details.items()])
    
    return f"""✅ *{flow_name} Complete!*

*Summary:*
{details_text}

━━━━━━━━━━━━━━━━

Type *menu* to explore more options."""


# Estimated time calculations
def estimate_remaining_time(current_step, total_steps, time_per_step=1):
    """
    Estimate remaining time in minutes.
    
    Args:
        current_step: Current step number
        total_steps: Total number of steps
        time_per_step: Average time per step in minutes
    
    Returns:
        Estimated minutes remaining (rounded)
    """
    
    remaining_steps = total_steps - current_step
    return max(1, round(remaining_steps * time_per_step))


# Tips and helper text
def get_progress_tips():
    """Get helpful tips about navigating multi-step flows."""
    
    return """💡 *Navigation Tips:*

• Type *menu* anytime to cancel
• Your progress is saved automatically
• You can come back later to continue

Type *help* for more assistance."""
