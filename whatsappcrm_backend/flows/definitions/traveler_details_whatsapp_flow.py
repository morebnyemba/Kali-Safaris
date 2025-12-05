# whatsappcrm_backend/flows/definitions/traveler_details_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Traveler Details.
This is a reusable interactive flow for collecting individual traveler information.
"""

TRAVELER_DETAILS_WHATSAPP_FLOW_METADATA = {
    "name": "traveler_details_whatsapp_flow",
    "friendly_name": "Traveler Details WhatsApp Flow",
    "description": "Interactive WhatsApp flow for collecting traveler details (name, age, nationality, medical needs).",
    "trigger_keywords": ["traveler details", "passenger info"],
    "is_active": True,
    "flow_definition_name": None  # This is a reusable component used in loops
}

TRAVELER_DETAILS_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "TRAVELER_INFO",
            "title": "Traveler Details",
            "data": {
                "traveler_number": {
                    "type": "string",
                    "__example__": "1"
                },
                "total_travelers": {
                    "type": "string",
                    "__example__": "3"
                },
                "traveler_name": {
                    "type": "string",
                    "__example__": "John Smith"
                },
                "traveler_age": {
                    "type": "string",
                    "__example__": "35"
                },
                "traveler_nationality": {
                    "type": "string",
                    "__example__": "United States"
                },
                "traveler_medical": {
                    "type": "string",
                    "__example__": "None"
                },
                "traveler_gender": {
                    "type": "string",
                    "__example__": "Male"
                },
                "traveler_id_number": {
                    "type": "string",
                    "__example__": "123456789"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Traveler ${data.traveler_number} of ${data.total_travelers}"
                    },
                    {
                        "type": "TextBody",
                        "text": "Please provide the details for this traveler."
                    },
                    {
                        "type": "TextInput",
                        "name": "traveler_name",
                        "label": "Full Name",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter the traveler's full name"
                    },
                    {
                        "type": "TextInput",
                        "name": "traveler_age",
                        "label": "Age",
                        "required": True,
                        "input-type": "number",
                        "helper-text": "Enter the traveler's age"
                    },
                    {
                        "type": "TextInput",
                        "name": "traveler_nationality",
                        "label": "Nationality",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter the traveler's nationality"
                    },
                    {
                        "type": "TextInput",
                        "name": "traveler_medical",
                        "label": "Dietary/Medical Needs",
                        "required": False,
                        "input-type": "text",
                        "helper-text": "Any dietary restrictions or medical needs (optional)"
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "traveler_gender",
                        "label": "Gender",
                        "required": True,
                        "data-source": [
                            {
                                "id": "male",
                                "title": "Male"
                            },
                            {
                                "id": "female",
                                "title": "Female"
                            },
                            {
                                "id": "other",
                                "title": "Other"
                            }
                        ]
                    },
                    {
                        "type": "TextInput",
                        "name": "traveler_id_number",
                        "label": "ID/Passport Number",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter ID or Passport number"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "traveler_name": "${form.traveler_name}",
                                "traveler_age": "${form.traveler_age}",
                                "traveler_nationality": "${form.traveler_nationality}",
                                "traveler_medical": "${form.traveler_medical}",
                                "traveler_gender": "${form.traveler_gender}",
                                "traveler_id_number": "${form.traveler_id_number}"
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
