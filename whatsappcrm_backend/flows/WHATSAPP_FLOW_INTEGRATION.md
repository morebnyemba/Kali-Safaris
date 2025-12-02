# WhatsApp Flow Integration - Usage Guide

## Overview
This guide explains how to sync WhatsApp Flows and link them to traditional conversational flows so they can be used automatically when available.

## How It Works

When a contact triggers a traditional flow, the system checks if there's an active, published WhatsApp Flow linked to it. If found, the WhatsApp Flow is used instead, providing a better user experience with Meta's native interactive flows.

## Syncing WhatsApp Flows

### Basic Usage
```bash
python manage.py sync_whatsapp_flows
```

This syncs all WhatsApp Flows defined in the system.

### Sync Specific Flow
```bash
python manage.py sync_whatsapp_flows --flow=tour_inquiry
python manage.py sync_whatsapp_flows --flow=date_picker
```

### Publish After Sync
```bash
python manage.py sync_whatsapp_flows --publish
```

This syncs the flows and immediately publishes them to Meta (makes them live).

### Force Re-sync
```bash
python manage.py sync_whatsapp_flows --force
```

Force re-sync even if the flow already exists and is published.

## Linking WhatsApp Flows to Traditional Flows

WhatsApp Flows are linked to traditional flows via the `flow_definition_name` field in their metadata.

### Example: Tour Inquiry Flow

In `tour_inquiry_whatsapp_flow.py`:
```python
TOUR_INQUIRY_WHATSAPP_FLOW_METADATA = {
    "name": "tour_inquiry_whatsapp",
    "friendly_name": "Tour Inquiry WhatsApp Flow",
    "description": "...",
    "flow_definition_name": "tour_inquiry_flow",  # Links to traditional flow
    "is_active": True
}
```

When synced, this WhatsApp Flow will be linked to the `tour_inquiry_flow` traditional flow.

### Reusable Components

Some WhatsApp Flows are reusable components (like date pickers) that aren't meant to replace a specific traditional flow:

```python
DATE_PICKER_WHATSAPP_FLOW_METADATA = {
    "name": "date_picker_whatsapp_flow",
    "friendly_name": "Date Picker WhatsApp Flow",
    "flow_definition_name": None,  # Not linked to a specific flow
    "is_active": True
}
```

## Creating New WhatsApp Flows

1. **Define the WhatsApp Flow JSON** following Meta's specification
2. **Add metadata** with the traditional flow name to link to:
   ```python
   MY_FLOW_METADATA = {
       "name": "my_whatsapp_flow",
       "friendly_name": "My WhatsApp Flow",
       "description": "Flow description",
       "flow_definition_name": "my_traditional_flow",  # Important!
       "is_active": True
   }
   ```

3. **Import and register** in `sync_whatsapp_flows.py`:
   ```python
   from flows.definitions.my_flow import MY_FLOW, MY_FLOW_METADATA
   
   # In handle method, add to flows_to_sync
   ```

4. **Create the traditional flow** in database with matching name
5. **Run sync command**

## Verification

After syncing, verify the link was created:
```python
from flows.models import WhatsApp Flow, Flow

# Get the WhatsApp Flow
wf = WhatsAppFlow.objects.get(name='tour_inquiry_whatsapp')

# Check it's linked
print(f"Linked to: {wf.flow_definition.name if wf.flow_definition else 'None'}")
# Output: Linked to: tour_inquiry_flow
```

## Troubleshooting

### WhatsApp Flow not being used
1. Check the WhatsApp Flow is synced: `sync_status='published'`
2. Check it has a flow_id from Meta
3. Check it's linked to the traditional flow via `flow_definition`
4. Check it's active: `is_active=True`

### Warning: Traditional flow not found
The traditional flow specified in `flow_definition_name` doesn't exist in the database. Create it first using the flow definition scripts.

### Force re-sync to update links
If you added a `flow_definition_name` to an existing WhatsApp Flow's metadata, run:
```bash
python manage.py sync_whatsapp_flows --force
```

## Benefits

- **Better UX**: Native WhatsApp Flows provide better interactive forms
- **Seamless fallback**: If WhatsApp Flow isn't available, traditional flow is used
- **Easy migration**: Add WhatsApp Flows without changing traditional flow logic
- **Centralized management**: Link flows via simple metadata configuration
