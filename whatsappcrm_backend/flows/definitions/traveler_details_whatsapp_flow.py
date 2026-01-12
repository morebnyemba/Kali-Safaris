# whatsappcrm_backend/flows/definitions/traveler_details_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Traveler Details.
This is a reusable interactive flow for collecting individual traveler information.

Note: PhotoPicker components in WhatsApp Flow API v7.3 require both 
'min-uploaded-photos' and 'max-uploaded-photos' properties (range: 0-30 and 1-30 respectively).
Without these properties, the flow will fail Meta's validation when publishing.
"""

TRAVELER_DETAILS_WHATSAPP_FLOW_METADATA = {
    "name": "traveler_details_whatsapp_flow",
    "friendly_name": "Traveler Details WhatsApp Flow",
    "description": "Interactive WhatsApp flow for collecting traveler details (name, age, nationality, medical needs, gender, ID number).",
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
                        "text": "Traveler Details"
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
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "ID_DOCUMENT_UPLOAD"
                            },
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
            }
        },
        {
            "id": "ID_DOCUMENT_UPLOAD",
            "title": "Upload ID Document",
            "data": {
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
                        "text": "Upload ID/Passport"
                    },
                    {
                        "type": "TextBody",
                        "text": "Please upload a clear photo of your ID or Passport for ${data.traveler_name}. This is required for park entry."
                    },
                    {
                        "type": "PhotoPicker",
                        "name": "id_document_photo",
                        "label": "ID/Passport Photo",
                        "description": "Take or upload a photo of the ID/Passport",
                        "photo-source": "camera_gallery",
                        "required": True,
                        "min-uploaded-photos": 1,
                        "max-uploaded-photos": 1
                    },
                    {
                        "type": "Footer",
                        "label": "Submit Details",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "traveler_name": "${data.traveler_name}",
                                "traveler_age": "${data.traveler_age}",
                                "traveler_nationality": "${data.traveler_nationality}",
                                "traveler_medical": "${data.traveler_medical}",
                                "traveler_gender": "${data.traveler_gender}",
                                "traveler_id_number": "${data.traveler_id_number}",
                                "id_document_photo": "${form.id_document_photo}"
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
