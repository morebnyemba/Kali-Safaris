"""
iVeri REST API client for CBZ payment gateway.

Handles communication with the iVeri Enterprise Gateway for both
EcoCash (mobile money) and Card (Visa/Mastercard) payments.

Flow:
  EcoCash: debit_ecocash() → STK Push sent to customer → response indicates success/failure
  Card:    debit_card() → immediate response (or 3DS redirect data for website)
"""
import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

import requests
from django.conf import settings

from .constants import (
    ECOCASH_DEFAULT_EXPIRY,
    ECOCASH_PAN_PREFIX,
    IVERI_API_VERSION,
    IVERI_REST_TRANSACTIONS,
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


@dataclass
class IVeriConfig:
    """Configuration for the iVeri REST API."""
    portal_url: str          # e.g., https://portal.host.iveri.com
    certificate_id: str      # CertificateID GUID
    application_id: str      # ApplicationID GUID
    mode: str = 'Test'       # 'Test' or 'LIVE'
    callback_url: str = ''   # Optional out-of-band notification URL


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
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        self.api_url = f"{self.config.portal_url.rstrip('/')}{IVERI_REST_TRANSACTIONS}"

        # Log initialization (masked credentials)
        cert_masked = f"***{self.config.certificate_id[-6:]}" if self.config.certificate_id else "<empty>"
        app_masked = f"***{self.config.application_id[-6:]}" if self.config.application_id else "<empty>"
        logger.info(
            "IVeriClient initialized | url=%s cert=%s app=%s mode=%s",
            self.api_url, cert_masked, app_masked, self.config.mode,
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
                    certificate_id=config_model.certificate_id,
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
                "iVeri HTTP error | status=%s body=%s",
                error_status, error_body,
            )
            raise
        except requests.exceptions.Timeout:
            logger.error("iVeri request timeout (60s)")
            raise
        except Exception as e:
            logger.error("iVeri unexpected error: %s", str(e), exc_info=True)
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
        status = (txn.get('Status') or '').strip()
        return (
            txn.get('ResultCode') == RESULT_CODE_SUCCESS
            and status == STATUS_PENDING
        )

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
