# whatsappcrm_backend/flows/definitions/tour_inquiry_whatsapp_flow.py

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
            "title": "Welcome to Kali Safaris! 🦒",
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {"type": "TextBody", "text": ["Let's plan your dream safari adventure!"]},
                    {"type": "TextBody", "text": ["We'll ask a few quick questions to help us tailor your experience."]},
                    {"type": "Button", "label": "Start Inquiry", "on-click-action": {"name": "navigate", "next": {"type": "screen", "name": "DESTINATIONS"}}}
                ]
            }
        },
        {
            "id": "DESTINATIONS",
            "title": "Choose Destinations",
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {"type": "TextBody", "text": ["Which destinations would you like to visit? (e.g., Maasai Mara, Serengeti, Victoria Falls)"]},
                    {"type": "TextInput", "label": "Destinations", "name": "destinations", "required": True},
                    {"type": "Button", "label": "Next", "on-click-action": {"name": "navigate", "next": {"type": "screen", "name": "DATES"}}}
                ]
            }
        },
        {
            "id": "DATES",
            "title": "Preferred Travel Date",
            "data": {
                "preferred_date": {"type": "string", "__example__": "2024-08-15"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {"type": "TextBody", "text": ["When would you like to travel? (Pick a single date)"]},
                    {"type": "DatePicker", "label": "Preferred Travel Date", "name": "preferred_date", "required": True},
                    {"type": "Button", "label": "Next", "on-click-action": {"name": "navigate", "next": {"type": "screen", "name": "TRAVELERS"}}}
                ]
            }
        },
        {
            "id": "TRAVELERS",
            "title": "Number of Travelers",
            "data": {
                "number_of_travelers": {"type": "string", "__example__": "2"}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {"type": "TextBody", "text": ["How many people are traveling?"]},
                    {"type": "Dropdown", "label": "Travelers", "name": "number_of_travelers", "required": True, "data-source": [
                        {"id": "1", "title": "1 traveler"},
                        {"id": "2", "title": "2 travelers"},
                        {"id": "3", "title": "3 travelers"},
                        {"id": "4", "title": "4 travelers"},
                        {"id": "5", "title": "5 travelers"},
                        {"id": "6+", "title": "6 or more travelers"}
                    ]},
                    {"type": "Button", "label": "Next", "on-click-action": {"name": "navigate", "next": {"type": "screen", "name": "NOTES"}}}
                ]
            }
        },
        {
            "id": "NOTES",
            "title": "Additional Notes",
            "data": {
                "notes": {"type": "string", "__example__": "Interested in photography, specific lodges, etc."}
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {"type": "TextBody", "text": ["Any special requests or notes? (Optional)"]},
                    {"type": "TextInput", "label": "Notes", "name": "notes", "required": False, "multiline": True},
                    {"type": "Button", "label": "Review & Submit", "on-click-action": {"name": "navigate", "next": {"type": "screen", "name": "REVIEW"}}}
                ]
            }
        },
        {
            "id": "REVIEW",
            "title": "Review Your Inquiry",
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {"type": "TextBody", "text": ["Please review your details below. If everything looks good, submit your inquiry!"]},
                    {"type": "TextBody", "text": ["Destinations: ${form.destinations}"]},
                    {"type": "TextBody", "text": ["Travel Date: ${form.preferred_date}"]},
                    {"type": "TextBody", "text": ["Travelers: ${form.number_of_travelers}"]},
                    {"type": "TextBody", "text": ["Notes: ${form.notes}"]},
                    {"type": "Button", "label": "Submit Inquiry", "on-click-action": {"name": "data_exchange", "payload": {
                        "destinations": "${form.destinations}",
                        "preferred_date": "${form.preferred_date}",
                        "number_of_travelers": "${form.number_of_travelers}",
                        "notes": "${form.notes}"
                    }}},
                    {"type": "Button", "label": "Back", "on-click-action": {"name": "navigate", "next": {"type": "screen", "name": "NOTES"}}}
                ]
            }
        },
        {
            "id": "THANK_YOU",
            "title": "Thank You!",
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {"type": "TextBody", "text": ["Your inquiry has been submitted."]},
                    {"type": "TextBody", "text": ["A Kali Safaris expert will contact you soon to help plan your adventure."]}
                ]
            }
        }
    ]
}


