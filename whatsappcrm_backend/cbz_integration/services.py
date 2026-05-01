"""
iVeri REST API client for CBZ payment gateway.

Handles communication with the iVeri Enterprise Gateway for both
EcoCash (mobile money) and Card (Visa/Mastercard) payments.

Flow:
  EcoCash: debit_ecocash() → STK Push sent to customer → response indicates success/failure
  Card:    debit_card() → immediate response (or 3DS redirect data for website)
"""
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional
from xml.etree import ElementTree as ET

import requests
from django.conf import settings

from .constants import (
    ECOCASH_DEFAULT_EXPIRY,
    ECOCASH_PAN_PREFIX,
    IVERI_API_VERSION,
    IVERI_REST_TRANSACTIONS,
    IVERI_SOAP_TIMEOUT,
    COMMAND_DEBIT,
    COMMAND_AUTHORISATION,
    COMMAND_CREDIT,
    COMMAND_LOOKUP,
    COMMAND_VOID,
    ECI_ECOMMERCE,
    RESULT_CODE_SUCCESS,
    STATUS_PENDING,
    STATUS_APPROVED,
)


logger = logging.getLogger(__name__)


def _mask_value(value: str, visible_chars: int = 6) -> str:
    """Mask a sensitive identifier while leaving a short suffix for correlation."""
    if not value:
        return "<empty>"
    return f"***{value[-visible_chars:]}" if len(value) > visible_chars else "***"


def _local_name(tag: str) -> str:
    """Return an XML tag without its namespace."""
    return tag.split('}', 1)[-1] if '}' in tag else tag


