# whatsappcrm_backend/flows/definitions/tour_inquiry_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Tour Inquiry.
This is a production-ready interactive flow for collecting safari tour inquiries.

Note: In Meta's WhatsApp Flow specification, each screen must declare all data variables
it will receive and pass. The data schema is intentionally repeated across screens
as this is required by the WhatsApp Flows API for proper data binding.
"""

TOUR_INQUIRY_WHATSAPP_FLOW_METADATA = {
    "name": "tour_inquiry_whatsapp",
    "friendly_name": "Tour Inquiry WhatsApp Flow",
    "description": "A robust, production-ready WhatsApp interactive flow for collecting detailed safari tour inquiries from users, including destinations, dates, group size, and special requests.",
    "trigger_keywords": ["tour inquiry", "safari inquiry", "book safari", "plan trip"],
    "is_active": True
}

TOUR_INQUIRY_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "WELCOME",
            "title": "Welcome to Kali Safaris!",
            "data": {
                "destinations": {
                    "type": "string",
                    "__example__": "Maasai Mara, Serengeti"
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2024-08-15"
                },
                "number_of_travelers": {
                    "type": "string",
                    "__example__": "2"
                },
                "notes": {
                    "type": "string",
                    "__example__": "Interested in photography"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Plan Your Safari Adventure"
                    },
                    {
                        "type": "TextBody",
                        "text": "Let's plan your dream safari adventure! We'll ask a few quick questions to help us tailor your experience."
                    },
                    {
                        "type": "Footer",
                        "label": "Start Inquiry",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "DESTINATIONS"
                            },
                            "payload": {
                                "destinations": "",
                                "preferred_date": "",
                                "number_of_travelers": "",
                                "notes": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "DESTINATIONS",
            "title": "Choose Destinations",
            "data": {
                "destinations": {
                    "type": "string",
                    "__example__": "Maasai Mara, Serengeti"
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2024-08-15"
                },
                "number_of_travelers": {
                    "type": "string",
                    "__example__": "2"
                },
                "notes": {
                    "type": "string",
                    "__example__": "Interested in photography"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Destinations"
                    },
                    {
                        "type": "TextBody",
                        "text": "Which destinations would you like to visit? (e.g., Maasai Mara, Serengeti, Victoria Falls)"
                    },
                    {
                        "type": "TextInput",
                        "name": "destinations",
                        "label": "Destinations",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter the destinations you'd like to visit"
                    },
                    {
                        "type": "Footer",
                        "label": "Next",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "DATES"
                            },
                            "payload": {
                                "destinations": "${form.destinations}",
                                "preferred_date": "${data.preferred_date}",
                                "number_of_travelers": "${data.number_of_travelers}",
                                "notes": "${data.notes}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "DATES",
            "title": "Preferred Travel Date",
            "data": {
                "destinations": {
                    "type": "string",
                    "__example__": "Maasai Mara, Serengeti"
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2024-08-15"
                },
                "number_of_travelers": {
                    "type": "string",
                    "__example__": "2"
                },
                "notes": {
                    "type": "string",
                    "__example__": "Interested in photography"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Travel Date"
                    },
                    {
                        "type": "TextBody",
                        "text": "When would you like to travel?"
                    },
                    {
                        "type": "DatePicker",
                        "name": "preferred_date",
                        "label": "Preferred Travel Date",
                        "required": True
                    },
                    {
                        "type": "Footer",
                        "label": "Next",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "TRAVELERS"
                            },
                            "payload": {
                                "destinations": "${data.destinations}",
                                "preferred_date": "${form.preferred_date}",
                                "number_of_travelers": "${data.number_of_travelers}",
                                "notes": "${data.notes}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "TRAVELERS",
            "title": "Number of Travelers",
            "data": {
                "destinations": {
                    "type": "string",
                    "__example__": "Maasai Mara, Serengeti"
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2024-08-15"
                },
                "number_of_travelers": {
                    "type": "string",
                    "__example__": "2"
                },
                "notes": {
                    "type": "string",
                    "__example__": "Interested in photography"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Group Size"
                    },
                    {
                        "type": "TextBody",
                        "text": "How many people are traveling?"
                    },
                    {
                        "type": "Dropdown",
                        "name": "number_of_travelers",
                        "label": "Number of Travelers",
                        "required": True,
                        "data-source": [
                            {"id": "1", "title": "1 traveler"},
                            {"id": "2", "title": "2 travelers"},
                            {"id": "3", "title": "3 travelers"},
                            {"id": "4", "title": "4 travelers"},
                            {"id": "5", "title": "5 travelers"},
                            {"id": "6+", "title": "6 or more travelers"}
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Next",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "NOTES"
                            },
                            "payload": {
                                "destinations": "${data.destinations}",
                                "preferred_date": "${data.preferred_date}",
                                "number_of_travelers": "${form.number_of_travelers}",
                                "notes": "${data.notes}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "NOTES",
            "title": "Additional Notes",
            "data": {
                "destinations": {
                    "type": "string",
                    "__example__": "Maasai Mara, Serengeti"
                },
                "preferred_date": {
                    "type": "string",
                    "__example__": "2024-08-15"
                },
                "number_of_travelers": {
                    "type": "string",
                    "__example__": "2"
                },
                "notes": {
                    "type": "string",
                    "__example__": "Interested in photography"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Special Requests"
                    },
                    {
                        "type": "TextBody",
                        "text": "Any special requests or notes? (Optional)"
                    },
                    {
                        "type": "TextInput",
                        "name": "notes",
                        "label": "Notes",
                        "required": False,
                        "input-type": "text",
                        "helper-text": "E.g., photography interests, specific lodges, dietary requirements"
                    },
                    {
                        "type": "Footer",
                        "label": "Submit Inquiry",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "destinations": "${data.destinations}",
                                "preferred_date": "${data.preferred_date}",
                                "number_of_travelers": "${data.number_of_travelers}",
                                "notes": "${form.notes}"
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
