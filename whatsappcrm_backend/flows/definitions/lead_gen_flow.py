# whatsappcrm_backend/flows/definitions/lead_gen_flow.py

LEAD_GENERATION_FLOW = {
    "name": "lead_generation",
    "friendly_name": "Purchase Products",
    "description": "Guides a user through selecting products, providing delivery details, and creating an order.",
    "trigger_keywords": ["buy", "shop", "purchase", "buy product"],
    "is_active": True,
    "steps": [
        # 1. Initialize Cart
        {
            "name": "start_purchase_flow",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "cart_items", "value_template": []}
                ]
            },
            "transitions": [{"to_step": "query_products_for_display", "condition_config": {"type": "always_true"}}]
        },
        # 2. Query Products
        {
            "name": "query_products_for_display",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Product",
                    "variable_name": "available_products",
                    "filters_template": {
                        "is_active": True,
                        "product_type__not_in": "['service']" # Exclude service types, show all other products.
                    },
                    "fields_to_return": ["sku", "name", "price", "category__name"],
                    "order_by": ["category__name", "name"]
                }]
            },
            "transitions": [{"to_step": "check_if_products_exist", "condition_config": {"type": "always_true"}}]
        },
        # 3. Check if products exist
        {
            "name": "check_if_products_exist",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "display_products_and_ask_sku", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "available_products.0"}},
                {"to_step": "handle_no_products_available", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        # 4. Display products and start the loop
        {
            "name": "display_products_and_ask_sku",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": (
                            "Welcome to our shop! Here are our available products:\n"
                            "{% for category in available_products | groupby('category__name') %}\n"
                            "*_{{ category.grouper or 'Other Products' }}:_*\n\n"
                            "{% for product in category.list %}"
                            "_[{{ loop.index + loop.parent.loop.index0 * available_products|length }}]_ *{{ product.name }}*\n  Price: ${{ product.price }}\n"
                            "{% endfor %}"
                            "{% endfor %}\n\n"
                            "Please enter the number of the product you'd like to add to your cart. Type *done* when you are finished."
                        )
                    }
                },
                "reply_config": {"expected_type": "number", "save_to_variable": "selected_product_index"}
            },
            "transitions": [
                {"to_step": "check_if_cart_is_empty", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "done"}},
                {"to_step": "get_product_from_selection", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        # 5. Verify SKU
        {
            "name": "get_product_from_selection",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_context_variable",
                    "variable_name": "found_product",
                    "value_template": "{{ [available_products[selected_product_index - 1]] if selected_product_index > 0 and selected_product_index <= available_products|length else [] }}"
                }]
            },
            "transitions": [
                {"to_step": "ask_for_quantity", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "found_product.0"}},
                {"to_step": "handle_invalid_selection", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        # 6. Ask for Quantity
        {
            "name": "ask_for_quantity",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "How many units of *{{ found_product.0.name }}* would you like to add?"}},
                "reply_config": {"expected_type": "number", "save_to_variable": "product_quantity"}
            },
            "transitions": [{"to_step": "add_to_cart", "condition_config": {"type": "variable_exists", "variable_name": "product_quantity"}}]
        },
        # 7. Add to Cart
        {
            "name": "add_to_cart",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_context_variable",
                    "variable_name": "cart_items",
                    "value_template": "{{ cart_items + [{'sku': found_product.0.sku, 'quantity': product_quantity, 'name': found_product.0.name, 'price': found_product.0.price}] }}"
                }]
            },
            "transitions": [{"to_step": "display_cart_and_ask_next", "condition_config": {"type": "always_true"}}]
        },
        # 8. Display cart and ask for next item
        {
            "name": "display_cart_and_ask_next",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": (
                            "✅ Added {{ product_quantity }} x *{{ found_product.0.name }}*.\n\n"
                            "🛒 *Your Cart:*\n"
                            "{% set total = 0 %}"
                            "{% for item in cart_items %}"
                            "  - {{ item.quantity }} x {{ item.name }} (${{ '%.2f'|format(item.price * item.quantity) }})\n"
                            "{% set total = total + (item.price * item.quantity) %}"
                            "{% endfor %}\n"
                            "*Subtotal: ${{ total }}*\n\n"
                            "Enter another SKU to add more products, or type *done* to proceed to checkout."
                        ) # This message is now part of a loop and will be updated.
                    }
                },
                "reply_config": {"expected_type": "number", "save_to_variable": "selected_product_index"}
            },
            "transitions": [
                {"to_step": "check_if_cart_is_empty", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "done"}},
                {"to_step": "get_product_from_selection", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        # 9. Handle invalid SKU input
        {
            "name": "handle_invalid_selection",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Sorry, that's not a valid selection. Please enter a number from the list, or type *done* to finish."}},
                "reply_config": {"expected_type": "number", "save_to_variable": "selected_product_index"}
            },
            "transitions": [
                {"to_step": "check_if_cart_is_empty", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "done"}},
                {"to_step": "get_product_from_selection", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        # 10. Checkout process starts here
        {
            "name": "check_if_cart_is_empty",
            "type": "condition",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "ask_delivery_name", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "cart_items.0"}},
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        # 11. Collect Delivery Details
        {"name": "ask_delivery_name", "type": "question", "config": {"message_config": {"message_type": "text", "text": {"body": "Let's get your delivery details. What is the full name for the delivery?"}}, "reply_config": {"expected_type": "text", "save_to_variable": "delivery_name"}}, "transitions": [{"to_step": "ask_delivery_phone", "condition_config": {"type": "always_true"}}]},
        {"name": "ask_delivery_phone", "type": "question", "config": {"message_config": {"message_type": "text", "text": {"body": "Great. What is the best contact number for the delivery?"}}, "reply_config": {"expected_type": "text", "save_to_variable": "delivery_phone", "validation_regex": "^\\+?[1-9]\\d{8,14}$"}, "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid phone number (e.g., +263...)"}}, "transitions": [{"to_step": "ask_delivery_address", "condition_config": {"type": "always_true"}}]},
        {"name": "ask_delivery_address", "type": "question", "config": {"message_config": {"message_type": "text", "text": {"body": "And finally, what is the full delivery address? Please be as specific as possible."}}, "reply_config": {"expected_type": "text", "save_to_variable": "delivery_address", "validation_regex": "^.{10,}"}, "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please provide a more detailed address."}}, "transitions": [{"to_step": "confirm_order", "condition_config": {"type": "always_true"}}]},
        # 12. Confirm Order
        {
            "name": "confirm_order",
            "type": "question",
            "config": {
                "message_config": {"message_type": "interactive", "interactive": {"type": "button", "header": {"type": "text", "text": "Confirm Your Order"}, "body": {"text": "Please review your order details:\n\n📝 *Order Summary:*\n{% set total = 0 %}{% for item in cart_items %}- {{ item.quantity }} x {{ item.name }} (${{ item.price * item.quantity }})\n{% set total = total + (item.price * item.quantity) %}{% endfor %}\n*Total Amount: ${{ total }}*\n\n🚚 *Delivery Details:*\nName: {{ delivery_name }}\nPhone: {{ delivery_phone }}\nAddress: {{ delivery_address }}"}, "action": {"buttons": [{"type": "reply", "reply": {"id": "confirm_purchase", "title": "✅ Confirm Order"}}, {"type": "reply", "reply": {"id": "cancel_purchase", "title": "❌ Cancel"}}]}}},
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "order_confirmation"}
            },
            "transitions": [
                {"to_step": "generate_order_number", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_purchase"}},
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        # 13. Create Order
        {"name": "generate_order_number", "type": "action", "config": {"actions_to_run": [{"action_type": "generate_unique_order_number", "params_template": {"save_to_variable": "generated_order_number_raw"}}]}, "transitions": [{"to_step": "prefix_order_number", "condition_config": {"type": "always_true"}}]},
        {"name": "prefix_order_number", "type": "action", "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "generated_order_number", "value_template": "HAN-{{ generated_order_number_raw }}"}]}, "transitions": [{"to_step": "create_final_order", "condition_config": {"type": "always_true"}}]},
        {
            "name": "create_final_order",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "create_order_from_cart", "params_template": {"cart_context_var": "cart_items", "order_name_template": "Online Order for {{ delivery_name }}", "order_number_context_var": "generated_order_number", "notes_template": "Delivery to: {{ delivery_name }}, {{ delivery_phone }}, {{ delivery_address }}. Placed via WhatsApp.", "stage": "closed_won", "payment_status": "pending", "save_order_to": "created_order_details"}},
                    {"action_type": "send_group_notification", "params_template": {"group_names": ["Sales Team", "System Admins"], "template_name": "hanna_new_online_order_placed"}}
                ]
            },
            "transitions": [{"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}]
        },
        # 14. End States
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Thank you for your order! 🎉\n\nYour order #*{{ created_order_details.order_number }}* has been placed successfully.\n\n*Total Amount: ${{ created_order_details.amount }}*\n\nA sales agent will contact you shortly with payment options to finalize your purchase."}}}
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Your order has been cancelled. Type 'menu' to start over."}}}
        },
        {
            "name": "handle_no_products_available",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "I'm sorry, it seems we have no products available for online purchase right now. I'm connecting you with a sales agent who can assist you directly.",
                "notification_details": "Purchase Flow: User tried to shop, but no active products were found in the database."
            }
        }
    ]
}