def _flatten_xml(element: ET.Element) -> Dict[str, Any]:
    """Flatten a SOAP XML subtree into a simple dict keyed by local tag names."""
    flattened: Dict[str, Any] = {}
    for child in element:
        key = _local_name(child.tag)
        if list(child):
            value = _flatten_xml(child)
        else:
            value = (child.text or '').strip()

        if key in flattened:
            existing = flattened[key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                flattened[key] = [existing, value]
        else:
            flattened[key] = value
    return flattened


@dataclass
class IVeriConfig:
    """Configuration for the iVeri REST API."""
    portal_url: str          # e.g., https://portal.host.iveri.com
    certificate_id: str      # CertificateID GUID
    application_id: str      # ApplicationID GUID
    mode: str = 'Test'       # 'Test' or 'LIVE'
    callback_url: str = ''   # Optional out-of-band notification URL


@dataclass
class IVeriCertificateConfig:
    """Configuration for the iVeri SOAP certificate lifecycle API."""
    soap_url: str
    application_id: str
    soap_username: str = ''
    soap_password: str = ''
    soap_namespace: str = ''
    soap_action_base: str = ''
    merchant_id: str = ''
    terminal_id: str = ''
    certificate_id: str = ''
    mode: str = 'Test'
    timeout: int = IVERI_SOAP_TIMEOUT


def build_certificate_client_from_settings(config_model: Optional[Any] = None) -> 'IVeriCertificateClient':
    """Build the SOAP certificate lifecycle client from Django settings and optional DB config."""
    return IVeriCertificateClient(IVeriCertificateConfig(
        soap_url=getattr(settings, 'CBZ_CERTIFICATE_SOAP_URL', ''),
        soap_namespace=getattr(settings, 'CBZ_CERTIFICATE_SOAP_NAMESPACE', ''),
        soap_action_base=getattr(settings, 'CBZ_CERTIFICATE_SOAP_ACTION_BASE', ''),
        soap_username=getattr(settings, 'CBZ_CERTIFICATE_SOAP_USERNAME', ''),
        soap_password=getattr(settings, 'CBZ_CERTIFICATE_SOAP_PASSWORD', ''),
        merchant_id=getattr(settings, 'CBZ_CERTIFICATE_MERCHANT_ID', ''),
        terminal_id=getattr(settings, 'CBZ_CERTIFICATE_TERMINAL_ID', ''),
        application_id=(config_model.application_id if config_model else getattr(settings, 'CBZ_APPLICATION_ID', '')),
        certificate_id=(config_model.certificate_id if config_model and config_model.certificate_id else getattr(settings, 'CBZ_CERTIFICATE_ID', '')),
        mode=(config_model.mode if config_model else getattr(settings, 'CBZ_MODE', 'Test')),
    ))


class IVeriClient:
    """
    Client for the iVeri Enterprise REST API.

    Supports:
    - EcoCash payments via PAN encoding (910012 + mobile number)
    - Card payments (Visa/Mastercard) via direct PAN
    - Transaction status queries
    - Refunds and voids
    """

    def __init__(self, config: Optional[IVeriConfig] = None):
        """
        Initialize the client with configuration.
        If no config is provided, attempts to load from database.
        """
        if config is None:
            config = self._load_config_from_db()

        if config is None:
            raise ValueError(
                "No CBZ/iVeri configuration found. "
                "Please configure CBZ credentials in the admin panel."
            )

        self.config = config
        self._validate_config()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        self.api_url = f"{self.config.portal_url.rstrip('/')}{IVERI_REST_TRANSACTIONS}"

        # Log initialization (masked credentials)
        logger.info(
            "IVeriClient initialized | url=%s app=%s mode=%s callback=%s",
            self.api_url,
            _mask_value(self.config.application_id),
            self.config.mode,
            bool(self.config.callback_url),
        )

    def _validate_config(self) -> None:
        """Validate required REST configuration before attempting requests."""
        missing_fields = []
        if not (self.config.portal_url or '').strip():
            missing_fields.append('portal_url')
        if not (self.config.certificate_id or '').strip():
            missing_fields.append('certificate_id')
        if not (self.config.application_id or '').strip():
            missing_fields.append('application_id')

        if missing_fields:
            logger.error(
                "IVeriClient invalid configuration | missing=%s mode=%s callback=%s",
                ','.join(missing_fields),
                self.config.mode,
                bool(self.config.callback_url),
            )
            raise ValueError(
                "Incomplete CBZ/iVeri configuration. Missing: "
                f"{', '.join(missing_fields)}"
            )

        if self.config.mode not in {'Test', 'LIVE'}:
            logger.warning(
                "IVeriClient unusual mode configured | mode=%s app=%s",
                self.config.mode,
                _mask_value(self.config.application_id),
            )

    @staticmethod
    def _load_config_from_db() -> Optional[IVeriConfig]:
        """Load active CBZ configuration from database."""
        try:
            from .models import CBZConfig as CBZConfigModel

            config_model = CBZConfigModel.get_active_config()
            if config_model:
                return IVeriConfig(
                    portal_url=config_model.portal_url,
                    certificate_id=config_model.certificate_id or '',
                    application_id=config_model.application_id,
                    mode=config_model.mode,
                    callback_url=config_model.callback_url or '',
                )
            else:
                logger.warning("No active CBZ/iVeri configuration found in database.")
                return None
        except Exception as e:
            logger.error(f"Error loading CBZ config from database: {e}", exc_info=True)
            return None

    def _build_payload(self, command: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the standard iVeri REST API payload.

        Args:
            command: Transaction command (Debit, Authorisation, Credit, etc.)
            transaction_data: Additional transaction-specific parameters

        Returns:
            Complete JSON payload for the iVeri REST API
        """
        merchant_reference = transaction_data.get('MerchantReference')
        if not merchant_reference:
            logger.warning(
                "iVeri payload missing merchant reference | command=%s mode=%s",
                command,
                self.config.mode,
            )

        transaction = {
            'ApplicationID': self.config.application_id,
            'Command': command,
            'Mode': self.config.mode,
        }
        transaction.update(transaction_data)

        payload = {
            'Version': IVERI_API_VERSION,
            'CertificateID': self.config.certificate_id,
            'Direction': 'Request',
            'Transaction': transaction,
        }

        # Add callback URL for out-of-band notifications if configured
        if self.config.callback_url:
            payload['Transaction']['NotificationURL'] = self.config.callback_url

        return payload

    def _execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an API request to the iVeri gateway.

        Args:
            payload: Complete JSON payload

        Returns:
            Parsed JSON response

        Raises:
            requests.exceptions.HTTPError: On HTTP errors
            Exception: On unexpected errors
        """
        # Log outgoing request (masked sensitive data)
        safe_log = {
            'Version': payload.get('Version'),
            'Direction': payload.get('Direction'),
            'Command': payload.get('Transaction', {}).get('Command'),
            'Mode': payload.get('Transaction', {}).get('Mode'),
            'Amount': payload.get('Transaction', {}).get('Amount'),
            'Currency': payload.get('Transaction', {}).get('Currency'),
            'MerchantReference': payload.get('Transaction', {}).get('MerchantReference'),
            'HasNotificationURL': bool(payload.get('Transaction', {}).get('NotificationURL')),
        }
        logger.info("iVeri request | %s", safe_log)

        try:
            resp = self.session.post(self.api_url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            # Log response (safe fields only)
            txn_resp = data.get('Transaction', {})
            logger.info(
                "iVeri response | ResultCode=%s Status=%s Description=%s TransactionIndex=%s",
                txn_resp.get('ResultCode'),
                txn_resp.get('Status'),
                txn_resp.get('ResultDescription', '')[:100],
                txn_resp.get('TransactionIndex'),
            )
            return data

        except requests.exceptions.HTTPError as e:
            error_body = e.response.text[:500] if e.response else "No response"
            error_status = e.response.status_code if e.response else "No status"
            logger.error(
                "iVeri HTTP error | status=%s command=%s ref=%s body=%s",
                error_status,
                payload.get('Transaction', {}).get('Command'),
                payload.get('Transaction', {}).get('MerchantReference'),
                error_body,
            )
            raise
        except requests.exceptions.Timeout:
            logger.error(
                "iVeri request timeout | command=%s ref=%s timeout=60s",
                payload.get('Transaction', {}).get('Command'),
                payload.get('Transaction', {}).get('MerchantReference'),
            )
            raise
        except Exception as e:
            logger.error(
                "iVeri unexpected error | command=%s ref=%s error=%s",
                payload.get('Transaction', {}).get('Command'),
                payload.get('Transaction', {}).get('MerchantReference'),
                str(e),
                exc_info=True,
            )
            raise

    # ─── EcoCash Payments ────────────────────────────────────────────

    @staticmethod
    def _format_ecocash_pan(mobile: str) -> str:
        """
        Encode mobile number as EcoCash PAN.

        iVeri expects EcoCash numbers as: 910012 + mobile_number
        Mobile should be in local format without country code (e.g., 0771234567)

        Args:
            mobile: Mobile number (accepts 2637..., 07..., or raw digits)

        Returns:
            PAN string like 9100120771234567
        """
        # Normalize to local format (07XXXXXXXX)
        digits = ''.join(c for c in mobile if c.isdigit())

        if digits.startswith('263'):
            digits = '0' + digits[3:]
        elif not digits.startswith('0') and len(digits) == 9:
            digits = '0' + digits

        return f"{ECOCASH_PAN_PREFIX}{digits}"

    def debit_ecocash(
        self,
        mobile: str,
        amount: Decimal,
        currency: str,
        merchant_reference: str,
    ) -> Dict[str, Any]:
        """
        Process EcoCash payment via iVeri STK Push.

        The customer receives a prompt on their phone to enter their EcoCash PIN.
        The response indicates whether the payment was approved.

        Args:
            mobile: Customer mobile number (2637XXXXXXXX or 07XXXXXXXX)
            amount: Amount to charge (in major units, e.g., 10.50)
            currency: Currency code ('USD' or 'ZWG')
            merchant_reference: Unique merchant reference for this transaction

        Returns:
            iVeri API response dict
        """
        pan = self._format_ecocash_pan(mobile)

        # iVeri amounts are in minor units (cents) as a string
        amount_cents = str(int(amount * 100))

        transaction_data = {
            'Currency': currency,
            'Amount': amount_cents,
            'PAN': pan,
            'ExpiryDate': ECOCASH_DEFAULT_EXPIRY,
            'MerchantReference': merchant_reference,
            'ECI': ECI_ECOMMERCE,
        }

        payload = self._build_payload(COMMAND_DEBIT, transaction_data)
        logger.info(
            "EcoCash debit | mobile=***%s amount=%s %s ref=%s",
            mobile[-4:] if len(mobile) >= 4 else '****',
            amount, currency, merchant_reference,
        )

        return self._execute(payload)

    # ─── Card Payments (Website Only) ────────────────────────────────

    def debit_card(
        self,
        pan: str,
        expiry_date: str,
        cvv: str,
        amount: Decimal,
        currency: str,
        merchant_reference: str,
        threed_secure_data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Process card payment (Visa/Mastercard) via iVeri.

        For website-initiated payments with optional 3D Secure data.

        Args:
            pan: Card number (16 digits)
            expiry_date: Expiry in MMYY format (e.g., '0228')
            cvv: Card CVV/CVC
            amount: Amount to charge
            currency: Currency code ('USD' or 'ZWG')
            merchant_reference: Unique merchant reference
            threed_secure_data: Optional 3DS authentication data

        Returns:
            iVeri API response dict
        """
        amount_cents = str(int(amount * 100))

        transaction_data = {
            'Currency': currency,
            'Amount': amount_cents,
            'PAN': pan,
            'ExpiryDate': expiry_date,
            'CardSecurityCode': cvv,
            'MerchantReference': merchant_reference,
            'ECI': ECI_ECOMMERCE,
        }

        # Add 3D Secure data if provided
        if threed_secure_data:
            transaction_data.update(threed_secure_data)

        payload = self._build_payload(COMMAND_DEBIT, transaction_data)

        # Mask PAN in logs
        masked = f"{pan[:4]}****{pan[-4:]}" if len(pan) >= 8 else "****"
        logger.info(
            "Card debit | pan=%s amount=%s %s ref=%s",
            masked, amount, currency, merchant_reference,
        )

        return self._execute(payload)

    def authorize_card(
        self,
        pan: str,
        expiry_date: str,
        cvv: str,
        amount: Decimal,
        currency: str,
        merchant_reference: str,
    ) -> Dict[str, Any]:
        """
        Pre-authorise a card payment (hold funds without capturing).

        Args:
            Same as debit_card()

        Returns:
            iVeri API response dict with TransactionIndex for later capture
        """
        amount_cents = str(int(amount * 100))

        transaction_data = {
            'Currency': currency,
            'Amount': amount_cents,
            'PAN': pan,
            'ExpiryDate': expiry_date,
            'CardSecurityCode': cvv,
            'MerchantReference': merchant_reference,
            'ECI': ECI_ECOMMERCE,
        }

        payload = self._build_payload(COMMAND_AUTHORISATION, transaction_data)
        return self._execute(payload)

    # ─── Transaction Management ──────────────────────────────────────

    def query_transaction(self, merchant_reference: str) -> Dict[str, Any]:
        """
        Query transaction status by merchant reference.

        Args:
            merchant_reference: Original merchant reference

        Returns:
            iVeri API response dict with current transaction status
        """
        transaction_data = {
            'MerchantReference': merchant_reference,
        }

        payload = self._build_payload(COMMAND_LOOKUP, transaction_data)
        logger.info("Transaction query | ref=%s", merchant_reference)

        return self._execute(payload)

    def refund(
        self,
        transaction_index: str,
        amount: Decimal,
        currency: str,
        merchant_reference: str,
    ) -> Dict[str, Any]:
        """
        Process a refund against a previous transaction.

        Args:
            transaction_index: TransactionIndex from the original transaction
            amount: Amount to refund
            currency: Currency code
            merchant_reference: New unique reference for the refund

        Returns:
            iVeri API response dict
        """
        amount_cents = str(int(amount * 100))

        transaction_data = {
            'Currency': currency,
            'Amount': amount_cents,
            'TransactionIndex': transaction_index,
            'MerchantReference': merchant_reference,
        }

        payload = self._build_payload(COMMAND_CREDIT, transaction_data)
        logger.info(
            "Refund | original_txn=%s amount=%s %s ref=%s",
            transaction_index, amount, currency, merchant_reference,
        )

        return self._execute(payload)

    def void_transaction(
        self,
        transaction_index: str,
        merchant_reference: str,
    ) -> Dict[str, Any]:
        """
        Void a pending/authorised transaction.

        Args:
            transaction_index: TransactionIndex of the transaction to void
            merchant_reference: Original merchant reference

        Returns:
            iVeri API response dict
        """
        transaction_data = {
            'TransactionIndex': transaction_index,
            'MerchantReference': merchant_reference,
        }

        payload = self._build_payload(COMMAND_VOID, transaction_data)
        logger.info("Void | txn=%s ref=%s", transaction_index, merchant_reference)

        return self._execute(payload)

    # ─── Response Helpers ────────────────────────────────────────────

    @staticmethod
    def is_approved(response: Dict[str, Any]) -> bool:
        """Check if the iVeri response indicates an approved transaction."""
        txn = response.get('Transaction', {})
        return (
            txn.get('ResultCode') == RESULT_CODE_SUCCESS
            and txn.get('Status') == STATUS_APPROVED
        )

    @staticmethod
    def is_pending(response: Dict[str, Any]) -> bool:
        """Check if the iVeri response indicates the transaction is still pending."""
        txn = response.get('Transaction', {})
        result_code = (txn.get('ResultCode') or '').strip()
        status = (txn.get('Status') or '').strip()

        # Standard explicit pending response.
        if result_code == RESULT_CODE_SUCCESS and status == STATUS_PENDING:
            return True

        # Some EcoCash debit responses return only TransactionIndex initially,
        # then require an out-of-band update/query for final status.
        if txn.get('TransactionIndex') and not status:
            return True

        # Defensive handling for alternative non-final status strings.
        if txn.get('TransactionIndex') and status.lower() in {'initiated', 'submitted', 'queued', 'processing'}:
            return True

        return False

    @staticmethod
    def is_3ds_required(response: Dict[str, Any]) -> bool:
        """Detect whether the response expects a 3DS browser challenge/redirect step."""
        txn = response.get('Transaction', {})
        three_ds = txn.get('ThreeDSecure') if isinstance(txn.get('ThreeDSecure'), dict) else {}

        # Gateways differ in naming; support common iVeri/3DS field variants.
        challenge_markers = (
            'ACSURL', 'ACSUrl', 'AcsUrl',
            'PaReq', 'PAREQ',
            'TermUrl', 'TermURL',
            'MD',
            'RedirectURL', 'RedirectUrl',
            'AuthenticationURL', 'AuthenticationUrl',
        )

        if any((txn.get(key) or '').strip() for key in challenge_markers):
            return True
        if any((three_ds.get(key) or '').strip() for key in challenge_markers):
            return True

        status = (txn.get('Status') or '').strip().lower()
        return status in {'3dsrequired', 'requires3ds', 'redirectshopper', 'challengerequired'}

    @staticmethod
    def get_3ds_challenge_data(response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract browser challenge data that should be returned to the frontend."""
        txn = response.get('Transaction', {})
        three_ds = txn.get('ThreeDSecure') if isinstance(txn.get('ThreeDSecure'), dict) else {}

        fields = (
            'ACSURL', 'ACSUrl', 'AcsUrl',
            'PaReq', 'PAREQ',
            'TermUrl', 'TermURL',
            'MD',
            'RedirectURL', 'RedirectUrl',
            'AuthenticationURL', 'AuthenticationUrl',
        )

        data: Dict[str, Any] = {}
        for key in fields:
            value = txn.get(key)
            if value:
                data[key] = value
        for key in fields:
            value = three_ds.get(key)
            if value and key not in data:
                data[key] = value

        if three_ds:
            data['ThreeDSecure'] = three_ds

        return data

    @staticmethod
    def get_result(response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key result fields from the iVeri response."""
        txn = response.get('Transaction', {})
        return {
            'result_code': txn.get('ResultCode'),
            'result_description': txn.get('ResultDescription', ''),
            'status': txn.get('Status'),
            'transaction_index': txn.get('TransactionIndex'),
            'authorisation_code': txn.get('AuthorisationCode'),
            'merchant_reference': txn.get('MerchantReference'),
            'amount': txn.get('Amount'),
            'currency': txn.get('Currency'),
            'request_id': txn.get('RequestID'),
        }


class IVeriCertificateClient:
    """SOAP client for the iVeri certificate lifecycle operations."""

    SOAP_ENV_NS = 'http://schemas.xmlsoap.org/soap/envelope/'

    def __init__(self, config: IVeriCertificateConfig):
        self.config = config
        self._validate_config()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'text/xml; charset=utf-8',
            'Accept': 'text/xml',
        })
        logger.info(
            "IVeriCertificateClient initialized | url=%s app=%s terminal=%s mode=%s",
            self.config.soap_url,
            _mask_value(self.config.application_id),
            _mask_value(self.config.terminal_id),
            self.config.mode,
        )

    def _validate_config(self) -> None:
        missing = []
        if not (self.config.soap_url or '').strip():
            missing.append('soap_url')
        if not (self.config.application_id or '').strip():
            missing.append('application_id')
        if not (self.config.soap_username or '').strip():
            missing.append('soap_username')
        if not (self.config.soap_password or '').strip():
            missing.append('soap_password')

        if missing:
            logger.error(
                "IVeriCertificateClient invalid configuration | missing=%s app=%s",
                ','.join(missing),
                _mask_value(self.config.application_id),
            )
            raise ValueError(
                "Incomplete iVeri certificate lifecycle configuration. Missing: "
                f"{', '.join(missing)}"
            )

    def _qualify(self, tag: str) -> str:
        if self.config.soap_namespace:
            return f"{{{self.config.soap_namespace}}}{tag}"
        return tag

    def _build_envelope(self, operation: str, params: Dict[str, Any]) -> bytes:
        envelope = ET.Element(f"{{{self.SOAP_ENV_NS}}}Envelope")
        body = ET.SubElement(envelope, f"{{{self.SOAP_ENV_NS}}}Body")
        operation_element = ET.SubElement(body, self._qualify(operation))

        merged_params: Dict[str, Any] = {
            'Username': self.config.soap_username,
            'Password': self.config.soap_password,
            'MerchantID': self.config.merchant_id,
            'ApplicationID': self.config.application_id,
            'TerminalID': self.config.terminal_id,
            'CertificateID': self.config.certificate_id,
            'Mode': self.config.mode,
        }
        merged_params.update(params)

        for key, value in merged_params.items():
            if value is None or value == '':
                continue
            child = ET.SubElement(operation_element, self._qualify(key))
            child.text = str(value)

        return ET.tostring(envelope, encoding='utf-8', xml_declaration=True)

    def _parse_response(self, response_text: str, operation: str) -> Dict[str, Any]:
        root = ET.fromstring(response_text)
        body = root.find(f"{{{self.SOAP_ENV_NS}}}Body")
        if body is None:
            raise ValueError('SOAP response did not contain a Body element')

        fault = body.find(f"{{{self.SOAP_ENV_NS}}}Fault")
        if fault is not None:
            fault_data = _flatten_xml(fault)
            raise ValueError(fault_data.get('faultstring') or fault_data.get('Reason') or 'SOAP fault returned')

        payload = next(iter(body), None)
        if payload is None:
            raise ValueError(f'SOAP {operation} response did not contain a payload')

        return _flatten_xml(payload)

    def _execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        envelope = self._build_envelope(operation, params)
        soap_action = self.config.soap_action_base.rstrip('/') if self.config.soap_action_base else ''
        headers = {
            'SOAPAction': f"{soap_action}/{operation}" if soap_action else operation,
        }

        logger.info(
            "iVeri certificate SOAP request | operation=%s app=%s terminal=%s has_cert=%s",
            operation,
            _mask_value(self.config.application_id),
            _mask_value(params.get('TerminalID') or self.config.terminal_id),
            bool(params.get('CertificateID') or self.config.certificate_id),
        )

        try:
            response = self.session.post(
                self.config.soap_url,
                data=envelope,
                headers=headers,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            parsed = self._parse_response(response.text, operation)
            logger.info("iVeri certificate SOAP response | operation=%s keys=%s", operation, sorted(parsed.keys()))
            return parsed
        except requests.exceptions.HTTPError as exc:
            body = exc.response.text[:500] if exc.response is not None else 'No response'
            status = exc.response.status_code if exc.response is not None else 'No status'
            logger.error(
                "iVeri certificate SOAP HTTP error | operation=%s status=%s body=%s",
                operation,
                status,
                body,
            )
            raise
        except requests.exceptions.Timeout:
            logger.error("iVeri certificate SOAP timeout | operation=%s timeout=%ss", operation, self.config.timeout)
            raise

    @staticmethod
    def _find_value(payload: Dict[str, Any], *keys: str) -> Optional[str]:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, dict):
                for nested_key in keys:
                    nested_value = value.get(nested_key)
                    if nested_value:
                        return nested_value
            if value:
                return value
        return None

    def generate_certificate_id(self, terminal_id: str = '') -> Dict[str, Any]:
        response = self._execute('GenerateCertificateID', {
            'TerminalID': terminal_id or self.config.terminal_id,
        })
        certificate_id = self._find_value(response, 'CertificateID', 'GenerateCertificateIDResult')
        if not certificate_id:
            raise ValueError('GenerateCertificateID did not return a CertificateID')
        return {
            'certificate_id': certificate_id,
            'raw': response,
        }

    def get_certificate(self, certificate_id: str = '') -> Dict[str, Any]:
        resolved_id = certificate_id or self.config.certificate_id
        if not resolved_id:
            raise ValueError('CertificateID is required to retrieve a certificate')
        response = self._execute('GetCertificate', {
            'CertificateID': resolved_id,
        })
        return {
            'certificate_id': resolved_id,
            'certificate': self._find_value(response, 'Certificate', 'PublicKey', 'GetCertificateResult'),
            'raw': response,
        }

    def submit_certificate(self, certificate_id: str = '', certificate_data: str = '', csr: str = '') -> Dict[str, Any]:
        resolved_id = certificate_id or self.config.certificate_id
        if not resolved_id:
            raise ValueError('CertificateID is required to submit a certificate')
        if not certificate_data and not csr:
            raise ValueError('certificate_data or csr is required to submit a certificate')
        response = self._execute('SubmitCertificate', {
            'CertificateID': resolved_id,
            'Certificate': certificate_data,
            'CSR': csr,
        })
        return {
            'certificate_id': resolved_id,
            'accepted': True,
            'raw': response,
        }

    def renew_certificate_id(self, certificate_id: str = '') -> Dict[str, Any]:
        resolved_id = certificate_id or self.config.certificate_id
        if not resolved_id:
            raise ValueError('CertificateID is required to renew a certificate')
        response = self._execute('RenewCertificateID', {
            'CertificateID': resolved_id,
        })
        renewed_id = self._find_value(response, 'CertificateID', 'RenewCertificateIDResult')
        if not renewed_id:
            raise ValueError('RenewCertificateID did not return a CertificateID')
        return {
            'certificate_id': renewed_id,
            'previous_certificate_id': resolved_id,
            'raw': response,
        }
