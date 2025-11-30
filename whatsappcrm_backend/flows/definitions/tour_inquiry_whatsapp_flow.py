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
                "type": "column",
                "children": [
                    {"type": "text", "text": "Let's plan your dream safari adventure!"},
                    {"type": "text", "text": "We'll ask a few quick questions to help us tailor your experience."},
                    {"type": "button", "label": "Start Inquiry", "on-click-action": {"name": "navigate", "next": {"type": "screen", "name": "DESTINATIONS"}}}
                ]
            }
        },
        {
            "id": "DESTINATIONS",
            "title": "Destinations of Interest",
            "data": {
                "destinations": {"type": "string", "__example__": "Maasai Mara, Serengeti"}
            },
            "layout": {
                "type": "column",
                "children": [
                    {"type": "text", "text": "Which destinations would you like to visit? (e.g., Maasai Mara, Serengeti, Victoria Falls)"},
                    {"type": "input", "input_type": "text", "label": "Destinations", "name": "destinations", "required": True},
                    {"type": "button", "label": "Next", "on-click-action": {"name": "navigate", "next": {"type": "screen", "name": "DATES"}}}
                ]
            }
        },
        {
            "id": "DATES",
            "title": "Preferred Travel Dates",
            "data": {
                "preferred_dates": {"type": "string", "__example__": "Mid-August 2024"}
            },
            "layout": {
                "type": "column",
                "children": [
                    {"type": "text", "text": "When would you like to travel? (e.g., Mid-August 2024)"},
                    {"type": "input", "input_type": "text", "label": "Travel Dates", "name": "preferred_dates", "required": True},
                    {"type": "button", "label": "Next", "on-click-action": {"name": "navigate", "next": {"type": "screen", "name": "TRAVELERS"}}}
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
                "type": "column",
                "children": [
                    {"type": "text", "text": "How many people are traveling?"},
                    {"type": "input", "input_type": "select", "label": "Travelers", "name": "number_of_travelers", "required": True, "options": [
                        {"id": "1", "title": "1 traveler"},
                        {"id": "2", "title": "2 travelers"},
                        {"id": "3", "title": "3 travelers"},
                        {"id": "4", "title": "4 travelers"},
                        {"id": "5", "title": "5 travelers"},
                        {"id": "6+", "title": "6 or more travelers"}
                    ]},
                    {"type": "button", "label": "Next", "onClickAction": {"name": "navigate", "next": {"type": "screen", "name": "NOTES"}}}
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
                "type": "column",
                "children": [
                    {"type": "text", "text": "Any special requests or notes? (Optional)"},
                    {"type": "input", "input_type": "textarea", "label": "Notes", "name": "notes", "required": False},
                    {"type": "button", "label": "Review & Submit", "onClickAction": {"name": "navigate", "next": {"type": "screen", "name": "REVIEW"}}}
                ]
            }
        },
        {
            "id": "REVIEW",
            "title": "Review Your Inquiry",
            "layout": {
                "type": "column",
                "children": [
                    {"type": "text", "text": "Please review your details below. If everything looks good, submit your inquiry!"},
                    {"type": "text", "text": "Destinations: ${form.destinations}"},
                    {"type": "text", "text": "Travel Dates: ${form.preferred_dates}"},
                    {"type": "text", "text": "Travelers: ${form.number_of_travelers}"},
                    {"type": "text", "text": "Notes: ${form.notes}"},
                    {"type": "button", "label": "Submit Inquiry", "onClickAction": {"name": "data_exchange", "payload": {
                        "destinations": "${form.destinations}",
                        "preferred_dates": "${form.preferred_dates}",
                        "number_of_travelers": "${form.number_of_travelers}",
                        "notes": "${form.notes}"
                    }}},
                    {"type": "button", "label": "Back", "onClickAction": {"name": "navigate", "next": {"type": "screen", "name": "NOTES"}}}
                ]
            }
        },
        {
            "id": "THANK_YOU",
            "title": "Thank You!",
            "layout": {
                "type": "column",
                "children": [
                    {"type": "text", "text": "Your inquiry has been submitted."},
                    {"type": "text", "text": "A Kali Safaris expert will contact you soon to help plan your adventure."}
                ]
            }
        }
    ]
}


