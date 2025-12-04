# Verification Guide: WhatsApp Flow Automatic Transitions

This guide helps you verify that the automatic transition improvements are working correctly.

## Prerequisites

Before testing, ensure:
- [ ] Django server is running
- [ ] Celery worker is running
- [ ] Celery beat is running (if using scheduled tasks)
- [ ] Redis is running
- [ ] Meta WhatsApp webhook is configured and verified

## Step-by-Step Verification

### 1. Check Configuration

```bash
# Verify Meta app config is active
python manage.py shell
>>> from meta_integration.models import MetaAppConfig
>>> config = MetaAppConfig.objects.get_active_config()
>>> print(f"Active config: {config.name}, Phone ID: {config.phone_number_id}")
```

### 2. Verify WhatsApp Flow is Published

```bash
# Check WhatsApp flow status
python manage.py shell
>>> from flows.models import WhatsAppFlow
>>> flow = WhatsAppFlow.objects.filter(name='tour_inquiry_whatsapp', is_active=True).first()
>>> print(f"Flow: {flow.name}, Status: {flow.sync_status}, Flow ID: {flow.flow_id}")
```

Expected output:
```
Flow: tour_inquiry_whatsapp, Status: published, Flow ID: <some_id>
```

### 3. Test End-to-End Flow

#### 3.1 Trigger the Flow

Send a message to your WhatsApp number that triggers the tour inquiry flow:
```
Message: "inquire" or "safari" or "tour"
```

#### 3.2 Check Initial Flow State

```bash
python manage.py shell
>>> from conversations.models import Contact
>>> from flows.models import ContactFlowState
>>> contact = Contact.objects.get(whatsapp_id="+1234567890")  # Replace with actual number
>>> flow_state = ContactFlowState.objects.get(contact=contact)
>>> print(f"Current step: {flow_state.current_step.name}")
>>> print(f"Context: {flow_state.flow_context_data}")
```

Expected:
```
Current step: wait_for_flow_response
Context: {'awaiting_inquiry_response': True}
```

#### 3.3 Submit WhatsApp Flow

On your phone:
1. Open the WhatsApp flow message
2. Fill in the inquiry details:
   - Destinations: "Kenya"
   - Preferred dates: "2024-12-15"
   - Number of travelers: 2
   - Notes: "Looking for wildlife safari"
3. Click "Submit"

#### 3.4 Check Logs

Look for these log messages in your Django logs:

```bash
# Tail the logs
tail -f logs/django.log  # or wherever your logs are

# Expected log sequence:
[INFO] nfm_reply (flow response) received for contact {contact_id}
[INFO] Saved WhatsAppFlowResponse for contact {contact_id} and flow tour_inquiry_whatsapp
[INFO] Successfully updated flow context for WhatsApp flow response
[INFO] Queued flow continuation task for WhatsApp flow response message {message_id}
[INFO] Transition condition met: From 'wait_for_flow_response' to 'process_inquiry_data'
```

#### 3.5 Verify Database Changes

```bash
python manage.py shell
>>> from conversations.models import Contact, Message
>>> from flows.models import ContactFlowState, WhatsAppFlowResponse
>>> from customer_data.models import TourInquiry

>>> contact = Contact.objects.get(whatsapp_id="+1234567890")

# 1. Check WhatsAppFlowResponse was created
>>> flow_response = WhatsAppFlowResponse.objects.filter(contact=contact).order_by('-created_at').first()
>>> print(f"Response created: {flow_response.created_at}")
>>> print(f"Response data: {flow_response.response_data}")
>>> print(f"Is processed: {flow_response.is_processed}")

# 2. Check Message was created
>>> message = Message.objects.filter(contact=contact, message_type='interactive').order_by('-timestamp').first()
>>> print(f"Message ID: {message.id}, Type: {message.message_type}")
>>> print(f"Content: {message.content_payload}")

# 3. Check flow state updated
>>> flow_state = ContactFlowState.objects.filter(contact=contact).first()
>>> if flow_state:
>>>     print(f"Current step: {flow_state.current_step.name}")
>>>     print(f"Context has response flag: {flow_state.flow_context_data.get('whatsapp_flow_response_received')}")
>>>     print(f"Destinations: {flow_state.flow_context_data.get('destinations')}")
>>> else:
>>>     print("Flow state cleared (flow completed)")

# 4. Check TourInquiry was created
>>> inquiry = TourInquiry.objects.filter(customer__contact=contact).order_by('-created_at').first()
>>> print(f"Inquiry ID: {inquiry.id}")
>>> print(f"Destinations: {inquiry.destinations}")
>>> print(f"Preferred dates: {inquiry.preferred_dates}")
>>> print(f"Number of travelers: {inquiry.number_of_travelers}")
```

