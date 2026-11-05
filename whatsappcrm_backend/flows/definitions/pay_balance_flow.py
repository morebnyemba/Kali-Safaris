# whatsappcrm_backend/flows/definitions/pay_balance_flow.py
"""
Pay a booking balance in instalments, or get the secure link to upload IDs.

Only the contact's own upcoming bookings are offered (picked from a list, by
booking id) — never a typed reference, which is shared by every paid booking
on a departure. Amounts are validated server-side (check_instalment_amount):
at least MIN_INSTALMENT (or the whole balance if smaller), at most the balance.
EcoCash is charged in-chat; card and Omari go through the secure website link.
"""

_DONE_FOOTER = "\n\nType *menu* for the main menu."

PAY_BALANCE_FLOW = {
    "name": "pay_balance_flow",
    "friendly_name": "Pay Balance / Upload IDs",
    "description": "Pay a booking balance (full or instalment) or get the secure link to upload traveller IDs.",
    "trigger_keywords": [
        "pay balance", "my balance", "instalment", "installment",
        "upload id", "upload ids", "manage booking",
    ],
    "is_active": True,
    "steps": [
        {
            "name": "start_pay_balance",
            "is_entry_point": True,
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "load_open_bookings", "params_template": {}}]},
            "transitions": [
                {"to_step": "no_open_bookings", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "pb_state", "value": "none"}},
                {"to_step": "select_only_booking", "priority": 2, "condition_config": {"type": "variable_equals", "variable_name": "pb_state", "value": "one"}},
                {"to_step": "ask_which_booking", "priority": 3, "condition_config": {"type": "always_true"}},
            ],
        },
        {
            "name": "no_open_bookings",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": (
                "✅ You have no upcoming bookings with a balance or missing IDs.\n\n"
                "If you paid from another number, message us your booking reference and we'll help." + _DONE_FOOTER
            )}}},
        },
        {
            "name": "ask_which_booking",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Your bookings"},
                        "body": {"text": "Which booking would you like to pay for or update?"},
                        "action": {"button": "Choose booking", "sections": [{"title": "Upcoming", "rows": "{{ pb_rows | tojson }}"}]},
                    },
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "pb_reply"},
                "fallback_config": {"re_prompt_message_text": "Please tap *Choose booking* and pick one."},
            },
            "transitions": [{"to_step": "select_only_booking", "condition_config": {"type": "always_true"}}],
        },
        {
            "name": "select_only_booking",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "select_open_booking", "params_template": {"reply_id": "{{ pb_reply }}"}}]},
            "transitions": [
                {"to_step": "booking_options", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "pb_valid", "value": "True"}},
                {"to_step": "start_pay_balance", "priority": 2, "condition_config": {"type": "always_true"}},
            ],
        },
        {
            "name": "booking_options",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Booking {{ pb_reference }}"},
                        "body": {"text": (
                            "*{{ pb_tour }}* · {{ pb_date }}\n\n"
                            "💰 Total: ${{ pb_total }}\n💵 Paid: ${{ pb_paid }}\n📊 Balance: *${{ pb_balance }}*"
                            "{% if pb_missing_ids %}\n\n🪪 ID/passport still needed for: {{ pb_missing_ids }}{% endif %}"
                        )},
                        "action": {"button": "Choose an option", "sections": [{"title": "Options", "rows": "{{ pb_menu_rows | tojson }}"}]},
                    },
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "pb_choice"},
                "fallback_config": {"re_prompt_message_text": "Please tap *Choose an option*."},
            },
            "transitions": [
                {"to_step": "set_full_balance", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "pb_full"}},
                {"to_step": "ask_instalment_amount", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "pb_part"}},
                {"to_step": "send_secure_link", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "pb_link"}},
            ],
        },
        {
            "name": "set_full_balance",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "pb_amount_input", "value_template": "{{ pb_balance }}"}]},
            "transitions": [{"to_step": "check_amount", "condition_config": {"type": "always_true"}}],
        },
        {
            "name": "ask_instalment_amount",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": (
                    "How much would you like to pay now?\n\nAny amount from *${{ pb_minimum }}* to *${{ pb_balance }}*. "
                    "Reply with just the number, e.g. 50"
                )}},
                "reply_config": {"expected_type": "text", "save_to_variable": "pb_amount_input"},
            },
            "transitions": [{"to_step": "check_amount", "condition_config": {"type": "always_true"}}],
        },
        {
            "name": "check_amount",
            "type": "action",
            "config": {"actions_to_run": [{
                "action_type": "check_instalment_amount",
                "params_template": {"booking_id": "{{ pb_booking_id }}", "amount": "{{ pb_amount_input }}"},
            }]},
            "transitions": [
                {"to_step": "ask_payment_method", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "pb_amount_valid", "value": "True"}},
                {"to_step": "amount_invalid", "priority": 2, "condition_config": {"type": "always_true"}},
            ],
        },
        {
            "name": "amount_invalid",
            "type": "send_message",
            "config": {"message_type": "text", "text": {"body": "⚠️ {{ pb_amount_error }}"}},
            "transitions": [{"to_step": "ask_instalment_amount", "condition_config": {"type": "always_true"}}],
        },
        {
            "name": "ask_payment_method",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Pay *${{ pb_amount }}* towards {{ pb_reference }} with:"},
                        "action": {"buttons": [
                            {"type": "reply", "reply": {"id": "pb_ecocash", "title": "EcoCash"}},
                            {"type": "reply", "reply": {"id": "pb_web", "title": "Card or Omari"}},
                            {"type": "reply", "reply": {"id": "pb_cancel", "title": "Cancel"}},
                        ]},
                    },
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "pb_method"},
                "fallback_config": {"re_prompt_message_text": "Please tap one of the buttons."},
            },
            "transitions": [
                {"to_step": "ask_ecocash_number", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "pb_ecocash"}},
                {"to_step": "send_web_payment_link", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "pb_web"}},
                {"to_step": "pay_balance_cancelled", "priority": 3, "condition_config": {"type": "always_true"}},
            ],
        },
        {
            "name": "ask_ecocash_number",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Enter the EcoCash number to charge (format 2637XXXXXXXX or 07XXXXXXXX)."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "payment_phone", "validation_regex": "^(2637[0-9]{8}|07[0-9]{8})$"},
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please enter a valid Zimbabwe mobile number (e.g., 263771234567 or 0771234567).",
                },
            },
            "transitions": [{"to_step": "charge_ecocash", "condition_config": {"type": "always_true"}}],
        },
        {
            "name": "charge_ecocash",
            "type": "action",
            "config": {"actions_to_run": [{
                "action_type": "initiate_cbz_ecocash_payment",
                "params_template": {"booking_id": "{{ pb_booking_id }}", "amount": "{{ pb_amount }}", "currency": "USD", "msisdn": "{{ payment_phone }}"},
            }]},
            "transitions": [
                {"to_step": "ecocash_approved", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "cbz_payment_status", "value": "approved"}},
                {"to_step": "ecocash_pending", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "cbz_payment_status", "value": "pending"}},
                {"to_step": "ecocash_failed", "priority": 2, "condition_config": {"type": "always_true"}},
            ],
        },
        {
            "name": "ecocash_approved",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": (
                "🎉 Payment received: *${{ pb_amount }}* for {{ pb_reference }}.\nPayment ref: {{ cbz_payment_reference }}\n\n"
                "Type *pay balance* any time to pay more or check what's left." + _DONE_FOOTER
            )}}},
        },
        {
            "name": "ecocash_pending",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": (
                "⏳ Approve the EcoCash prompt on *{{ payment_phone }}* to pay *${{ pb_amount }}*.\nPayment ref: {{ cbz_payment_reference }}\n\n"
                "We'll update your booking as soon as EcoCash confirms." + _DONE_FOOTER
            )}}},
        },
        {
            "name": "ecocash_failed",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": (
                "⚠️ The EcoCash payment didn't go through: {{ cbz_payment_error_message or 'not approved' }}.\n\n"
                "Nothing was charged. Type *pay balance* to try again, or pay by card or Omari here:\n{{ pb_link }}?amount={{ pb_amount }}"
                + _DONE_FOOTER
            )}}},
        },
        {
            "name": "send_web_payment_link",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": (
                "💳 Pay *${{ pb_amount }}* by card, Omari or EcoCash on our secure page:\n\n{{ pb_link }}?amount={{ pb_amount }}\n\n"
                "This link is private to your booking — please don't share it." + _DONE_FOOTER
            )}}},
        },
        {
            "name": "send_secure_link",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": (
                "🔐 Your secure booking page for {{ pb_reference }}:\n\n{{ pb_link }}\n\n"
                "{% if pb_missing_ids %}Upload the ID/passport photos for {{ pb_missing_ids }} there. {% endif %}"
                "{% if pb_balance|float > 0 %}You can also pay the ${{ pb_balance }} balance — all at once or in instalments. {% endif %}"
                "This link is private to your booking — please don't share it." + _DONE_FOOTER
            )}}},
        },
        {
            "name": "pay_balance_cancelled",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "No problem — nothing was charged." + _DONE_FOOTER}}},
        },
    ],
}
