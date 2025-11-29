# whatsappcrm_backend/flows/definitions/tour_inquiry_whatsapp_flow.py

WHATSAPP_FLOW_TOUR_INQUIRY = {
    "name": "tour_inquiry_whatsapp",
    "friendly_name": "Tour Inquiry Form",
    "description": "A WhatsApp interactive flow for capturing new tour inquiries from customers.",
    "flow_json": {
        "version": "3.0",
        "routing_model": {
            "GUEST": ["welcome_screen"]
        },
        "screens": [
            {
                "id": "welcome_screen",
                "title": "Tour Inquiry",
                "terminal": False,
                "data": {},
                "layout": {
                    "type": "SingleColumnLayout",
                    "children": [
                        {
                            "type": "TextSubheading",
                            "text": "Welcome to Kali Safaris! 🦒"
                        },
                        {
                            "type": "TextBody",
                            "text": "Please tell us a bit about your desired trip so we can help you plan the perfect safari adventure."
                        },
                        {
                            "type": "TextInput",
                            "label": "Destinations of Interest",
                            "name": "destinations",
                            "required": True,
                            "placeholder": "e.g., Maasai Mara, Serengeti, Victoria Falls"
                        },
                        {
                            "type": "TextInput",
                            "label": "Preferred Travel Dates",
                            "name": "preferred_dates",
                            "required": True,
                            "placeholder": "e.g., Mid-August 2024"
                        },
                        {
                            "type": "Dropdown",
                            "label": "Number of Travelers",
                            "name": "number_of_travelers",
                            "required": True,
                            "data_source": [
                                {"id": "1", "title": "1 traveler"},
                                {"id": "2", "title": "2 travelers"},
                                {"id": "3", "title": "3 travelers"},
                                {"id": "4", "title": "4 travelers"},
                                {"id": "5", "title": "5 travelers"},
                                {"id": "6+", "title": "6 or more travelers"}
                            ]
                        },
                        {
                            "type": "TextArea",
                            "label": "Additional Notes",
                            "name": "notes",
                            "required": False,
                            "placeholder": "e.g., interested in photography, specific lodges, any special requirements..."
                        },
                        {
                            "type": "Footer",
                            "label": "Submit Inquiry",
                            "on_click_action": {
                                "name": "complete",
                                "payload": {}
                            }
                        }
                    ]
                }
            }
        ]
    }
}
