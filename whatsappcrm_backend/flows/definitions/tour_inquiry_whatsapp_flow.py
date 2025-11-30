# whatsappcrm_backend/flows/definitions/tour_inquiry_whatsapp_flow.py

WHATSAPP_FLOW_TOUR_INQUIRY = {
    "name": "tour_inquiry_whatsapp_flow",
    # ...existing fields...
    TOUR_INQUIRY_WHATSAPP_FLOW_METADATA = {
        "name": "tour_inquiry_whatsapp_flow",
        "friendly_name": "Tour Inquiry WhatsApp Flow",
        "description": "Interactive WhatsApp flow for tour inquiries.",
        "trigger_keywords": ["tour inquiry", "safari inquiry"],
        "is_active": True
    }
    "version": "7.3",
    "screens": [
        {
            "id": "TOUR_INQUIRY",
            "title": "Tour Inquiry",
            "data": {
                "destinations": {"type": "string", "__example__": "Maasai Mara, Serengeti"},
                "preferred_dates": {"type": "string", "__example__": "Mid-August 2024"},
                "number_of_travelers": {"type": "string", "__example__": "2"},
                "notes": {"type": "string", "__example__": "Interested in photography, specific lodges, etc."}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {"type": "TextHeading", "text": "Welcome to Kali Safaris! 🦒"},
                    {"type": "TextBody", "text": "Please tell us a bit about your desired trip so we can help you plan the perfect safari adventure."},
                    {"type": "TextInput", "label": "Destinations of Interest", "name": "destinations", "required": True, "placeholder": "e.g., Maasai Mara, Serengeti, Victoria Falls"},
                    {"type": "TextInput", "label": "Preferred Travel Dates", "name": "preferred_dates", "required": True, "placeholder": "e.g., Mid-August 2024"},
                    {"type": "Dropdown", "label": "Number of Travelers", "name": "number_of_travelers", "required": True, "data-source": [
                        {"id": "1", "title": "1 traveler"},
                        {"id": "2", "title": "2 travelers"},
                        {"id": "3", "title": "3 travelers"},
                        {"id": "4", "title": "4 travelers"},
                        {"id": "5", "title": "5 travelers"},
                        {"id": "6+", "title": "6 or more travelers"}
                    ]},
                    {"type": "TextArea", "label": "Additional Notes", "name": "notes", "required": False, "placeholder": "e.g., interested in photography, specific lodges, any special requirements..."},
                    {"type": "Footer", "label": "Submit Inquiry", "on-click-action": {"name": "complete", "payload": {
                        "destinations": "${form.destinations}",
                        "preferred_dates": "${form.preferred_dates}",
                        "number_of_travelers": "${form.number_of_travelers}",
                        "notes": "${form.notes}"
                    }}}
                ]
            }
        }
    ]
}