Expected results:
- [x] WhatsAppFlowResponse exists with `is_processed=True`
- [x] Message exists with `message_type='interactive'`
- [x] Flow state either:
  - Still exists with `current_step` as the next step after processing
  - OR has been cleared (flow completed and ended)
- [x] Context had `whatsapp_flow_response_received=True` (before transition)
- [x] TourInquiry created with correct data
- [x] All data matches what was submitted in the flow

### 4. Check Webhook Event Log

```bash
python manage.py shell
>>> from meta_integration.models import WebhookEventLog
>>> log = WebhookEventLog.objects.filter(event_type__contains='interactive').order_by('-received_at').first()
>>> print(f"Event type: {log.event_type}")
>>> print(f"Processing status: {log.processing_status}")
>>> print(f"Notes: {log.processing_notes}")
```

Expected:
```
Event type: message_interactive
Processing status: processed
Notes: Flow context updated with WhatsApp flow data. Flow continuation queued.
```

### 5. Verify Celery Task Execution

```bash
# Check Celery logs
tail -f logs/celery.log  # or wherever your celery logs are

# Look for:
[INFO] Task flows.tasks.process_flow_for_message_task[...] succeeded
```

Or check in Django admin:
1. Go to `http://localhost:8000/admin/`
2. Navigate to Django Celery Results > Task results
3. Find the `process_flow_for_message_task` for your message
4. Verify status is `SUCCESS`

### 6. Test Error Handling

#### 6.1 Test with No Flow State

Try submitting a flow response when the contact is not in a flow:

Expected behavior:
- Response is saved
- Error logged: "No active flow state for contact"
- No transition occurs (graceful failure)

#### 6.2 Test with Invalid Data

Submit a flow with missing required fields:

Expected behavior:
- Response is saved
- Context is updated (whatever data is present)
- Transition still occurs (downstream validation handles invalid data)

## Common Issues and Solutions

### Issue 1: Transition Not Happening

**Symptoms:**
- Flow stays at `wait_for_flow_response` step
- No log message about transition condition met

**Check:**
```bash
python manage.py shell
>>> from flows.models import ContactFlowState
>>> contact = Contact.objects.get(whatsapp_id="+1234567890")
>>> flow_state = ContactFlowState.objects.get(contact=contact)
>>> print(f"Response flag: {flow_state.flow_context_data.get('whatsapp_flow_response_received')}")
>>> print(f"Current step: {flow_state.current_step.name}")
>>> print(f"Transitions: {list(flow_state.current_step.outgoing_transitions.all())}")
```

**Solutions:**
- Ensure `whatsapp_flow_response_received` is `True` in context
- Verify transition condition config matches: `{"type": "whatsapp_flow_response_received"}`
- Check Celery task was queued and executed successfully

### Issue 2: Celery Task Not Running

**Symptoms:**
- Response processed but no transition
- No Celery log messages

**Check:**
```bash
# Is Celery worker running?
celery -A whatsappcrm_backend inspect active

# Check Redis connection
redis-cli ping
```

**Solutions:**
- Start Celery worker: `celery -A whatsappcrm_backend worker -l info`
- Check Redis is running: `redis-server`
- Verify `CELERY_BROKER_URL` in settings

### Issue 3: Transaction Rollback

**Symptoms:**
- WhatsAppFlowResponse not created
- Flow context not updated
- Error in logs

**Check:**
```bash
# Look for error in logs
grep "Error processing WhatsApp flow response" logs/django.log
```

**Solutions:**
- Check database connection
- Verify model fields are correct
- Look for validation errors in logs

## Performance Verification

### Check Response Times

```bash
# Monitor webhook response times
grep "EVENT_RECEIVED" logs/django.log | tail -20

# Should see immediate responses (< 500ms)
```

