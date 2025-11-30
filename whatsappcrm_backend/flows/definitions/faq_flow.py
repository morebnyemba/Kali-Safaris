# whatsappcrm_backend/flows/definitions/faq_flow.py

FAQ_FLOW = {
    "name": "faq_flow",
    "friendly_name": "Frequently Asked Questions",
    "description": "Provides answers to common questions.",
    "trigger_keywords": ["faq", "questions", "help"],
    "is_active": True,
    "steps": [
        {
            "name": "start_faq",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "FAQ"},
                        "body": {"text": "Please select a question from the list below."},
                        "action": {
                            "button": "Questions",
                            "sections": [{
                                "title": "Common Questions",
                                "rows": [
                                    {"id": "faq_payment", "title": "Payment Options"},
                                    {"id": "faq_cancellation", "title": "Cancellation Policy"},
                                    {"id": "faq_what_to_pack", "title": "What should I pack?"},
                                    {"id": "faq_visa", "title": "Do I need a visa?"},
                                ]
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "faq_choice"}
            },
            "transitions": [
                {"to_step": "answer_payment", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "faq_payment"}},
                {"to_step": "answer_cancellation", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "faq_cancellation"}},
                {"to_step": "answer_what_to_pack", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "faq_what_to_pack"}},
                {"to_step": "answer_visa", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "faq_visa"}},
            ]
        },
        {
            "name": "answer_payment",
            "type": "send_message",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "We accept payments via Bank Transfer, Visa, MasterCard, and mobile money (EcoCash/OneMoney). Payment details will be provided on your invoice."}
                }
            },
            "transitions": [{"to_step": "end_faq", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "answer_cancellation",
            "type": "send_message",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Cancellations made more than 30 days before the tour start date are fully refundable. Cancellations made within 30 days are subject to a 50% fee. Please see our website for the full policy."}
                }
            },
            "transitions": [{"to_step": "end_faq", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "answer_what_to_pack",
            "type": "send_message",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "We recommend packing light, comfortable clothing in neutral colors, a hat, sunscreen, insect repellent, a good pair of walking shoes, and a camera! A warm jacket is also essential for early morning and evening game drives."}
                }
            },
            "transitions": [{"to_step": "end_faq", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "answer_visa",
            "type": "send_message",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Visa requirements vary by nationality. We strongly advise checking with the Zimbabwean embassy or consulate in your country. Many nationalities can obtain a visa upon arrival."}
                }
            },
            "transitions": [{"to_step": "end_faq", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_faq",
            "type": "send_message",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Is there anything else I can help you with regarding FAQs? Type *menu* to see the main options again."}
                }
            },
            "transitions": [{"to_step": "final_exit", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "final_exit",
            "type": "end_flow"
        }
    ]
}