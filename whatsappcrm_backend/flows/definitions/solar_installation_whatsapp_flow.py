# whatsappcrm_backend/flows/definitions/solar_installation_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Solar Installation Request.
This is a simplified conversion focusing on the core installation scheduling flow.
Note: Complex logic like order verification will be handled in the backend processing.
"""

SOLAR_INSTALLATION_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "WELCOME",
            "title": "Solar Installation",
            "data": {
                "installation_type": {
                    "type": "string",
                    "__example__": "residential"
                },
                "order_number": {
                    "type": "string",
                    "__example__": "HAN-12345"
                },
                "branch": {
                    "type": "string",
                    "__example__": "Harare"
                },
                "sales_person": {
                    "type": "string",
                    "__example__": "John Smith"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Request Solar Installation"
                    },
                    {
                        "type": "TextBody",
                        "text": "Let's schedule your solar installation. We'll collect the necessary details to process your request."
                    },
                    {
                        "type": "Footer",
                        "label": "Get Started",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "INSTALLATION_TYPE"
                            },
                            "payload": {
                                "installation_type": "",
                                "order_number": "",
                                "branch": "",
                                "sales_person": "",
                                "full_name": "",
                                "contact_phone": "",
                                "alt_contact_name": "",
                                "alt_contact_phone": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "INSTALLATION_TYPE",
            "title": "Installation Type",
            "data": {
                "installation_type": {
                    "type": "string",
                    "__example__": "residential"
                },
                "order_number": {
                    "type": "string",
                    "__example__": "HAN-12345"
                },
                "branch": {
                    "type": "string",
                    "__example__": "Harare"
                },
                "sales_person": {
                    "type": "string",
                    "__example__": "John Smith"
                },
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "alt_contact_name": {
                    "type": "string",
                    "__example__": "John Doe"
                },
                "alt_contact_phone": {
                    "type": "string",
                    "__example__": "+263779876543"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Property Type"
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "installation_type",
                        "label": "Is this for Residential or Commercial property?",
                        "required": True,
                        "data-source": [
                            {"id": "residential", "title": "Residential"},
                            {"id": "commercial", "title": "Commercial"}
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "ORDER_INFO"
                            },
                            "payload": {
                                "installation_type": "${form.installation_type}",
                                "order_number": "",
                                "branch": "",
                                "sales_person": "",
                                "full_name": "",
                                "contact_phone": "",
                                "alt_contact_name": "",
                                "alt_contact_phone": "",
                                "preferred_date": "",
                                "availability": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "ORDER_INFO",
            "title": "Order Information",
            "data": {
                "installation_type": {
                    "type": "string",
                    "__example__": "residential"
                },
                "order_number": {
                    "type": "string",
                    "__example__": "HAN-12345"
                },
                "branch": {
                    "type": "string",
                    "__example__": "Harare"
                },
                "sales_person": {
                    "type": "string",
                    "__example__": "John Smith"
                },
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "alt_contact_name": {
                    "type": "string",
                    "__example__": "John Doe"
                },
                "alt_contact_phone": {
                    "type": "string",
                    "__example__": "+263779876543"
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
                        "text": "Order Details"
                    },
                    {
                        "type": "TextInput",
                        "name": "order_number",
                        "label": "Order Number",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "e.g., HAN-12345, 12345/PO, or AV01/0034506"
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "branch",
                        "label": "Select Branch",
                        "required": True,
                        "data-source": [
                            {"id": "Harare", "title": "Harare"},
                            {"id": "Bulawayo", "title": "Bulawayo"},
                            {"id": "Mutare", "title": "Mutare"},
                            {"id": "Other", "title": "Other"}
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "SALES_INFO"
                            },
                            "payload": {
                                "installation_type": "${data.installation_type}",
                                "order_number": "${form.order_number}",
                                "branch": "${form.branch}",
                                "sales_person": "",
                                "full_name": "",
                                "contact_phone": "",
                                "alt_contact_name": "",
                                "alt_contact_phone": "",
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
            "id": "SALES_INFO",
            "title": "Sales Information",
            "data": {
                "installation_type": {
                    "type": "string",
                    "__example__": "residential"
                },
                "order_number": {
                    "type": "string",
                    "__example__": "HAN-12345"
                },
                "branch": {
                    "type": "string",
                    "__example__": "Harare"
                },
                "sales_person": {
                    "type": "string",
                    "__example__": "John Smith"
                },
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "alt_contact_name": {
                    "type": "string",
                    "__example__": "John Doe"
                },
                "alt_contact_phone": {
                    "type": "string",
                    "__example__": "+263779876543"
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
                        "text": "Sales Representative"
                    },
                    {
                        "type": "TextInput",
                        "name": "sales_person",
                        "label": "Sales Person Name",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter the name of your sales representative"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "CUSTOMER_INFO"
                            },
                            "payload": {
                                "installation_type": "${data.installation_type}",
                                "order_number": "${data.order_number}",
                                "branch": "${data.branch}",
                                "sales_person": "${form.sales_person}",
                                "full_name": "",
                                "contact_phone": "",
                                "alt_contact_name": "",
                                "alt_contact_phone": "",
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
                "installation_type": {
                    "type": "string",
                    "__example__": "residential"
                },
                "order_number": {
                    "type": "string",
                    "__example__": "HAN-12345"
                },
                "branch": {
                    "type": "string",
                    "__example__": "Harare"
                },
                "sales_person": {
                    "type": "string",
                    "__example__": "John Smith"
                },
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "alt_contact_name": {
                    "type": "string",
                    "__example__": "John Doe"
                },
                "alt_contact_phone": {
                    "type": "string",
                    "__example__": "+263779876543"
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
                        "text": "Contact Details"
                    },
                    {
                        "type": "TextInput",
                        "name": "full_name",
                        "label": "Client Name",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Full name as it appears on the invoice"
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
                        "type": "TextInput",
                        "name": "alt_contact_name",
                        "label": "Alternative Contact Name",
                        "required": False,
                        "input-type": "text",
                        "helper-text": "Optional - Enter N/A if not applicable"
                    },
                    {
                        "type": "TextInput",
                        "name": "alt_contact_phone",
                        "label": "Alternative Contact Number",
                        "required": False,
                        "input-type": "phone",
                        "helper-text": "Optional - Enter N/A if not applicable"
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
                                "installation_type": "${data.installation_type}",
                                "order_number": "${data.order_number}",
                                "branch": "${data.branch}",
                                "sales_person": "${data.sales_person}",
                                "full_name": "${form.full_name}",
                                "contact_phone": "${form.contact_phone}",
                                "alt_contact_name": "${form.alt_contact_name}",
                                "alt_contact_phone": "${form.alt_contact_phone}",
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
            "title": "Installation Schedule",
            "data": {
                "installation_type": {
                    "type": "string",
                    "__example__": "residential"
                },
                "order_number": {
                    "type": "string",
                    "__example__": "HAN-12345"
                },
                "branch": {
                    "type": "string",
                    "__example__": "Harare"
                },
                "sales_person": {
                    "type": "string",
                    "__example__": "John Smith"
                },
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "alt_contact_name": {
                    "type": "string",
                    "__example__": "John Doe"
                },
                "alt_contact_phone": {
                    "type": "string",
                    "__example__": "+263779876543"
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
                        "type": "TextBody",
                        "text": "Note: Installations are conducted within 48 hours of system delivery. This date is for confirmation purposes."
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
                                "name": "LOCATION"
                            },
                            "payload": {
                                "installation_type": "${data.installation_type}",
                                "order_number": "${data.order_number}",
                                "branch": "${data.branch}",
                                "sales_person": "${data.sales_person}",
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "alt_contact_name": "${data.alt_contact_name}",
                                "alt_contact_phone": "${data.alt_contact_phone}",
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
            "title": "Installation Location",
            "data": {
                "installation_type": {
                    "type": "string",
                    "__example__": "residential"
                },
                "order_number": {
                    "type": "string",
                    "__example__": "HAN-12345"
                },
                "branch": {
                    "type": "string",
                    "__example__": "Harare"
                },
                "sales_person": {
                    "type": "string",
                    "__example__": "John Smith"
                },
                "full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "alt_contact_name": {
                    "type": "string",
                    "__example__": "John Doe"
                },
                "alt_contact_phone": {
                    "type": "string",
                    "__example__": "+263779876543"
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
                        "helper-text": "Provide complete address with street, suburb, and city"
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
                                "installation_type": "${data.installation_type}",
                                "order_number": "${data.order_number}",
                                "branch": "${data.branch}",
                                "sales_person": "${data.sales_person}",
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "alt_contact_name": "${data.alt_contact_name}",
                                "alt_contact_phone": "${data.alt_contact_phone}",
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
SOLAR_INSTALLATION_FLOW_METADATA = {
    "name": "solar_installation_whatsapp",
    "friendly_name": "Solar Installation Request (Interactive)",
    "description": "Interactive WhatsApp flow for scheduling solar installations",
    "trigger_keywords": [],  # This flow is typically triggered from other flows or menu
    "is_active": True
}
