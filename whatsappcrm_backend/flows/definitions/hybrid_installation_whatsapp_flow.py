# whatsappcrm_backend/flows/definitions/hybrid_installation_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Hybrid Installation Request (Starlink + Solar).
"""

HYBRID_INSTALLATION_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "WELCOME",
            "title": "Hybrid Installation",
            "data": {
                "order_number": {"type": "string", "__example__": "ORD-12345"},
                "branch": {"type": "string", "__example__": "Harare"},
                "sales_person": {"type": "string", "__example__": "John Doe"},
                "full_name": {"type": "string", "__example__": "Jane Doe"},
                "contact_phone": {"type": "string", "__example__": "+263771234567"},
                "alt_contact_name": {"type": "string", "__example__": "N/A"},
                "alt_contact_phone": {"type": "string", "__example__": "N/A"},
                "preferred_date": {"type": "string", "__example__": "2025-12-25"},
                "availability": {"type": "string", "__example__": "morning"},
                "address": {"type": "string", "__example__": "123 Main St"},
                "starlink_kit_type": {"type": "string", "__example__": "standard"},
                "solar_capacity": {"type": "string", "__example__": "5kVA"},
                "mount_location": {"type": "string", "__example__": "roof"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Hybrid Installation Request"
                    },
                    {
                        "type": "TextBody",
                        "text": "Request installation for both Starlink and Solar systems. We'll collect details for both installations."
                    },
                    {
                        "type": "Footer",
                        "label": "Get Started",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {"type": "screen", "name": "ORDER_INFO"},
                            "payload": {
                                "order_number": "", "branch": "", "sales_person": "",
                                "full_name": "", "contact_phone": "", "alt_contact_name": "",
                                "alt_contact_phone": "", "preferred_date": "", "availability": "",
                                "address": "", "starlink_kit_type": "", "solar_capacity": "",
                                "mount_location": ""
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
                "order_number": {"type": "string", "__example__": "ORD-12345"},
                "branch": {"type": "string", "__example__": "Harare"},
                "sales_person": {"type": "string", "__example__": "John Doe"},
                "full_name": {"type": "string", "__example__": "Jane Doe"},
                "contact_phone": {"type": "string", "__example__": "+263771234567"},
                "alt_contact_name": {"type": "string", "__example__": "N/A"},
                "alt_contact_phone": {"type": "string", "__example__": "N/A"},
                "preferred_date": {"type": "string", "__example__": "2025-12-25"},
                "availability": {"type": "string", "__example__": "morning"},
                "address": {"type": "string", "__example__": "123 Main St"},
                "starlink_kit_type": {"type": "string", "__example__": "standard"},
                "solar_capacity": {"type": "string", "__example__": "5kVA"},
                "mount_location": {"type": "string", "__example__": "roof"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextInput",
                        "name": "order_number",
                        "label": "Order Number (if applicable)",
                        "input-type": "text",
                        "required": False,
                        "helper-text": "Enter your order number or leave blank"
                    },
                    {
                        "type": "TextInput",
                        "name": "branch",
                        "label": "Branch",
                        "input-type": "text",
                        "required": True
                    },
                    {
                        "type": "TextInput",
                        "name": "sales_person",
                        "label": "Sales Person Name",
                        "input-type": "text",
                        "required": True
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {"type": "screen", "name": "CONTACT_INFO"},
                            "payload": {
                                "order_number": "${data.order_number}",
                                "branch": "${data.branch}",
                                "sales_person": "${data.sales_person}",
                                   "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "alt_contact_name": "${data.alt_contact_name}",
                                "alt_contact_phone": "${data.alt_contact_phone}",
                                "preferred_date": "${data.preferred_date}",
                                "availability": "${data.availability}",
                                "address": "${data.address}",
                                "starlink_kit_type": "${data.starlink_kit_type}",
                                "solar_capacity": "${data.solar_capacity}",
                                "mount_location": "${data.mount_location}"
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
                "order_number": {"type": "string", "__example__": "ORD-12345"},
                "branch": {"type": "string", "__example__": "Harare"},
                "sales_person": {"type": "string", "__example__": "John Doe"},
                "full_name": {"type": "string", "__example__": "Jane Doe"},
                "contact_phone": {"type": "string", "__example__": "+263771234567"},
                "alt_contact_name": {"type": "string", "__example__": "N/A"},
                "alt_contact_phone": {"type": "string", "__example__": "N/A"},
                "preferred_date": {"type": "string", "__example__": "2025-12-25"},
                "availability": {"type": "string", "__example__": "morning"},
                "address": {"type": "string", "__example__": "123 Main St"},
                "starlink_kit_type": {"type": "string", "__example__": "standard"},
                "solar_capacity": {"type": "string", "__example__": "5kVA"},
                "mount_location": {"type": "string", "__example__": "roof"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextInput",
                        "name": "full_name",
                        "label": "Full Name",
                        "input-type": "text",
                        "required": True
                    },
                    {
                        "type": "TextInput",
                        "name": "contact_phone",
                        "label": "Contact Phone Number",
                        "input-type": "phone",
                        "required": True
                    },
                    {
                        "type": "TextInput",
                        "name": "alt_contact_name",
                        "label": "Alternative Contact Name",
                        "input-type": "text",
                        "required": False,
                        "helper-text": "Enter alternative contact or N/A"
                    },
                    {
                        "type": "TextInput",
                        "name": "alt_contact_phone",
                        "label": "Alternative Contact Number",
                        "input-type": "phone",
                        "required": False,
                        "helper-text": "Enter alternative number or N/A"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {"type": "screen", "name": "INSTALLATION_DETAILS"},
                            "payload": {
                                   "order_number": "${data.order_number}",
                                "branch": "${data.branch}",
                                "sales_person": "${data.sales_person}",
                                   "full_name": "${data.full_name}",
                                   "contact_phone": "${data.contact_phone}",
                                "alt_contact_name": "${data.alt_contact_name}",
                                "alt_contact_phone": "${data.alt_contact_phone}",
                                   "preferred_date": "${data.preferred_date}",
                                "availability": "${data.availability}",
                                "address": "${data.address}",
                                "starlink_kit_type": "${data.starlink_kit_type}",
                                "solar_capacity": "${data.solar_capacity}",
                                "mount_location": "${data.mount_location}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "INSTALLATION_DETAILS",
            "title": "Installation Details",
            "data": {
                "order_number": {"type": "string", "__example__": "ORD-12345"},
                "branch": {"type": "string", "__example__": "Harare"},
                "sales_person": {"type": "string", "__example__": "John Doe"},
                "full_name": {"type": "string", "__example__": "Jane Doe"},
                "contact_phone": {"type": "string", "__example__": "+263771234567"},
                "alt_contact_name": {"type": "string", "__example__": "N/A"},
                "alt_contact_phone": {"type": "string", "__example__": "N/A"},
                "preferred_date": {"type": "string", "__example__": "2025-12-25"},
                "availability": {"type": "string", "__example__": "morning"},
                "address": {"type": "string", "__example__": "123 Main St"},
                "starlink_kit_type": {"type": "string", "__example__": "standard"},
                "solar_capacity": {"type": "string", "__example__": "5kVA"},
                "mount_location": {"type": "string", "__example__": "roof"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "System Details"
                    },
                    {
                        "type": "Dropdown",
                        "name": "starlink_kit_type",
                        "label": "Starlink Kit Type",
                        "required": True,
                        "data-source": [
                            {"id": "standard", "title": "Standard Kit"},
                            {"id": "high_performance", "title": "High Performance"},
                            {"id": "roam", "title": "Roam Kit"}
                        ]
                    },
                    {
                        "type": "TextInput",
                        "name": "solar_capacity",
                        "label": "Solar System Capacity (e.g., 5kVA, 10kVA)",
                        "input-type": "text",
                        "required": True
                    },
                    {
                        "type": "TextInput",
                        "name": "mount_location",
                        "label": "Preferred Mount Location",
                        "input-type": "text",
                        "required": True,
                        "helper-text": "e.g., Roof, Wall, Ground"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {"type": "screen", "name": "SCHEDULE_INFO"},
                            "payload": {
                                   "order_number": "${data.order_number}",
                                "branch": "${data.branch}",
                                "sales_person": "${data.sales_person}",
                                   "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "alt_contact_name": "${data.alt_contact_name}",
                                "alt_contact_phone": "${data.alt_contact_phone}",
                                   "preferred_date": "${data.preferred_date}",
                                "availability": "${data.availability}",
                                "address": "${data.address}",
                                   "starlink_kit_type": "${data.starlink_kit_type}",
                                   "solar_capacity": "${data.solar_capacity}",
                                   "mount_location": "${data.mount_location}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "SCHEDULE_INFO",
            "title": "Schedule & Location",
            "data": {
                "order_number": {"type": "string", "__example__": "ORD-12345"},
                "branch": {"type": "string", "__example__": "Harare"},
                "sales_person": {"type": "string", "__example__": "John Doe"},
                "full_name": {"type": "string", "__example__": "Jane Doe"},
                "contact_phone": {"type": "string", "__example__": "+263771234567"},
                "alt_contact_name": {"type": "string", "__example__": "N/A"},
                "alt_contact_phone": {"type": "string", "__example__": "N/A"},
                "preferred_date": {"type": "string", "__example__": "2025-12-25"},
                "availability": {"type": "string", "__example__": "morning"},
                "address": {"type": "string", "__example__": "123 Main St"},
                "starlink_kit_type": {"type": "string", "__example__": "standard"},
                "solar_capacity": {"type": "string", "__example__": "5kVA"},
                "mount_location": {"type": "string", "__example__": "roof"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "DatePicker",
                        "name": "preferred_date",
                        "label": "Preferred Installation Date",
                        "required": True
                    },
                    {
                        "type": "Dropdown",
                        "name": "availability",
                        "label": "Preferred Time",
                        "required": True,
                        "data-source": [
                            {"id": "morning", "title": "Morning (8AM - 12PM)"},
                            {"id": "afternoon", "title": "Afternoon (12PM - 5PM)"}
                        ]
                    },
                    {
                        "type": "TextArea",
                        "name": "address",
                        "label": "Installation Address",
                        "required": True,
                        "helper-text": "Full physical address"
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
                                   "order_number": "${data.order_number}",
                                "branch": "${data.branch}",
                                "sales_person": "${data.sales_person}",
                                "full_name": "${data.full_name}",
                                "contact_phone": "${data.contact_phone}",
                                "alt_contact_name": "${data.alt_contact_name}",
                                "alt_contact_phone": "${data.alt_contact_phone}",
                                   "preferred_date": "${data.preferred_date}",
                                "availability": "${data.availability}",
                                "address": "${data.address}",
                                   "starlink_kit_type": "${data.starlink_kit_type}",
                                "solar_capacity": "${data.solar_capacity}",
                                "mount_location": "${data.mount_location}"
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

# Metadata for sync_whatsapp_flows command
HYBRID_INSTALLATION_FLOW_METADATA = {
    "name": "hybrid_installation_whatsapp",
    "friendly_name": "Hybrid Installation Request (Interactive)",
    "description": "Interactive WhatsApp flow for scheduling hybrid Starlink+Solar installations",
    "trigger_keywords": ["hybrid installation", "starlink solar", "combo installation"],
    "is_active": True
}
