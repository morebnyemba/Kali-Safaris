# Phase 3A Implementation Guide

## Overview

Phase 3A delivers three major advanced features:
1. **Flow Analytics & Metrics** - Track user behavior for optimization
2. **Automated Receipt Generation** - Professional payment documentation
3. **Enhanced Pre-Tour Summaries** - Better customer preparation

## Feature 1: Flow Analytics & Metrics

### Purpose
Track conversational flow performance to enable data-driven optimization.

### Models

#### FlowSession
Tracks complete user journeys through flows.

**Fields:**
- `contact` - User
- `flow_name` - Flow identifier
- `started_at` - Start time
- `completed_at` - End time
- `status` - active/completed/abandoned/error
- `context_data` - Flow context (JSON)
- `error_message` - Error details if failed

#### FlowStepEvent
Tracks individual step interactions.

**Fields:**
- `session` - Parent FlowSession
- `step_name` - Step identifier
- `action` - entered/completed/skipped/error/retry
- `timestamp` - Event time
- `time_spent` - Duration (seconds)
- `input_value` - User input
- `output_value` - System output
- `error_message` - Error details
- `retry_count` - Retry attempts

#### FlowMetricSnapshot
Pre-calculated periodic metrics.

**Fields:**
- `flow_name` - Flow identifier
- `period` - daily/weekly/monthly
- `period_start/end` - Time period
- `total_sessions` - Count
- `completed_sessions` - Completions
- `abandoned_sessions` - Abandonments
- `error_sessions` - Errors
- `avg_duration_seconds` - Average time
- `total_errors` - Error count
- `error_rate` - Percentage

### Usage

```python
from analytics.models import FlowSession, FlowStepEvent

# Track flow start
session = FlowSession.objects.create(
    contact=contact,
    flow_name='booking_flow'
)

# Track step
FlowStepEvent.objects.create(
    session=session,
    step_name='traveler_count',
    action='entered'
)

# Track completion
FlowStepEvent.objects.create(
    session=session,
    step_name='traveler_count',
    action='completed',
    time_spent=15.5,
    input_value='4'
)

# Mark session complete
session.mark_completed()
```

### Reports

```python
from analytics.reports import (
    get_flow_completion_rate,
    get_step_funnel,
    get_error_analysis,
    generate_daily_snapshot
)

# Get completion rate
metrics = get_flow_completion_rate('booking_flow', days=7)
print(f"Completion rate: {metrics['completion_rate']}%")

# Get funnel analysis
funnel = get_step_funnel('booking_flow', days=7)
for step in funnel:
    print(f"{step['step_name']}: {step['percentage']}%")

# Get error analysis
errors = get_error_analysis('booking_flow', days=7)
for error in errors:
    print(f"{error['step_name']}: {error['count']} errors")

# Generate daily snapshot
snapshot = generate_daily_snapshot('booking_flow', date.today())
```

### Admin Interface

Access via Django Admin → Analytics:
- Flow Sessions - View all sessions
- Flow Step Events - Detailed step tracking
- Flow Metric Snapshots - Pre-calculated metrics

**Filters available:**
- Status
- Flow name
- Date range
- Step name
- Action type

## Feature 2: Automated Receipt Generation

### Purpose
Generate professional PDF receipts automatically when payments are approved.

### Integration Points

Receipts are automatically generated when:
1. Manual payments are approved by admin
2. Omari payments are confirmed
3. Admin clicks "Generate Receipt" action
4. Customer requests via WhatsApp: "send receipt"

### Receipt Contents

1. **Header**
   - Company branding
   - Receipt number (unique)
   - Date and time

2. **Customer Info**
   - Name
   - Contact details
   - Booking reference

3. **Payment Details**
   - Amount paid
   - Payment method
   - Transaction reference
   - Payment date

4. **Booking Summary**
   - Tour name
   - Tour date
   - Number of travelers
   - Total cost
   - Amount paid
   - Balance due

5. **Footer**
   - Terms and conditions
   - Contact information
   - Thank you message

### Usage (Future Implementation)

```python
from customer_data.receipts import generate_receipt

# Generate receipt for payment
pdf_bytes = generate_receipt(payment.id)

# Send via WhatsApp
send_whatsapp_document(
    contact=booking.customer.primary_contact,
    document_bytes=pdf_bytes,
    filename=f'Receipt_{payment.id}.pdf',
    caption='Your payment receipt'
)
```

## Feature 3: Enhanced Pre-Tour Summaries

### Purpose
Send comprehensive tour information 7 days before the tour to help customers prepare.

### Command

