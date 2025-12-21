import json
import logging
from dataclasses import dataclass
from typing import Any, Dict

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

    def __init__(self, config: OmariConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Merchant-Key': self.config.merchant_key,
        })

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
        logger.debug(f"Omari auth URL: {url}; payload={payload}")
        resp = self.session.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Omari auth response: %s", data)
        return data

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
