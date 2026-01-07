import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


logger = logging.getLogger(__name__)


@dataclass
class OmariConfig:
    """Configuration for Omari Merchant API v1.2.0."""
    base_url: str  # e.g., https://omari.v.co.zw/vsuite/omari/api/merchant/api/payment
    merchant_key: str  # API Key provided by O'mari


class OmariClient:
    """
    Client for Omari Merchant API v1.2.0.

    Flow:
    1. Call auth() to initiate transaction and get OTP reference
    2. Customer enters OTP received via SMS/Email
    3. Call request() with OTP to complete payment
    4. Optionally call query() to check transaction status
    """

    def __init__(self, config: Optional[OmariConfig] = None):
        """
        Initialize the client with configuration.
        If no config is provided, attempts to load from database.
        """
        if config is None:
            config = self._load_config_from_db()
        
        if config is None:
            raise ValueError(
                "No Omari configuration found. Please configure Omari credentials in the admin panel."
            )
        
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Merchant-Key': self.config.merchant_key,
        })
        
        # Log initialization (masked key)
        key_masked = f"***{self.config.merchant_key[-6:]}" if self.config.merchant_key else "<empty>"
        logger.info(
            "OmariClient initialized | url=%s merchant_key=%s",
            self.config.base_url,
            key_masked,
        )
    
    @staticmethod
    def _load_config_from_db() -> Optional[OmariConfig]:
        """Load active Omari configuration from database."""
        try:
            from .models import OmariConfig as OmariConfigModel
            
            config_model = OmariConfigModel.get_active_config()
            if config_model:
                return OmariConfig(
                    base_url=config_model.base_url,
                    merchant_key=config_model.merchant_key
                )
            else:
                logger.warning("No active Omari configuration found in database.")
                return None
        except Exception as e:
            logger.error(f"Error loading Omari config from database: {e}", exc_info=True)
            return None

    def auth(self, msisdn: str, reference: str, amount: float, currency: str, channel: str = 'WEB') -> Dict[str, Any]:
        """
        POST /auth - Initiate transaction and trigger OTP.

        Args:
            msisdn: Mobile number in 2637XXXXXXXX format
            reference: Unique UUID reference
            amount: Amount to charge
            currency: 'ZWG' or 'USD'
            channel: 'POS' or 'WEB' (default: WEB)

        Returns:
            {"error": bool, "message": str, "responseCode": str, "otpReference": str}
        """
        url = f"{self.config.base_url.rstrip('/')}/auth"
        payload = {
            'msisdn': msisdn,
            'reference': reference,
            'amount': amount,
            'currency': currency,
            'channel': channel,
        }
        logger.debug(f"Omari auth payload: {payload}")
        try:
            resp = self.session.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            logger.info("Omari auth success | responseCode=%s message=%s", data.get('responseCode'), data.get('message'))
            return data
        except requests.exceptions.HTTPError as e:
            # Capture response body for debugging 500 errors
            try:
                error_body = e.response.text if e.response else "No response"
                error_status = e.response.status_code if e.response else "No status"
                logger.error(
                    "Omari auth HTTP error | status=%s message=%s body=%s",
                    error_status,
                    str(e),
                    error_body[:300],  # First 300 chars of response
                )
            except Exception as log_err:
                logger.error("Omari auth error (failed to capture details): %s", str(log_err))
            raise
        except Exception as e:
            logger.error("Omari auth unexpected error: %s", str(e), exc_info=True)
            raise

    def request(self, msisdn: str, reference: str, otp: str) -> Dict[str, Any]:
        """
        POST /request - Validate OTP and complete payment.

        Args:
            msisdn: Mobile number in 2637XXXXXXXX format
            reference: Same UUID reference used in auth()
            otp: OTP entered by customer

        Returns:
            {"error": bool, "message": str, "responseCode": str, "paymentReference": str, "debitReference": str}
        """
        url = f"{self.config.base_url.rstrip('/')}/request"
        payload = {
            'msisdn': msisdn,
            'reference': reference,
            'otp': otp,
        }
        logger.debug(f"Omari request URL: {url}; payload={payload}")
        resp = self.session.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Omari request response: %s", data)
        return data

    def query(self, reference: str) -> Dict[str, Any]:
        """
        GET /query/{reference} - Check transaction status.

        Args:
            reference: UUID reference for the transaction

        Returns:
            {"error": bool, "message": str, "status": str, "responseCode": str,
             "reference": str, "amount": float, "currency": str, "channel": str,
             "paymentReference": str, "debitReference": str, "created": str}
        """
        url = f"{self.config.base_url.rstrip('/')}/query/{reference}"
        logger.debug(f"Omari query URL: {url}")
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Omari query response: %s", data)
        return data
