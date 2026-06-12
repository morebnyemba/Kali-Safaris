"""
Constants for CBZ/iVeri payment integration.
Centralises URLs and configuration values to avoid hardcoding.
"""

# iVeri Gateway Portal URLs
IVERI_PORTAL_URL_LIVE = 'https://portal.host.iveri.com'
IVERI_PORTAL_URL_TEST = 'https://portal.host.iveri.com'  # Same host, Mode field controls test/live

# REST API endpoints (relative to portal URL)
IVERI_REST_TRANSACTIONS = '/api/transactions'

# SOAP certificate lifecycle defaults
IVERI_SOAP_TIMEOUT = 60

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

# ECI (Electronic Commerce Indicator) values
ECI_ECOMMERCE = '7'           # Card Not Present, no 3DS authentication
ECI_3DS_AUTHENTICATED = '5'   # Fully 3DS authenticated — liability shifts to issuer
ECI_3DS_ATTEMPTED = '6'       # 3DS attempted but not completed (e.g. card not enrolled)

# Result codes
RESULT_CODE_SUCCESS = '0'
STATUS_PENDING = 'Pending'
STATUS_APPROVED = 'Approved'

# ─── iVeri Status Map ────────────────────────────────────────────────
# Authoritative mapping of iVeri ResultCode values to semantic labels.
# Source: iVeri Enterprise Gateway documentation + task specification.
IVERI_STATUS_MAP = {
    "0": "SUCCESS",         # Successful payment
    "1": "ERROR",           # System error / timeout — retriable
    "4": "DECLINED",        # Card declined
    "255": "INVALID_CARD",  # Invalid card / PAN
}

# ResultCodes that indicate a transient failure worth retrying
IVERI_RETRIABLE_CODES = {"1"}  # Timeout / system error

# ResultCodes that are terminal failures — never retry
IVERI_TERMINAL_FAILURE_CODES = {"4", "255"}  # Declined or invalid card
