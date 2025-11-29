# whatsappcrm_backend/flows/definitions/starlink_installation_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Starlink Installation Request.
This is a conversion of the traditional flow to WhatsApp's interactive flow format.
"""

STARLINK_INSTALLATION_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "WELCOME",
            "title": "Starlink Installation",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "kit_type": {
                    "type": "string",
                    "__example__": "standard"
                },
                "mount_location": {
                    "type": "string",
                    "__example__": "On the roof"
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "availability": {
                    "type": "string",
                    "__example__": "morning"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Request Starlink Installation"
                    },
                    {
                        "type": "TextBody",
                        "text": "Let's get your Starlink installation scheduled. We'll need to collect a few details to process your request."
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
                                "kit_type": "",
                                "mount_location": "",
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
            "title": "Customer Information",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "kit_type": {
                    "type": "string",
                    "__example__": "standard"
                },
                "mount_location": {
                    "type": "string",
                    "__example__": "On the roof"
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
                        "text": "Your Contact Information"
                    },
                    {
                        "type": "TextInput",
                        "name": "full_name",
                        "label": "Full Name",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter your full name for the installation booking"
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
                                "name": "KIT_DETAILS"
                            },
                            "payload": {
                                "full_name": "${form.full_name}",
                                "contact_phone": "${form.contact_phone}",
                                "kit_type": "",
                                "mount_location": "",
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
            "id": "KIT_DETAILS",
            "title": "Starlink Kit Details",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "kit_type": {
                    "type": "string",
                    "__example__": "standard"
                },
                "mount_location": {
                    "type": "string",
                    "__example__": "On the roof"
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
                        "text": "Kit Information"
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "kit_type",
                        "label": "What type of Starlink kit do you have?",
                        "required": True,
                        "data-source": [
                            {"id": "standard", "title": "Standard"},
                            {"id": "high_performance", "title": "High Performance"},
                            {"id": "other", "title": "Other/Not Sure"}
                        ]
                    },
                    {
                        "type": "TextInput",
                        "name": "mount_location",
                        "label": "Preferred Mount Location",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "e.g., On the roof, on a pole in the yard"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "INSTALLATION_SCHEDULE"
                            },
                            "payload": {
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "kit_type": "${form.kit_type}",
                                "mount_location": "${form.mount_location}",
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
            "id": "INSTALLATION_SCHEDULE",
            "title": "Installation Schedule",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "kit_type": {
                    "type": "string",
                    "__example__": "standard"
                },
                "mount_location": {
                    "type": "string",
                    "__example__": "On the roof"
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
                        "text": "Schedule Your Installation"
                    },
                    {
                        "type": "DatePicker",
                        "name": "preferred_date",
                        "label": "Preferred Installation Date",
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
                                "name": "LOCATION_INFO"
                            },
                            "payload": {
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "kit_type": "${data.kit_type}",
                                "mount_location": "${data.mount_location}",
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
            "id": "LOCATION_INFO",
            "title": "Installation Location",
            "data": {
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "kit_type": {
                    "type": "string",
                    "__example__": "standard"
                },
                "mount_location": {
                    "type": "string",
                    "__example__": "On the roof"
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
                        "label": "Full Installation Address",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Provide the complete address with street, suburb, and city"
                    },
                    {
                        "type": "TextBody",
                        "text": "Note: You'll be able to share your location pin via WhatsApp after submitting this form."
                    },
                    {
                        "type": "Footer",
                        "label": "Submit Request",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "kit_type": "${data.kit_type}",
                                "mount_location": "${data.mount_location}",
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
STARLINK_INSTALLATION_FLOW_METADATA = {
    "name": "starlink_installation_whatsapp",
    "friendly_name": "Starlink Installation Request (Interactive)",
    "description": "Interactive WhatsApp flow for scheduling Starlink installations",
    "trigger_keywords": ["request starlink", "starlink installation"],
    "is_active": True
}