### Check Task Queue Length

```bash
# Check pending tasks
celery -A whatsappcrm_backend inspect reserved

# Should be empty or low number
```

### Check Database Lock Wait Times

```bash
python manage.py dbshell
# For PostgreSQL:
SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock';

# Should show minimal lock contention
```

## Success Criteria

✅ Flow triggered successfully
✅ WhatsApp flow message sent to user
✅ User submits flow with data
✅ Webhook receives nfm_reply
✅ Message object created
✅ WhatsAppFlowResponse record created
✅ Flow context updated with `whatsapp_flow_response_received=True`
✅ Flow context contains all submitted data
✅ Celery task queued and executed
✅ Transition condition evaluated and met
✅ Flow moved to next step automatically
✅ Next step actions executed (e.g., TourInquiry created)
✅ User receives confirmation message
✅ WebhookEventLog shows `processed` status
✅ No errors in logs
✅ System responsive (no timeouts)

## Automated Verification Script

Save this as `verify_whatsapp_flow.py`:

```python
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')
django.setup()

from flows.models import WhatsAppFlow, ContactFlowState, WhatsAppFlowResponse
from meta_integration.models import MetaAppConfig, WebhookEventLog
from conversations.models import Contact
from customer_data.models import TourInquiry

def verify_setup():
    """Verify basic setup is correct."""
    print("=" * 50)
    print("VERIFYING SETUP")
    print("=" * 50)
    
    # Check Meta config
    try:
        config = MetaAppConfig.objects.get_active_config()
        print(f"✓ Active Meta config: {config.name}")
    except:
        print("✗ No active Meta config found")
        return False
    
    # Check WhatsApp flow
    try:
        flow = WhatsAppFlow.objects.get(name='tour_inquiry_whatsapp', is_active=True)
        print(f"✓ WhatsApp flow: {flow.name} (Status: {flow.sync_status})")
    except:
        print("✗ WhatsApp flow not found or not published")
        return False
    
    print("\n✓ Setup verification passed\n")
    return True

def verify_recent_submission(contact_phone):
    """Verify a recent flow submission for a contact."""
    print("=" * 50)
    print(f"VERIFYING SUBMISSION FOR {contact_phone}")
    print("=" * 50)
    
    try:
        contact = Contact.objects.get(whatsapp_id=contact_phone)
    except:
        print(f"✗ Contact {contact_phone} not found")
        return
    
    # Check WhatsAppFlowResponse
    response = WhatsAppFlowResponse.objects.filter(contact=contact).order_by('-created_at').first()
    if response:
        print(f"✓ Flow response created at {response.created_at}")
        print(f"  Data: {response.response_data}")
    else:
        print("✗ No flow response found")
    
    # Check flow state or completion
    flow_state = ContactFlowState.objects.filter(contact=contact).first()
    if flow_state:
        print(f"✓ Flow state exists")
        print(f"  Current step: {flow_state.current_step.name}")
        print(f"  Response flag: {flow_state.flow_context_data.get('whatsapp_flow_response_received')}")
    else:
        print("✓ Flow completed (state cleared)")
    
    # Check TourInquiry
    inquiry = TourInquiry.objects.filter(customer__contact=contact).order_by('-created_at').first()
    if inquiry:
        print(f"✓ Tour inquiry created: #{inquiry.id}")
        print(f"  Destinations: {inquiry.destinations}")
    else:
        print("⚠ No tour inquiry found (may not have reached that step yet)")
    
    # Check webhook logs
    log = WebhookEventLog.objects.filter(
        event_type__contains='interactive'
    ).order_by('-received_at').first()
    if log:
        print(f"✓ Webhook log: {log.processing_status}")
        print(f"  Notes: {log.processing_notes}")
    
    print("\n✓ Verification complete\n")

if __name__ == '__main__':
    if verify_setup():
        import sys
        if len(sys.argv) > 1:
            verify_recent_submission(sys.argv[1])
        else:
            print("Usage: python verify_whatsapp_flow.py <contact_phone>")
            print("Example: python verify_whatsapp_flow.py +1234567890")
```

Run with:
```bash
python verify_whatsapp_flow.py +1234567890
```

## Conclusion

If all verification steps pass, the automatic transition system is working correctly!
