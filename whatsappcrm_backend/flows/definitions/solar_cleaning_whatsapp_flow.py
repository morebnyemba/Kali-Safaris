# whatsappcrm_backend/flows/definitions/solar_cleaning_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Solar Panel Cleaning Request.
This is a conversion of the traditional flow to WhatsApp's interactive flow format.
"""

SOLAR_CLEANING_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "WELCOME",
            "title": "Solar Panel Cleaning",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "roof_type": {
                    "type": "string",
                    "__example__": "tile"
                },
                "panel_type": {
                    "type": "string",
                    "__example__": "monocrystalline"
                },
                "panel_count": {
                    "type": "number",
                    "__example__": 10
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "availability": {
                    "type": "string",
                    "__example__": "morning"
                },
                "address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Solar Panel Cleaning Service"
                    },
                    {
                        "type": "TextBody",
                        "text": "Let's get a few details to provide you with a quote for our solar panel cleaning service."
                    },
                    {
                        "type": "Footer",
                        "label": "Get Started",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "CUSTOMER_INFO"
                            },
                            "payload": {
                                "full_name": "",
                                "contact_phone": "",
                                "roof_type": "",
                                "panel_type": "",
                                "panel_count": 0,
                                "preferred_date": "",
                                "availability": "",
                                "address": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "CUSTOMER_INFO",
            "title": "Your Information",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "roof_type": {
                    "type": "string",
                    "__example__": "tile"
                },
                "panel_type": {
                    "type": "string",
                    "__example__": "monocrystalline"
                },
                "panel_count": {
                    "type": "number",
                    "__example__": 10
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "availability": {
                    "type": "string",
                    "__example__": "morning"
                },
                "address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Contact Information"
                    },
                    {
                        "type": "TextInput",
                        "name": "full_name",
                        "label": "Full Name",
                        "required": True,
                        "input-type": "text"
                    },
                    {
                        "type": "TextInput",
                        "name": "contact_phone",
                        "label": "Contact Number",
                        "required": True,
                        "input-type": "phone",
                        "helper-text": "e.g., +263771234567"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "ROOF_DETAILS"
                            },
                            "payload": {
                                "full_name": "${form.full_name}",
                                "contact_phone": "${form.contact_phone}",
                                "roof_type": "${data.roof_type}",
                                "panel_type": "${data.panel_type}",
                                "panel_count": "${data.panel_count}",
                                "preferred_date": "${data.preferred_date}",
                                "availability": "${data.availability}",
                                "address": "${data.address}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "ROOF_DETAILS",
            "title": "Roof Information",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "roof_type": {
                    "type": "string",
                    "__example__": "tile"
                },
                "panel_type": {
                    "type": "string",
                    "__example__": "monocrystalline"
                },
                "panel_count": {
                    "type": "number",
                    "__example__": 10
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "availability": {
                    "type": "string",
                    "__example__": "morning"
                },
                "address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Roof Type"
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "roof_type",
                        "label": "What type of roof do you have?",
                        "required": True,
                        "data-source": [
                            {"id": "tile", "title": "Tile Roof"},
                            {"id": "ibr_metal", "title": "IBR / Metal Sheet"},
                            {"id": "flat_concrete", "title": "Flat Concrete"},
                            {"id": "other", "title": "Other / Not Sure"}
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "PANEL_DETAILS"
                            },
                            "payload": {
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "roof_type": "${form.roof_type}",
                                "panel_type": "${data.panel_type}",
                                "panel_count": "${data.panel_count}",
                                "preferred_date": "${data.preferred_date}",
                                "availability": "${data.availability}",
                                "address": "${data.address}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "PANEL_DETAILS",
            "title": "Solar Panel Information",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "roof_type": {
                    "type": "string",
                    "__example__": "tile"
                },
                "panel_type": {
                    "type": "string",
                    "__example__": "monocrystalline"
                },
                "panel_count": {
                    "type": "number",
                    "__example__": 10
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "availability": {
                    "type": "string",
                    "__example__": "morning"
                },
                "address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Panel Details"
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "panel_type",
                        "label": "What type of solar panels do you have?",
                        "required": True,
                        "data-source": [
                            {"id": "monocrystalline", "title": "Monocrystalline"},
                            {"id": "polycrystalline", "title": "Polycrystalline"},
                            {"id": "not_sure", "title": "I'm Not Sure"}
                        ]
                    },
                    {
                        "type": "TextInput",
                        "name": "panel_count",
                        "label": "Number of Solar Panels",
                        "required": True,
                        "input-type": "number",
                        "helper-text": "Enter the total number of panels"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "SCHEDULE"
                            },
                            "payload": {
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "roof_type": "${data.roof_type}",
                                "panel_type": "${form.panel_type}",
                                "panel_count": "${form.panel_count}",
                                "preferred_date": "",
                                "availability": "",
                                "address": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "SCHEDULE",
            "title": "Service Schedule",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "roof_type": {
                    "type": "string",
                    "__example__": "tile"
                },
                "panel_type": {
                    "type": "string",
                    "__example__": "monocrystalline"
                },
                "panel_count": {
                    "type": "number",
                    "__example__": 10
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "availability": {
                    "type": "string",
                    "__example__": "morning"
                },
                "address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Schedule Your Service"
                    },
                    {
                        "type": "DatePicker",
                        "name": "preferred_date",
                        "label": "Preferred Service Date",
                        "required": True
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "availability",
                        "label": "Preferred Time",
                        "required": True,
                        "data-source": [
                            {"id": "morning", "title": "Morning"},
                            {"id": "afternoon", "title": "Afternoon"}
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "LOCATION"
                            },
                            "payload": {
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "roof_type": "${data.roof_type}",
                                "panel_type": "${data.panel_type}",
                                "panel_count": "${data.panel_count}",
                                "preferred_date": "${form.preferred_date}",
                                "availability": "${form.availability}",
                                "address": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "LOCATION",
            "title": "Service Location",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "roof_type": {
                    "type": "string",
                    "__example__": "tile"
                },
                "panel_type": {
                    "type": "string",
                    "__example__": "monocrystalline"
                },
                "panel_count": {
                    "type": "number",
                    "__example__": 10
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "availability": {
                    "type": "string",
                    "__example__": "morning"
                },
                "address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Location Details"
                    },
                    {
                        "type": "TextInput",
                        "name": "address",
                        "label": "Full Service Address",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Provide the complete address"
                    },
                    {
                        "type": "TextBody",
                        "text": "Note: You can share your location pin via WhatsApp after submitting this form."
                    },
                    {
                        "type": "Footer",
                        "label": "Submit Request",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "roof_type": "${data.roof_type}",
                                "panel_type": "${data.panel_type}",
                                "panel_count": "${data.panel_count}",
                                "preferred_date": "${data.preferred_date}",
                                "availability": "${data.availability}",
                                "address": "${form.address}"
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


# Metadata for the flow
SOLAR_CLEANING_FLOW_METADATA = {
    "name": "solar_cleaning_whatsapp",
    "friendly_name": "Solar Panel Cleaning Request (Interactive)",
    "description": "Interactive WhatsApp flow for requesting solar panel cleaning services",
    "trigger_keywords": ["solar cleaning", "clean panels"],
    "is_active": True
}
