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
            "id": "WELCOME",
            "title": "Date Selection",
            "data": {
                "start_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "end_date": {
                    "type": "string",
                    "__example__": "2025-12-30"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Select Your Tour Dates"
                    },
                    {
                        "type": "TextBody",
                        "text": "Please choose your start and end dates for the tour."
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "DATE_PICKER"
                            },
                            "payload": {
                                "start_date": "",
                                "end_date": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "DATE_PICKER",
            "title": "Select Tour Dates",
            "data": {
                "start_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "end_date": {
                    "type": "string",
                    "__example__": "2025-12-30"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Choose Your Tour Dates"
                    },
                    {
                        "type": "TextBody",
                        "text": "Please select your start and end dates for the tour."
                    },
                    {
                        "type": "DatePicker",
                        "name": "start_date",
                        "label": "Start Date",
                        "required": True
                    },
                    {
                        "type": "DatePicker",
                        "name": "end_date",
                        "label": "End Date",
                        "required": True
                    },
                    {
                        "type": "Footer",
                        "label": "Confirm Selection",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "start_date": "${form.start_date}",
                                "end_date": "${form.end_date}"
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

