# whatsappcrm_backend/flows/definitions/service_booking_flow.py
"""
WhatsApp Flow JSON definition for Service Booking.
This flow collects service booking information including date selection.

Note: In Meta's WhatsApp Flow specification:
1. Each screen must declare all data variables it receives and passes
2. The 'complete' action's payload sends collected data back to the backend
   for processing (this is how the form data is captured)
"""

SERVICE_BOOKING_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "SERVICE_WELCOME",
            "title": "Book a Service",
            "data": {
                "service_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "service_contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "service_description": {
                    "type": "string",
                    "__example__": "Vehicle service"
                },
                "service_preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "service_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Book a Service"
                    },
                    {
                        "type": "TextBody",
                        "text": "Let's schedule a service appointment. We'll just need a few details from you."
                    },
                    {
                        "type": "Footer",
                        "label": "Get Started",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "CUSTOMER_DETAILS"
                            },
                            "payload": {
                                "service_full_name": "",
                                "service_contact_phone": "",
                                "service_description": "",
                                "service_preferred_date": "",
                                "service_address": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "CUSTOMER_DETAILS",
            "title": "Your Details",
            "data": {
                "service_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "service_contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "service_description": {
                    "type": "string",
                    "__example__": "Vehicle service"
                },
                "service_preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "service_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Your Information"
                    },
                    {
                        "type": "TextInput",
                        "name": "service_full_name",
                        "label": "Full Name",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter your full name"
                    },
                    {
                        "type": "TextInput",
                        "name": "service_contact_phone",
                        "label": "Contact Phone Number",
                        "required": True,
                        "input-type": "phone",
                        "helper-text": "e.g., +263771234567"
                    },
                    {
                        "type": "Footer",
                        "label": "Next",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "SERVICE_DETAILS"
                            },
                            "payload": {
                                "service_full_name": "${form.service_full_name}",
                                "service_contact_phone": "${form.service_contact_phone}",
                                "service_description": "${data.service_description}",
                                "service_preferred_date": "${data.service_preferred_date}",
                                "service_address": "${data.service_address}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "SERVICE_DETAILS",
            "title": "Service Details",
            "data": {
                "service_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "service_contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "service_description": {
                    "type": "string",
                    "__example__": "Vehicle service"
                },
                "service_preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "service_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Service Information"
                    },
                    {
                        "type": "TextInput",
                        "name": "service_description",
                        "label": "Briefly describe the service you need",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Describe the service you require"
                    },
                    {
                        "type": "DatePicker",
                        "name": "service_preferred_date",
                        "label": "Preferred Service Date",
                        "required": True
                    },
                    {
                        "type": "Footer",
                        "label": "Next",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "LOCATION_DETAILS"
                            },
                            "payload": {
                                "service_full_name": "${data.service_full_name}",
                                "service_contact_phone": "${data.service_contact_phone}",
                                "service_description": "${form.service_description}",
                                "service_preferred_date": "${form.service_preferred_date}",
                                "service_address": "${data.service_address}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "LOCATION_DETAILS",
            "title": "Service Location",
            "data": {
                "service_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "service_contact_phone": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "service_description": {
                    "type": "string",
                    "__example__": "Vehicle service"
                },
                "service_preferred_date": {
                    "type": "string",
                    "__example__": "2025-12-25"
                },
                "service_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Service Location"
                    },
                    {
                        "type": "TextInput",
                        "name": "service_address",
                        "label": "Service Address",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Please provide the full address for the service"
                    },
                    {
                        "type": "Footer",
                        "label": "Submit Booking",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "service_full_name": "${data.service_full_name}",
                                "service_contact_phone": "${data.service_contact_phone}",
                                "service_description": "${data.service_description}",
                                "service_preferred_date": "${data.service_preferred_date}",
                                "service_address": "${form.service_address}"
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

SERVICE_BOOKING_FLOW_METADATA = {
    "name": "service_booking_whatsapp",
    "friendly_name": "Service Booking Flow",
    "description": "A generic flow for booking a service appointment, including date selection.",
    "trigger_keywords": ["book service", "schedule appointment"],
    "is_active": True
}
