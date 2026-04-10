# Phase 2 Enhancements - Implementation Guide

This document describes the Phase 2 future enhancements implemented for the Kali Safaris WhatsApp CRM system.

## Overview

Phase 2 delivers three major enhancements:
1. **Standardized Error Message Templates**
2. **Booking Flow Progress Indicators**
3. **ID Document Reminder System**

---

## 1. Standardized Error Message Templates

### File: `flows/error_templates.py`

### Purpose
Provides consistent, user-friendly error handling across all conversational flows.

### Features

#### Available Error Types
- `invalid_input` - Generic invalid input
- `invalid_number` - Number format errors
- `invalid_date` - Date format errors
- `not_found` - Item not found
- `booking_not_found` - Specific to bookings
- `system_error` - Backend errors
- `payment_failed` - Payment processing errors
- `unauthorized` - Permission errors
- `validation_failed` - Field validation errors
- `timeout` - Session timeout
- `cancelled` - User cancellation

#### Usage Example

```python
from flows.error_templates import get_error_message, get_retry_prompt, get_success_message

# Get an error message
error_msg = get_error_message(
    'booking_not_found',
    booking_reference='BK-123',
    retry_command='manual payment'
)

# Get a retry prompt with encouragement
retry_msg = get_retry_prompt(
    'enter the amount',
    max_retries=3,
    current_retry=2
)

# Get a success message
success_msg = get_success_message(
    'payment_recorded',
    amount=500.00,
    booking_reference='BK-123',
    payment_method='Bank Transfer'
)
```

### Benefits
- ✅ Consistent error formatting across all flows
- ✅ Helpful recovery options
- ✅ Encouraging retry messages
- ✅ Clear examples and tips
- ✅ Professional tone

### Integration
To apply to existing flows:
1. Import the error template functions
2. Replace hardcoded error messages with template calls
3. Use retry prompts for validation errors
4. Add contextual information to parameters

---

## 2. Booking Flow Progress Indicators

### Files
- `flows/progress_indicators.py` - Core utilities
- `flows/booking_flow_enhancements.py` - Booking-specific templates

### Purpose
Show users where they are in multi-step flows with visual progress indicators.

### Features

#### Progress Bar Styles
```
Dots:    ●●◉○○
Bars:    ██▓░░
Emojis:  ✅✅🔹⚪⚪
```

#### Step Headers
```
📋 *Traveler Details*

✅✅🔹⚪⚪ Step 3 of 5
⏱️ ~3 min remaining
```

#### Multi-Traveler Progress
```
👥 *Traveler 2 of 4*

✅🔹⚪⚪
```

### Usage Example

```python
from flows.progress_indicators import (
    get_step_header,
    get_multi_traveler_progress,
    format_booking_step_message
)

# Add header to any message
header = get_step_header(
    'Select Dates',
    current_step=2,
    total_steps=5,
    estimated_time=3
)

# Format entire booking message
message = format_booking_step_message(
    'dates',
    'When would you like to start your tour?'
)

# Show traveler progress
traveler_header = get_multi_traveler_progress(
    current_traveler=2,
    total_travelers=4
)
```

### Enhanced Booking Flow Messages

The `booking_flow_enhancements.py` file provides enhanced message templates:

```python
from flows.booking_flow_enhancements import get_enhanced_message

# Get enhanced traveler count message
message = get_enhanced_message(
    'traveler_count',
    tour_name='Victoria Falls Safari'
)

# Get enhanced confirmation message
message = get_enhanced_message(
    'confirmation',
    booking_details={
        'tour_name': 'Victoria Falls Safari',
        'date': 'February 10, 2026',
        'num_travelers': 4,
        'total_amount': 2000.00
    }
)
```

### Benefits
- ✅ Users always know where they are
- ✅ Sets time expectations
- ✅ Reduces abandonment
- ✅ Professional appearance
- ✅ Motivates completion

### Integration Steps

To add progress indicators to the booking flow:

1. **Import the utilities** in `booking_flow.py`:
```python
from flows.booking_flow_enhancements import get_enhanced_message, add_progress_to_message
```

2. **Update message templates** in flow steps:
```python
# Original
"text": {"body": "How many adults will be traveling?"}

# Enhanced
"text": {"body": "{{ get_enhanced_message('traveler_count', tour_name=tour_name) }}"}
```

3. **Add progress to existing messages**:
```python
"text": {"body": "{{ add_progress_to_message(original_message, 'travelers') }}"}
```

---

## 3. ID Document Reminder System

### File: `customer_data/management/commands/send_id_reminders.py`

### Purpose
Automatically reminds travelers to upload ID documents before their tour date.

### Features

- ✅ Checks upcoming tours (default: 48 hours before)
- ✅ Identifies travelers without ID documents
- ✅ Sends personalized WhatsApp reminders
- ✅ Handles multiple travelers per booking
- ✅ Includes clear instructions and deadlines
- ✅ Dry-run mode for testing
- ✅ Force mode to resend reminders

### Command Usage

```bash
# Send reminders for tours starting in 48 hours (default)
python manage.py send_id_reminders

# Send reminders for tours starting in 24 hours
python manage.py send_id_reminders --hours-before 24

# Dry run - see what would be sent without sending
python manage.py send_id_reminders --dry-run

# Force send even if already sent today
python manage.py send_id_reminders --force

# Custom timing with dry run
python manage.py send_id_reminders --hours-before 72 --dry-run
```

