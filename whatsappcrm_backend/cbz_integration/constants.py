"""
Constants for CBZ/iVeri payment integration.
Centralises URLs and configuration values to avoid hardcoding.
"""

# iVeri Gateway Portal URLs
IVERI_PORTAL_URL_LIVE = 'https://portal.host.iveri.com'
IVERI_PORTAL_URL_TEST = 'https://portal.host.iveri.com'  # Same host, Mode field controls test/live

# REST API endpoints (relative to portal URL)
IVERI_REST_TRANSACTIONS = '/api/transactions'

# 3DS 2 enrollment endpoint (relative to portal URL) — form POST, browser-initiated
IVERI_3DS_ENROLLMENT = '/threedsecure/EnrollmentInitial'

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

# ECI (Electronic Commerce Indicator) values for EcoCash (legacy numeric)
ECI_ECOMMERCE = '7'           # Card Not Present, no 3DS (used for EcoCash only)

# ECI string values for 3DS 2 (iVeri Enterprise uses string labels, not numeric)
ECI_3DS2_AUTHENTICATED = 'ThreeDSecure'         # Fully authenticated — ECI 05/02
ECI_3DS2_ATTEMPTED = 'ThreeDSecureAttempted'    # Attempted — ECI 06/01
ECI_3DS2_SECURE_CHANNEL = 'SecureChannel'       # Secure channel — ECI 07

# Legacy 3DS v1 ECI numeric values (kept for reference/compatibility)
ECI_3DS_AUTHENTICATED = '5'   # 3DS v1 fully authenticated
ECI_3DS_ATTEMPTED = '6'       # 3DS v1 attempted

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
