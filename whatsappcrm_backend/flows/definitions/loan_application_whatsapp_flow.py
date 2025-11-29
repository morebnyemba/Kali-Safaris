# whatsappcrm_backend/flows/definitions/loan_application_whatsapp_flow.py

"""
WhatsApp Flow JSON definition for Loan Application.
This is a conversion of the traditional flow to WhatsApp's interactive flow format.

Note: The new WhatsApp Flow format does not support conditional branching.
This flow uses a linear approach where users select loan type first, then provide
all relevant fields. The backend handler will interpret the data based on the loan type.
"""

LOAN_APPLICATION_WHATSAPP_FLOW = {
    "version": "7.3",
    "screens": [
        {
            "id": "WELCOME",
            "title": "Loan Application",
            "data": {
                "loan_type": {
                    "type": "string",
                    "__example__": "cash_loan"
                },
                "loan_applicant_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "loan_national_id": {
                    "type": "string",
                    "__example__": "12-345678-A-12"
                },
                "loan_employment_status": {
                    "type": "string",
                    "__example__": "employed"
                },
                "loan_monthly_income": {
                    "type": "number",
                    "__example__": 1000
                },
                "loan_request_amount": {
                    "type": "string",
                    "__example__": "500"
                },
                "loan_product_interest": {
                    "type": "string",
                    "__example__": "5kVA Solar Kit"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Loan Application"
                    },
                    {
                        "type": "TextBody",
                        "text": "Welcome to our loan application service. Let's get started with your application."
                    },
                    {
                        "type": "Footer",
                        "label": "Start Application",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "LOAN_TYPE"
                            },
                            "payload": {
                                "loan_type": "",
                                "loan_applicant_name": "",
                                "loan_national_id": "",
                                "loan_employment_status": "",
                                "loan_monthly_income": 0,
                                "loan_request_amount": "",
                                "loan_product_interest": ""
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "LOAN_TYPE",
            "title": "Type of Loan",
            "data": {
                "loan_type": {
                    "type": "string",
                    "__example__": "cash_loan"
                },
                "loan_applicant_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "loan_national_id": {
                    "type": "string",
                    "__example__": "12-345678-A-12"
                },
                "loan_employment_status": {
                    "type": "string",
                    "__example__": "employed"
                },
                "loan_monthly_income": {
                    "type": "number",
                    "__example__": 1000
                },
                "loan_request_amount": {
                    "type": "string",
                    "__example__": "500"
                },
                "loan_product_interest": {
                    "type": "string",
                    "__example__": "5kVA Solar Kit"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Select Loan Type"
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "loan_type",
                        "label": "Are you applying for a Cash Loan or a Product Loan?",
                        "required": True,
                        "data-source": [
                            {"id": "cash_loan", "title": "Cash Loan"},
                            {"id": "product_loan", "title": "Product Loan"}
                        ]
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "PERSONAL_INFO"
                            },
                            "payload": {
                                "loan_type": "${form.loan_type}",
                                "loan_applicant_name": "${data.loan_applicant_name}",
                                "loan_national_id": "${data.loan_national_id}",
                                "loan_employment_status": "${data.loan_employment_status}",
                                "loan_monthly_income": "${data.loan_monthly_income}",
                                "loan_request_amount": "${data.loan_request_amount}",
                                "loan_product_interest": "${data.loan_product_interest}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "PERSONAL_INFO",
            "title": "Personal Details",
            "data": {
                "loan_type": {
                    "type": "string",
                    "__example__": "cash_loan"
                },
                "loan_applicant_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "loan_national_id": {
                    "type": "string",
                    "__example__": "12-345678-A-12"
                },
                "loan_employment_status": {
                    "type": "string",
                    "__example__": "employed"
                },
                "loan_monthly_income": {
                    "type": "number",
                    "__example__": 1000
                },
                "loan_request_amount": {
                    "type": "string",
                    "__example__": "500"
                },
                "loan_product_interest": {
                    "type": "string",
                    "__example__": "5kVA Solar Kit"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Your Information"
                    },
                    {
                        "type": "TextInput",
                        "name": "loan_applicant_name",
                        "label": "Full Name",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter your full legal name"
                    },
                    {
                        "type": "TextInput",
                        "name": "loan_national_id",
                        "label": "National ID Number",
                        "required": True,
                        "input-type": "text",
                        "helper-text": "Enter your National ID number"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "EMPLOYMENT_INFO"
                            },
                            "payload": {
                                "loan_type": "${data.loan_type}",
                                "loan_applicant_name": "${form.loan_applicant_name}",
                                "loan_national_id": "${form.loan_national_id}",
                                "loan_employment_status": "${data.loan_employment_status}",
                                "loan_monthly_income": "${data.loan_monthly_income}",
                                "loan_request_amount": "${data.loan_request_amount}",
                                "loan_product_interest": "${data.loan_product_interest}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "EMPLOYMENT_INFO",
            "title": "Employment Details",
            "data": {
                "loan_type": {
                    "type": "string",
                    "__example__": "cash_loan"
                },
                "loan_applicant_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "loan_national_id": {
                    "type": "string",
                    "__example__": "12-345678-A-12"
                },
                "loan_employment_status": {
                    "type": "string",
                    "__example__": "employed"
                },
                "loan_monthly_income": {
                    "type": "number",
                    "__example__": 1000
                },
                "loan_request_amount": {
                    "type": "string",
                    "__example__": "500"
                },
                "loan_product_interest": {
                    "type": "string",
                    "__example__": "5kVA Solar Kit"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Employment Status"
                    },
                    {
                        "type": "RadioButtonsGroup",
                        "name": "loan_employment_status",
                        "label": "What is your current employment status?",
                        "required": True,
                        "data-source": [
                            {"id": "employed", "title": "Employed"},
                            {"id": "self_employed", "title": "Self-Employed"},
                            {"id": "unemployed", "title": "Other"}
                        ]
                    },
                    {
                        "type": "TextInput",
                        "name": "loan_monthly_income",
                        "label": "Monthly Income (USD)",
                        "required": True,
                        "input-type": "number",
                        "helper-text": "Enter your estimated monthly income"
                    },
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "navigate",
                            "next": {
                                "type": "screen",
                                "name": "LOAN_DETAILS"
                            },
                            "payload": {
                                "loan_type": "${data.loan_type}",
                                "loan_applicant_name": "${data.loan_applicant_name}",
                                "loan_national_id": "${data.loan_national_id}",
                                "loan_employment_status": "${form.loan_employment_status}",
                                "loan_monthly_income": "${form.loan_monthly_income}",
                                "loan_request_amount": "${data.loan_request_amount}",
                                "loan_product_interest": "${data.loan_product_interest}"
                            }
                        }
                    }
                ]
            }
        },
        {
            "id": "LOAN_DETAILS",
            "title": "Loan Details",
            "data": {
                "loan_type": {
                    "type": "string",
                    "__example__": "cash_loan"
                },
                "loan_applicant_name": {
                    "type": "string",
                    "__example__": "Jane Doe"
                },
                "loan_national_id": {
                    "type": "string",
                    "__example__": "12-345678-A-12"
                },
                "loan_employment_status": {
                    "type": "string",
                    "__example__": "employed"
                },
                "loan_monthly_income": {
                    "type": "number",
                    "__example__": 1000
                },
                "loan_request_amount": {
                    "type": "string",
                    "__example__": "500"
                },
                "loan_product_interest": {
                    "type": "string",
                    "__example__": "5kVA Solar Kit"
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "TextHeading",
                        "text": "Loan Specifics"
                    },
                    {
                        "type": "TextBody",
                        "text": "Please provide details about your loan request. If you selected Cash Loan, fill in the amount. If you selected Product Loan, specify the product name."
                    },
                    {
                        "type": "TextInput",
                        "name": "loan_request_amount",
                        "label": "Cash Amount (USD)",
                        "required": False,
                        "input-type": "text",
                        "helper-text": "For Cash Loan: Enter amount. For Product Loan: Enter 0 or leave blank"
                    },
                    {
                        "type": "TextInput",
                        "name": "loan_product_interest",
                        "label": "Product of Interest",
                        "required": False,
                        "input-type": "text",
                        "helper-text": "For Product Loan: Enter product name. For Cash Loan: Enter N/A or leave blank"
                    },
                    {
                        "type": "Footer",
                        "label": "Submit Application",
                        "on-click-action": {
                            "name": "complete",
                            "payload": {
                                "loan_type": "${data.loan_type}",
                                "loan_applicant_name": "${data.loan_applicant_name}",
                                "loan_national_id": "${data.loan_national_id}",
                                "loan_employment_status": "${data.loan_employment_status}",
                                "loan_monthly_income": "${data.loan_monthly_income}",
                                "loan_request_amount": "${form.loan_request_amount}",
                                "loan_product_interest": "${form.loan_product_interest}"
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


# Metadata for the flow
LOAN_APPLICATION_FLOW_METADATA = {
    "name": "loan_application_whatsapp",
    "friendly_name": "Loan Application (Interactive)",
    "description": "Interactive WhatsApp flow for applying for cash or product loans",
    "trigger_keywords": ["loan", "apply for loan"],
    "is_active": True
}
