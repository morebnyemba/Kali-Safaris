# whatsappcrm_backend/flows/definitions/date_picker_whatsapp_flow.py

WHATSAPP_FLOW_DATE_PICKER = {
    "name": "date_picker_whatsapp_flow",
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