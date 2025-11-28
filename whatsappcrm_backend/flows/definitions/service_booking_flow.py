# whatsappcrm_backend/flows/definitions/service_booking_flow.py
"""
Flow Definition for a generic Service Booking.
This flow demonstrates the use of a DatePicker.
"""

SERVICE_BOOKING_FLOW = {
    "version": "3.0",
    "data_api_version": "3.0",
    "routing_model": {
        "service_booking_whatsapp": ["service_booking_confirmation"]
    },
    "screens": [
        {
            "id": "SERVICE_WELCOME",
            "title": "Book a Service Appointment",
            "data": {
                "service_full_name": "",
                "service_contact_phone": "",
                "service_description": "",
                "service_preferred_date": None,
                "service_address": ""
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "🛠️ Book a Service"
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
                            "next": "CUSTOMER_DETAILS"
                        }
                    }
                ]
            }
        },
        {
            "id": "CUSTOMER_DETAILS",
            "title": "Your Details",
            "data": {},
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "Form",
                        "name": "customer_form",
                        "children": [
                            {
                                "type": "TextInput",
                                "label": "Full Name",
                                "name": "service_full_name",
                                "required": True
                            },
                            {
                                "type": "TextInput",
                                "label": "Contact Phone Number",
                                "name": "service_contact_phone",
                                "required": True,
                                "input-type": "phone"
                            }
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Next",
                        "on-click-action": {
                            "name": "navigate",
                            "next": "SERVICE_DETAILS",
                            "payload": {
                                "service_full_name": "${form.customer_form.service_full_name}",
                                "service_contact_phone": "${form.customer_form.service_contact_phone}",
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
            "data": {},
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "Form",
                        "name": "service_form",
                        "children": [
                            {
                                "type": "TextInput",
                                "label": "Briefly describe the service you need",
                                "name": "service_description",
                                "required": True
                            },
                            {
                                "type": "DatePicker",
                                "label": "Preferred Service Date",
                                "name": "service_preferred_date",
                                "required": True,
                                "helper-text": "Select a date for your appointment."
                            }
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Next",
                        "on-click-action": {
                            "name": "navigate",
                            "next": "LOCATION_DETAILS",
                            "payload": {
                                "service_full_name": "${data.service_full_name}",
                                "service_contact_phone": "${data.service_contact_phone}",
                                "service_description": "${form.service_form.service_description}",
                                "service_preferred_date": "${form.service_form.service_preferred_date}",
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
            "data": {},
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "Form",
                        "name": "location_form",
                        "children": [
                            {
                                "type": "TextInput",
                                "label": "Service Address",
                                "name": "service_address",
                                "required": True,
                                "helper-text": "Please provide the full address for the service."
                            }
                        ]
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
                                "service_address": "${form.location_form.service_address}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "service_booking_confirmation",
            "title": "Booking Complete",
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "✅ Appointment Booked!"
                    },
                    {
                        "type": "TextBody",
                        "text": "Thank you, ${data.service_full_name}! Your service appointment has been successfully scheduled."
                    },
                    {
                        "type": "TextSubheading",
                        "text": "*Details:*"
                    },
                    {
                        "type": "TextParagraph",
                        "text": "📅 *Date:* ${data.service_preferred_date}\n📍 *Address:* ${data.service_address}\n📝 *Service:* ${data.service_description}"
                    },
                    {
                        "type": "TextBody",
                        "text": "Our team will contact you at ${data.service_contact_phone} to confirm the details. You can close this window now."
                    }
                ]
            }
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