```bash
# Send 7-day summaries
python manage.py send_tour_summaries --days-before 7

# Dry run (test without sending)
python manage.py send_tour_summaries --days-before 7 --dry-run

# Custom timing
python manage.py send_tour_summaries --days-before 3
```

### Summary Contents

1. **Tour Details**
   - Name, description
   - Date, time, duration
   - Meeting point with map
   - Guide information

2. **Booking Info**
   - Reference number
   - Traveler names
   - Payment status
   - Balance due

3. **Preparation**
   - Packing list
   - Weather forecast
   - Clothing recommendations

4. **Important Info**
   - Park rules
   - Safety guidelines
   - Emergency contacts
   - Cancellation policy

5. **Quick Actions**
   - Pay balance
   - Update details
   - Upload IDs
   - Contact support

### Automation

Set up cron job:

```bash
# Daily at 8 AM
0 8 * * * cd /path/to/project && python manage.py send_tour_summaries --days-before 7
```

## Installation

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'analytics',
]
```

### 2. Run Migrations

```bash
python manage.py makemigrations analytics
python manage.py migrate analytics
```

### 3. Set Up Cron Jobs

```bash
# ID reminders (48 hours before)
0 9 * * * cd /path && python manage.py send_id_reminders --hours-before 48

# Tour summaries (7 days before)
0 8 * * * cd /path && python manage.py send_tour_summaries --days-before 7
```

## Testing

### Test Analytics

```python
from analytics.models import FlowSession
from meta_integration.models import Contact

contact = Contact.objects.first()
session = FlowSession.objects.create(
    contact=contact,
    flow_name='test_flow'
)
session.mark_completed()

print(f"Duration: {session.duration_seconds}s")
```

### Test Reports

```python
from analytics.reports import get_flow_completion_rate

metrics = get_flow_completion_rate('booking_flow', days=7)
print(metrics)
```

## Metrics to Track

### Key Performance Indicators (KPIs)

1. **Completion Rates**
   - Overall flow completion
   - Step-by-step completion
   - Target: >80%

2. **Abandonment Points**
   - Where users drop off
   - Step-specific rates
   - Target: Identify top 3

3. **Time Metrics**
   - Average flow duration
   - Time per step
   - Target: <5 minutes

4. **Error Rates**
   - Error frequency by type
   - Recovery success rate
   - Target: <10%

5. **User Satisfaction**
   - Completion to booking ratio
   - Repeat user rate
   - Support ticket correlation

## Best Practices

### Analytics

1. **Track Consistently**
   - Use middleware for automation
   - Manual tracking for custom flows
   - Don't skip steps

2. **Clean Data**
   - Set session timeouts
   - Handle duplicates
   - Validate inputs

3. **Act on Insights**
   - Review metrics weekly
   - A/B test improvements
   - Iterate based on data

### Receipts

1. **Always Generate**
   - On payment approval
   - Store for re-download
   - Send immediately

2. **Professional Format**
   - Use company branding
   - Include all required info
   - Clear, readable layout

### Tour Summaries

1. **Timing Matters**
   - 7 days: Initial reminder
   - 3 days: Final check
   - 1 day: Last-minute details

2. **Complete Information**
   - Answer common questions
   - Provide contact info
   - Enable quick actions

3. **Personalization**
   - Use customer name
   - Reference specific booking
   - Context-aware messages

## Troubleshooting

### Analytics Not Tracking

**Problem:** Sessions not being created

**Solutions:**
1. Check middleware is installed
2. Verify INSTALLED_APPS includes 'analytics'
3. Confirm migrations are run
4. Check for transaction issues

### Receipts Not Generating

**Problem:** PDF generation fails

**Solutions:**
1. Check payment object exists
2. Verify booking has all required fields
3. Check file permissions
4. Review error logs

### Summaries Not Sending

**Problem:** Command runs but messages don't send

**Solutions:**
1. Check WhatsApp API credentials
2. Verify contact phone numbers
3. Run with --dry-run to test logic
4. Check cron job logs

## Future Enhancements (Phase 3B)

1. **Multi-language Support**
   - Translate all messages
   - Detect user language
   - Persist preference

2. **Smart Context Awareness**
   - Returning vs new users
   - Recent activity
   - Personalized quick actions

3. **Advanced Analytics**
   - Machine learning predictions
   - Conversion optimization
   - Cohort analysis

4. **ID Validation**
   - OCR for automatic extraction
   - Document verification
   - Quality checking

## Support

For questions or issues:
- Check documentation
- Review error logs
- Contact development team

---

**Phase 3A Complete!** 🎉

Three powerful features delivered for better analytics, professionalism, and customer preparation.
