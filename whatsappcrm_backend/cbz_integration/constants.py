"""
Constants for CBZ/iVeri payment integration.
Centralises URLs and configuration values to avoid hardcoding.
"""

# iVeri Gateway Portal URLs
IVERI_PORTAL_URL_LIVE = 'https://portal.host.iveri.com'
IVERI_PORTAL_URL_TEST = 'https://portal.host.iveri.com'  # Same host, Mode field controls test/live

# REST API endpoints (relative to portal URL)
IVERI_REST_TRANSACTIONS = '/api/transactions'

# API Version
IVERI_API_VERSION = '2.0'

# EcoCash PAN prefix — mobile numbers are encoded as: 910012 + mobile_number
ECOCASH_PAN_PREFIX = '910012'

# Default expiry date for EcoCash pseudo-PAN (any future date works)
ECOCASH_DEFAULT_EXPIRY = '1230'

# Transaction commands
COMMAND_DEBIT = 'Debit'
COMMAND_AUTHORISATION = 'Authorisation'
COMMAND_CREDIT = 'Credit'
COMMAND_VOID = 'Void'
COMMAND_LOOKUP = 'Lookup'

# Transaction modes
MODE_TEST = 'Test'
MODE_LIVE = 'LIVE'

# ECI for e-commerce (Card Not Present)
ECI_ECOMMERCE = '7'  # Secure e-commerce with SSL

# Result codes
RESULT_CODE_SUCCESS = '0'
STATUS_PENDING = 'Pending'
STATUS_APPROVED = 'Approved'
