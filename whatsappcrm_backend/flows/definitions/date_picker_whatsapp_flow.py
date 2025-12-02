# whatsappcrm_backend/flows/definitions/date_picker_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Date Picker.
This is a reusable interactive flow for selecting dates.
"""

DATE_PICKER_WHATSAPP_FLOW_METADATA = {
    "name": "date_picker_whatsapp_flow",
    "friendly_name": "Date Picker WhatsApp Flow",
    "description": "Interactive WhatsApp flow for selecting dates.",
    "trigger_keywords": ["date picker", "select date"],
    "is_active": True,
    "flow_definition_name": None  # This is a reusable component, not a replacement for a specific traditional flow
}

DATE_PICKER_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "DATE_PICKER",
            "title": "Select Date",
            "data": {
                "selected_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Choose Your Date"
                    },
                    {
                        "type": "TextBody",
                        "text": "Please select your preferred date."
                    },
                    {
                        "type": "DatePicker",
                        "name": "selected_date",
                        "label": "Select Date",
                        "required": True
                    },
                    {
                        "type": "Footer",
                        "label": "Confirm Selection",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "selected_date": "${form.selected_date}"
                            }
                        }
                    }
                ]
            },
            "terminal": True,
            "success": True
        }
    ]
}

