# paynow_integration/constants.py
"""
Constants for Paynow integration
"""

# IPN (Instant Payment Notification) callback URL path
# This is the path portion of the URL that Paynow will call to notify payment status
PAYNOW_IPN_CALLBACK_PATH = '/crm-api/paynow/ipn/'

# Return URL path (for browser-based payments, though not used for Express Checkout)
PAYNOW_RETURN_URL_PATH = '/crm-api/paynow/return/'
