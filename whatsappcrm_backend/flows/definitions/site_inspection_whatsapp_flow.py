# whatsappcrm_backend/flows/definitions/site_inspection_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Site Assessment/Inspection Request.
This now includes assessment_type selection via dropdown to align with legacy message flow.
"""

SITE_INSPECTION_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "WELCOME",
            "title": "Site Assessment",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "assessment_type": {
                    "type": "string",
                    "__example__": "starlink"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Site Assessment Request"
                    },
                    {
                        "type": "TextBody",
                        "text": "Let's schedule a site assessment. First, select what type of assessment you need."
                    },
                    {
                        "type": "Footer",
                        "label": "Get Started",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "ASSESSMENT_TYPE"
                            },
                            "payload": {
                                "assessment_full_name": "",
                                "assessment_preferred_day": "",
                                "assessment_company_name": "",
                                "assessment_address": "",
                                "assessment_contact_info": "",
                                "assessment_type": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "ASSESSMENT_TYPE",
            "title": "Assessment Type",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "assessment_type": {
                    "type": "string",
                    "__example__": "starlink"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "What type of assessment do you need?"
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "assessment_type",
                        "label": "Assessment Type",
                        "required": True,
                        "data-source": [
                            {
                                "id": "starlink",
                                "title": "Starlink Installation"
                            },
                            {
                                "id": "commercial_solar",
                                "title": "Commercial Solar System"
                            },
                            {
                                "id": "hybrid_starlink_solar",
                                "title": "Hybrid (Starlink + Solar)"
                            },
                            {
                                "id": "custom_furniture",
                                "title": "Custom Furniture"
                            },
                            {
                                "id": "other",
                                "title": "Other"
                            }
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "PERSONAL_INFO"
                            },
                            "payload": {
                                "assessment_full_name": "${data.assessment_full_name}",
                                "assessment_preferred_day": "${data.assessment_preferred_day}",
                                "assessment_company_name": "${data.assessment_company_name}",
                                "assessment_address": "${data.assessment_address}",
                                "assessment_contact_info": "${data.assessment_contact_info}",
                                "assessment_type": "${form.assessment_type}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "PERSONAL_INFO",
            "title": "Your Information",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "assessment_type": {
                    "type": "string",
                    "__example__": "commercial_solar"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Personal Details"
                    },
                    {
                        "type": "TextInput",
                        "name": "assessment_full_name",
                        "label": "Full Name",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter your full name"
                    },
                    {
                        "type": "DatePicker",
                        "name": "assessment_preferred_day",
                        "label": "Preferred Assessment Date",
                        "required": True
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "COMPANY_INFO"
                            },
                            "payload": {
                                "assessment_full_name": "${form.assessment_full_name}",
                                "assessment_preferred_day": "${form.assessment_preferred_day}",
                                "assessment_company_name": "${data.assessment_company_name}",
                                "assessment_address": "${data.assessment_address}",
                                "assessment_contact_info": "${data.assessment_contact_info}",
                                "assessment_type": "${data.assessment_type}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "COMPANY_INFO",
            "title": "Company Information",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "assessment_type": {
                    "type": "string",
                    "__example__": "hybrid_starlink_solar"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Company Details"
                    },
                    {
                        "type": "TextInput",
                        "name": "assessment_company_name",
                        "label": "Company Name",
                        "required": False,
                        "input-type": "text",
                        "helper-text": "Enter N/A if not applicable"
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
                                "assessment_full_name": "${data.assessment_full_name}",
                                "assessment_preferred_day": "${data.assessment_preferred_day}",
                                "assessment_company_name": "${form.assessment_company_name}",
                                "assessment_address": "${data.assessment_address}",
                                "assessment_contact_info": "${data.assessment_contact_info}",
                                "assessment_type": "${data.assessment_type}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "LOCATION_INFO",
            "title": "Location Details",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "assessment_type": {
                    "type": "string",
                    "__example__": "custom_furniture"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Site Address"
                    },
                    {
                        "type": "TextInput",
                        "name": "assessment_address",
                        "label": "Full Site Address",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Provide the complete address for the assessment"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "CONTACT_INFO"
                            },
                            "payload": {
                                "assessment_full_name": "${data.assessment_full_name}",
                                "assessment_preferred_day": "${data.assessment_preferred_day}",
                                "assessment_company_name": "${data.assessment_company_name}",
                                "assessment_address": "${form.assessment_address}",
                                "assessment_contact_info": "${data.assessment_contact_info}",
                                "assessment_type": "${data.assessment_type}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "CONTACT_INFO",
            "title": "Contact Information",
            "data": {
                "assessment_full_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "assessment_preferred_day": {
                    "type": "string",
                    "__example__": "Monday, December 25th"
                },
                "assessment_company_name": {
                    "type": "string",
                    "__example__": "ABC Company"
                },
                "assessment_address": {
                    "type": "string",
                    "__example__": "123 Main Street, Harare"
                },
                "assessment_contact_info": {
                    "type": "string",
                    "__example__": "+263771234567"
                },
                "assessment_type": {
                    "type": "string",
                    "__example__": "starlink"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Contact Number"
                    },
                    {
                        "type": "TextInput",
                        "name": "assessment_contact_info",
                        "label": "Best Contact Number",
                        "required": True,
                        "input-type": "phone",
                        "helper-text": "e.g., +263771234567"
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
                                "assessment_full_name": "${data.assessment_full_name}",
                                "assessment_preferred_day": "${data.assessment_preferred_day}",
                                "assessment_company_name": "${data.assessment_company_name}",
                                "assessment_address": "${data.assessment_address}",
                                "assessment_contact_info": "${form.assessment_contact_info}",
                                "assessment_type": "${data.assessment_type}"
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
SITE_INSPECTION_FLOW_METADATA = {
    "name": "site_inspection_whatsapp",
    "friendly_name": "Site Assessment Request (Interactive)",
    "description": "Interactive WhatsApp flow for requesting site assessments (with type selection)",
    "trigger_keywords": ["site assessment", "assessment", "book assessment", "site inspection"],
    "is_active": True
}
