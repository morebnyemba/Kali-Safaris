# whatsappcrm_backend/flows/definitions/date_picker_whatsapp_flow.py

DATE_PICKER_WHATSAPP_FLOW_METADATA = {
    "name": "date_picker_whatsapp_flow",
    "friendly_name": "Date Picker WhatsApp Flow",
    "description": "Interactive WhatsApp flow for selecting dates.",
    "trigger_keywords": ["date picker", "select date"],
    "is_active": True
}

DATE_PICKER_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "DATE_PICKER",
            "title": "Select Date(s)",
            "data": {
                "selected_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {"type": "TextHeading", "text": "Choose Your Dates"},
                    {"type": "TextBody", "text": "Please select the date or date range."},
                    {
                        "type": "DatePicker",
                        "name": "selected_date",
                        "label": "Select Date(s)",
                        "mode": "single",
                        "range": {"min": "", "max": ""}
                    },
                    {
                        "type": "Footer",
                        "label": "Confirm Selection",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {"selected_date": "${form.selected_date}"}
                        }
                    }
                ]
            }
        }
    ]
}