### Reminder Message Format

```
⚠️ *ID Document Reminder*

Hi! Your tour is coming up soon:

🌍 *Tour:* Victoria Falls Safari
📅 *Date:* February 10, 2026
📋 *Booking:* BK-T005-20260210

📸 *Action Needed:*
We still need ID/Passport photos for:
John Doe, Jane Doe

🚨 *Deadline:* February 9 at 11:00 AM

━━━━━━━━━━━━━━━━

*To upload now:*
Reply with *traveler details* to start the process.

💡 *Why we need this:*
ID documents are required by park authorities for entry.

Questions? Just reply to this message!

Kalai Safaris Team 🦁
```

### Scheduling

Set up automated reminders using cron:

```bash
# Edit crontab
crontab -e

# Add entries for 48-hour and 24-hour reminders
# Run at 9 AM every day - 48 hour reminder
0 9 * * * cd /path/to/project && python manage.py send_id_reminders --hours-before 48

# Run at 9 AM every day - 24 hour reminder  
0 9 * * * cd /path/to/project && python manage.py send_id_reminders --hours-before 24
```

Or use Django-cron, Celery Beat, or your preferred task scheduler.

### Logic Flow

```
1. Calculate target date range (hours_before ± 1 hour window)
2. Find confirmed bookings (PAID/DEPOSIT_PAID) in that range
3. For each booking:
   a. Get travelers without ID documents
   b. If any missing, get customer contact
   c. Format personalized reminder message
   d. Send via WhatsApp
4. Log results and summary
```

### Benefits
- ✅ Proactive customer service
- ✅ Ensures compliance with park requirements
- ✅ Reduces day-of-tour delays
- ✅ Automated - no manual intervention needed
- ✅ Personalized messages per booking
- ✅ Clear deadlines and instructions

---

## Testing Phase 2 Features

### Test Error Templates

```python
# In Django shell or view
from flows.error_templates import get_error_message

# Test different error types
print(get_error_message('booking_not_found', booking_reference='BK-123'))
print(get_error_message('invalid_number', example='123.45'))
print(get_error_message('system_error'))
```

### Test Progress Indicators

```python
from flows.progress_indicators import get_step_header, get_progress_bar

# Test progress bars
print(get_progress_bar(3, 5, 'emojis'))  # ✅✅🔹⚪⚪

# Test step header
print(get_step_header('Traveler Details', 3, 5, 3))
```

### Test Booking Enhancements

```python
from flows.booking_flow_enhancements import get_enhanced_message

# Test enhanced messages
print(get_enhanced_message('traveler_count', tour_name='Safari Adventure'))
print(get_enhanced_message('confirmation', booking_details={
    'tour_name': 'Safari',
    'date': 'Feb 10',
    'num_travelers': 4,
    'total_amount': 2000
}))
```

### Test ID Reminders

```bash
# Dry run to see what would be sent
python manage.py send_id_reminders --dry-run

# Test with different timing
python manage.py send_id_reminders --hours-before 24 --dry-run

# Actually send (on test/staging first!)
python manage.py send_id_reminders
```

---

## Migration Path

### For Existing Flows

1. **Adopt Error Templates Gradually**
   - Start with one flow (e.g., manual_payment_flow)
   - Replace error messages with template calls
   - Test thoroughly
   - Roll out to other flows

2. **Add Progress Indicators**
   - Begin with booking flow (highest impact)
   - Use `add_progress_to_message()` wrapper initially
   - Gradually replace with enhanced message templates
   - Test user feedback

3. **Enable ID Reminders**
   - Test in dry-run mode first
   - Set up for 48-hour reminders initially
   - Monitor delivery rates and user responses
   - Add 24-hour reminders after validation
   - Expand to other reminder types (payment, review, etc.)

### Backward Compatibility

All Phase 2 enhancements are:
- ✅ **Non-breaking** - Existing flows work unchanged
- ✅ **Opt-in** - Use new features as needed
- ✅ **Incremental** - Apply gradually
- ✅ **Testable** - Dry-run and test modes available

---

## Monitoring & Metrics

### Error Templates
- Track error frequency by type
- Monitor recovery rates (users who retry successfully)
- Measure support ticket reduction

### Progress Indicators
- Track flow completion rates (before/after)
- Measure time spent per step
- Monitor abandonment points

### ID Reminders
- Track reminder delivery rates
- Measure ID upload completion after reminder
- Monitor day-of-tour compliance rates
- Track customer satisfaction

---

## Future Enhancements (Phase 3)

Based on Phase 2 learnings:
1. **Multi-language support** for messages
2. **Voice-friendly** message formats
3. **A/B testing** framework for message effectiveness
4. **Smart timing** - learn optimal reminder times per user
5. **Progress persistence** - save and resume flows
6. **Advanced validation** - OCR for ID documents

---

## Support

For questions or issues:
- 📧 Email: dev@kalaisafaris.com
- 📖 Docs: See individual file docstrings
- 🐛 Issues: Create GitHub issue with [Phase 2] tag

---

**Phase 2 Complete!** 🎉

These enhancements provide a robust foundation for excellent user experience and operational efficiency.
