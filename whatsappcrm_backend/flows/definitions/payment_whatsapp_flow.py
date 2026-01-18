# whatsappcrm_backend/flows/definitions/payment_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Paynow Payment Processing.
This flow collects payment method and details, then initiates Paynow payment.
"""

PAYMENT_WHATSAPP_FLOW = {
    "version": "7.3",
    "data_api_version": "3.0",
    "data_channel_uri": "https://backend.kalaisafaris.com/crm-api/flows/paynow-payment-webhook/",
    "routing_model": {
        "PAYMENT": ["PAYMENT_PROCESSING", "PAYMENT_ERROR"]
    },
    "screens": [
        {
            "id": "PAYMENT",
            "title": "Complete Payment",
            "data": {
                "booking_reference": {
                    "type": "string",
                    "__example__": "BK-12345"
                },
                "amount": {
                    "type": "string",
                    "__example__": "150.00"
                },
                "currency": {
                    "type": "string",
                    "__example__": "USD"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Payment Details"
                    },
                    {
                        "type": "TextBody",
                        "text": "Booking: ${data.booking_reference}\nAmount: ${data.amount} ${data.currency}"
                    },
                    {
                        "type": "TextCaption",
                        "text": "Select your preferred payment method and complete the payment securely."
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "payment_method",
                        "label": "Payment Method",
                        "required": True,
                        "data-source": [
                            {
                                "id": "ecocash",
                                "title": "💚 Ecocash",
                                "description": "Pay with Ecocash mobile money"
                            },
                            {
                                "id": "onemoney",
                                "title": "💙 OneMoney",
                                "description": "Pay with OneMoney"
                            },
                            {
                                "id": "innbucks",
                                "title": "🟣 Innbucks",
                                "description": "Pay with Innbucks wallet"
                            }
                        ]
                    },
                    {
                        "type": "TextInput",
                        "name": "phone_number",
                        "label": "Phone Number",
                        "required": True,
                        "input-type": "phone",
                        "helper-text": "Enter phone number linked to your mobile money account (e.g., 263771234567)"
                    },
                    {
                        "type": "TextInput",
                        "name": "email",
                        "label": "Email",
                        "required": True,
                        "input-type": "email",
                        "helper-text": "Required for your payment receipt and Paynow authorization"
                    },
                    {
                        "type": "Footer",
                        "label": "Pay Now",
                        "on-click-action": {
                            "name": "data_exchange",
                            "payload": {
                                "booking_reference": "${data.booking_reference}",
                                "amount": "${data.amount}",
                                "payment_method": "${form.payment_method}",
                                "phone_number": "${form.phone_number}",
                                "email": "${form.email}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "PAYMENT_PROCESSING",
            "title": "Processing Payment",
            "terminal": True,
            "success": True,
            "data": {
                "payment_reference": {
                    "type": "string",
                    "__example__": "PAY-2025-12345"
                },
                "instructions": {
                    "type": "string",
                    "__example__": "Please check your Ecocash phone for a prompt to complete payment."
                },
                "poll_url": {
                    "type": "string",
                    "__example__": "https://api.paynow.co.zw/poll/..."
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "✅ Payment Initiated"
                    },
                    {
                        "type": "TextBody",
                        "text": "Reference: ${data.payment_reference}"
                    },
                    {
                        "type": "TextBody",
                        "text": "${data.instructions}"
                    },
                    {
                        "type": "TextCaption",
                        "text": "You will receive a WhatsApp notification once payment is confirmed."
                    },
                    {
                        "type": "Footer",
                        "label": "Done",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "payment_reference": "${data.payment_reference}",
                                "poll_url": "${data.poll_url}",
                                "status": "initiated"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "PAYMENT_ERROR",
            "title": "Payment Error",
            "terminal": True,
            "data": {
                "error_message": {
                    "type": "string",
                    "__example__": "Payment could not be initiated. Please try again."
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "❌ Payment Failed"
                    },
                    {
                        "type": "TextBody",
                        "text": "${data.error_message}"
                    },
                    {
                        "type": "TextCaption",
                        "text": "Please contact our support team or try again."
                    },
                    {
                        "type": "Footer",
                        "label": "Close",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "status": "failed"
                            }
                        }
                    }
                ]
            }
        }
    ]
}

# Metadata for the flow
PAYMENT_FLOW_METADATA = {
    "name": "payment_whatsapp_flow",
    "friendly_name": "Paynow Payment Processing",
    "description": "Interactive WhatsApp flow for processing Paynow payments",
    "trigger_keywords": [],
    "is_active": True,
    "category": "payment"
}
