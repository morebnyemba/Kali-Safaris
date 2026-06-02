"""
Unified Payment Gateway Strategy

Provides a PaymentProcessor abstract interface and a PaymentGatewayFactory that
resolves the correct concrete gateway implementation by type key.

Usage:
    gateway = PaymentGatewayFactory.get_gateway("IVERI")
    result  = gateway.initiate_payment(...)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ─── Abstract Interface ───────────────────────────────────────────────


class PaymentProcessor(ABC):
    """
    Abstract base class that every payment gateway adapter must implement.

    Each method returns a normalised result dict so callers stay decoupled from
    gateway-specific response formats.
    """

    @abstractmethod
    def initiate_payment(
        self,
        *,
        amount: Decimal,
        currency: str,
        merchant_reference: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Initiate a new payment.

        Returns:
            {
                "success": bool,
                "pending": bool,
                "result_code": str | None,
                "result_description": str | None,
                "transaction_index": str | None,
                "authorisation_code": str | None,
                "raw": dict,  # full gateway response (PCI-scrubbed if applicable)
            }
        """

    @abstractmethod
    def verify_payment(self, *, merchant_reference: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Query the gateway for the current status of an existing transaction.

        Returns same shape as initiate_payment.
        """

    @abstractmethod
    def handle_callback(self, *, payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Process an inbound webhook / callback notification.

        Returns:
            {
                "merchant_reference": str,
                "status": "approved" | "pending" | "declined" | "retriable_error",
                "result_code": str | None,
                "raw": dict,
            }
        """

    @abstractmethod
    def refund(
        self,
        *,
        merchant_reference: str,
        amount: Decimal,
        currency: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Initiate a refund for a previously approved transaction.

        Returns:
            {"success": bool, "message": str, "raw": dict}
        """


# ─── iVeri / CBZ Concrete Implementation ─────────────────────────────


class IVeriGateway(PaymentProcessor):
    """
    PaymentProcessor adapter for the iVeri Enterprise REST Gateway.

    Thin wrapper around IVeriClient — it translates the raw service responses
    into the normalised dict format defined by the PaymentProcessor interface.
    """

    def __init__(self) -> None:
        # Import here to avoid circular imports; views also import services.
        from .services import IVeriClient, build_certificate_client_from_settings
        from .models import CBZConfig

        self._client_class = IVeriClient
        self._build_client = build_certificate_client_from_settings
        self._config_model = CBZConfig

    def _get_client(self) -> Any:
        config = self._config_model.objects.filter(is_active=True).first()
        if not config:
            raise RuntimeError("No active CBZConfig — iVeri gateway is not configured")
        return self._build_client(config)

    # ── normalise ────────────────────────────────────────────────────

    @staticmethod
    def _normalise(response: Dict[str, Any], *, raw: Dict[str, Any]) -> Dict[str, Any]:
        from .services import IVeriClient
        result = IVeriClient.get_result(response)
        return {
            "success": IVeriClient.is_approved(response),
            "pending": IVeriClient.is_pending(response),
            "result_code": result.get("result_code"),
            "status_label": result.get("status_label"),
            "is_retriable": result.get("is_retriable", False),
            "result_description": result.get("result_description"),
            "transaction_index": result.get("transaction_index"),
            "authorisation_code": result.get("authorisation_code"),
            "bank_reference": result.get("bank_reference"),
            "consumer_order_id": result.get("consumer_order_id"),
            "card_bin": result.get("card_bin"),
            "raw": raw,
        }

    # ── interface methods ─────────────────────────────────────────────

    def initiate_payment(
        self,
        *,
        amount: Decimal,
        currency: str,
        merchant_reference: str,
        payment_type: str = "card",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Initiate an iVeri payment.

        Pass payment_type="ecocash" for EcoCash STK push, or "card" (default)
        for Visa/Mastercard direct debit.

        EcoCash extra kwargs: mobile (str)
        Card extra kwargs:    pan, expiry_date, cvv, threed_secure_data
        """
        client = self._get_client()
        logger.info(
            "iVeri initiate_payment",
            extra={
                "merchant_reference": merchant_reference,
                "amount": str(amount),
                "currency": currency,
                "payment_type": payment_type,
            },
        )
        if payment_type.lower() == "ecocash":
            response = client.debit_ecocash(
                mobile=kwargs["mobile"],
                amount=amount,
                currency=currency,
                merchant_reference=merchant_reference,
            )
        else:
            response = client.debit_card(
                pan=kwargs["pan"],
                expiry_date=kwargs["expiry_date"],
                cvv=kwargs["cvv"],
                amount=amount,
                currency=currency,
                merchant_reference=merchant_reference,
                threed_secure_data=kwargs.get("threed_secure_data"),
            )
        return self._normalise(response, raw=response)

    def verify_payment(self, *, merchant_reference: str, **kwargs: Any) -> Dict[str, Any]:
        """Query iVeri for the current transaction status."""
        client = self._get_client()
        logger.info("iVeri verify_payment | ref=%s", merchant_reference)
        response = client.query_transaction(merchant_reference=merchant_reference)
        return self._normalise(response, raw=response)

    def handle_callback(self, *, payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Normalise an iVeri out-of-band callback notification.

        Does NOT persist anything — persistence is handled in the view layer
        (cbz_callback_view) which already owns the CBZTransaction record.
        """
        from .constants import IVERI_STATUS_MAP, IVERI_RETRIABLE_CODES, RESULT_CODE_SUCCESS
        txn_data = payload.get("Transaction", {})
        result_code = str(txn_data.get("ResultCode") or "")
        status_label = IVERI_STATUS_MAP.get(result_code, "UNKNOWN")

        if status_label == "SUCCESS":
            status = "approved"
        elif result_code in IVERI_RETRIABLE_CODES:
            status = "retriable_error"
        else:
            status = "declined"

        return {
            "merchant_reference": txn_data.get("MerchantReference"),
            "status": status,
            "status_label": status_label,
            "result_code": result_code,
            "result_description": txn_data.get("ResultDescription"),
            "raw": payload,
        }

    def refund(
        self,
        *,
        merchant_reference: str,
        amount: Decimal,
        currency: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Initiate an iVeri refund."""
        client = self._get_client()
        logger.info(
            "iVeri refund | ref=%s amount=%s %s",
            merchant_reference, amount, currency,
        )
        try:
            response = client.refund(
                merchant_reference=merchant_reference,
                amount=amount,
                currency=currency,
            )
            normalised = self._normalise(response, raw=response)
            return {
                "success": normalised["success"],
                "message": normalised.get("result_description") or "Refund processed",
                "raw": response,
            }
        except Exception as exc:
            logger.exception("iVeri refund failed | ref=%s", merchant_reference)
            return {"success": False, "message": str(exc), "raw": {}}


# ─── Factory ──────────────────────────────────────────────────────────


class PaymentGatewayFactory:
    """
    Registry-based factory for PaymentProcessor implementations.

    Register a gateway:
        PaymentGatewayFactory.register("MY_GATEWAY", MyGatewayClass)

    Retrieve a gateway:
        gateway = PaymentGatewayFactory.get_gateway("IVERI")
        result  = gateway.initiate_payment(...)
    """

    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, key: str, gateway_class: type) -> None:
        """Register a gateway class under a normalised uppercase key."""
        if not issubclass(gateway_class, PaymentProcessor):
            raise TypeError(f"{gateway_class} must subclass PaymentProcessor")
        cls._registry[key.upper()] = gateway_class
        logger.debug("PaymentGatewayFactory registered: %s → %s", key.upper(), gateway_class.__name__)

    @classmethod
    def get_gateway(cls, key: str) -> PaymentProcessor:
        """
        Return a fresh instance of the gateway registered under *key*.

        Raises:
            KeyError: if no gateway is registered for the given key.
        """
        normalised = key.upper()
        gateway_class = cls._registry.get(normalised)
        if gateway_class is None:
            available = ', '.join(cls._registry.keys()) or 'none'
            raise KeyError(
                f"No payment gateway registered for '{normalised}'. "
                f"Available: {available}"
            )
        return gateway_class()

    @classmethod
    def available_gateways(cls) -> list[str]:
        """Return a sorted list of all registered gateway keys."""
        return sorted(cls._registry.keys())


# ─── Default Registrations ────────────────────────────────────────────

PaymentGatewayFactory.register("IVERI", IVeriGateway)
PaymentGatewayFactory.register("CBZ", IVeriGateway)      # alias
PaymentGatewayFactory.register("CBZ_CARD", IVeriGateway)
PaymentGatewayFactory.register("CBZ_ECOCASH", IVeriGateway)
