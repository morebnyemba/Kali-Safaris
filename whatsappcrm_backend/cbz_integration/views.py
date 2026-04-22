"""
API views for CBZ/iVeri payment integration.

Provides REST endpoints for:
- EcoCash payments (WhatsApp bot or direct API)
- Card payments (website checkout)
- Transaction status queries
- Out-of-band webhook callbacks from iVeri
"""
import json
import logging
import uuid

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional
from django.conf import settings
from django.http import JsonResponse, HttpRequest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction as db_transaction

from customer_data.models import Booking, Payment
from .models import CBZConfig, CBZTransaction
from .services import IVeriClient, IVeriCertificateClient, build_certificate_client_from_settings
from .constants import RESULT_CODE_SUCCESS, STATUS_APPROVED


logger = logging.getLogger(__name__)


def _build_client() -> IVeriClient:
    """Build iVeri client from database configuration."""
    return IVeriClient()


def _get_active_config() -> Optional[CBZConfig]:
    return CBZConfig.get_active_config()


def _build_certificate_client(config_model: Optional[CBZConfig] = None) -> IVeriCertificateClient:
    return build_certificate_client_from_settings(config_model or _get_active_config())


def _apply_gateway_result_to_transaction(
    txn: CBZTransaction,
    result: Dict[str, Any],
    *,
    approved: bool,
    pending: bool,
) -> None:
    """Persist gateway result fields and normalize local transaction status."""
    txn.result_code = result.get('result_code')
    txn.result_description = result.get('result_description')
    txn.transaction_index = result.get('transaction_index') or txn.transaction_index
    txn.authorisation_code = result.get('authorisation_code') or txn.authorisation_code
    txn.request_id = result.get('request_id') or txn.request_id

    if approved:
        txn.status = CBZTransaction.TransactionStatus.APPROVED
        txn.completed_at = timezone.now()
    elif pending:
        txn.status = CBZTransaction.TransactionStatus.PENDING
    elif txn.status != CBZTransaction.TransactionStatus.APPROVED:
        txn.status = CBZTransaction.TransactionStatus.DECLINED

    txn.save()


# ─── EcoCash API Endpoint ────────────────────────────────────────────


@csrf_exempt
@require_http_methods(["POST"])
def cbz_ecocash_debit_view(request: HttpRequest) -> JsonResponse:
    """
    POST /crm-api/payments/cbz/ecocash/debit/

    Initiates an EcoCash payment via iVeri STK Push.

    Request JSON:
    {
        "msisdn": "263774325309",
        "amount": 10.50,
        "currency": "USD",
        "booking_reference": "KS-ABC123"  // optional
    }

    Response (approved):
    {
        "success": true,
        "message": "Payment approved",
        "merchant_reference": "KS-XXXXXXXXXXXX",
        "transaction_index": "...",
        "authorisation_code": "..."
    }

    Response (pending):
    {
        "success": true,
        "pending": true,
        "message": "Payment initiated and awaiting final confirmation",
        "merchant_reference": "KS-XXXXXXXXXXXX"
    }

    Response (failure):
    {
        "success": false,
        "message": "Payment declined: Insufficient funds",
        "merchant_reference": "KS-XXXXXXXXXXXX",
        "result_code": "05"
    }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    # Validate required fields
    required = ["msisdn", "amount", "currency"]
    missing = [k for k in required if k not in payload]
    if missing:
        return JsonResponse(
            {"success": False, "message": f"Missing fields: {', '.join(missing)}"},
            status=400,
        )

    # Validate amount
    try:
        amount = Decimal(str(payload['amount']))
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (InvalidOperation, ValueError) as e:
        return JsonResponse(
            {"success": False, "message": f"Invalid amount: {str(e)}"},
            status=400,
        )

    merchant_ref = f"KS-{uuid.uuid4().hex[:12].upper()}"
    currency = payload['currency']
    msisdn = payload['msisdn']

    # Optionally link to booking
    booking = None
    booking_ref = payload.get('booking_reference')
    if booking_ref:
        try:
            booking = Booking.objects.get(booking_reference=booking_ref)
        except Booking.DoesNotExist:
            logger.warning(f"Booking {booking_ref} not found for CBZ payment")

    # Create transaction record
    txn = CBZTransaction.objects.create(
        merchant_reference=merchant_ref,
        payment_type=CBZTransaction.PaymentType.ECOCASH,
        msisdn=msisdn,
        amount=amount,
        currency=currency,
        command='Debit',
        status=CBZTransaction.TransactionStatus.INITIATED,
        booking=booking,
    )

    client = _build_client()
    try:
        response = client.debit_ecocash(
            mobile=msisdn,
            amount=amount,
            currency=currency,
            merchant_reference=merchant_ref,
        )

        result = IVeriClient.get_result(response)
        is_approved = IVeriClient.is_approved(response)
        is_pending = IVeriClient.is_pending(response)

        # Update transaction
        txn.result_code = result.get('result_code')
        txn.result_description = result.get('result_description')
        txn.transaction_index = result.get('transaction_index')
        txn.authorisation_code = result.get('authorisation_code')
        txn.request_id = result.get('request_id')

        if is_approved:
            txn.status = CBZTransaction.TransactionStatus.APPROVED
            txn.completed_at = timezone.now()
            txn.save()

            # Record payment on booking
            if booking:
                _record_payment(txn, booking)

            return JsonResponse({
                "success": True,
                "message": "Payment approved",
                "merchant_reference": merchant_ref,
                "transaction_index": result.get('transaction_index'),
                "authorisation_code": result.get('authorisation_code'),
            })
        elif is_pending:
            txn.status = CBZTransaction.TransactionStatus.PENDING
            txn.save()
            return JsonResponse({
                "success": True,
                "pending": True,
                "message": result.get(
                    'result_description',
                    'Payment initiated and awaiting final confirmation',
                ),
                "merchant_reference": merchant_ref,
                "result_code": result.get('result_code'),
            }, status=202)
        else:
            txn.status = CBZTransaction.TransactionStatus.DECLINED
            txn.save()
            return JsonResponse({
                "success": False,
                "message": result.get('result_description', 'Payment declined'),
                "merchant_reference": merchant_ref,
                "result_code": result.get('result_code'),
            })

    except Exception as e:
        logger.exception("CBZ EcoCash debit failed")
        txn.status = CBZTransaction.TransactionStatus.FAILED
        txn.result_description = str(e)[:500]
        txn.save()
        return JsonResponse(
            {"success": False, "message": str(e), "merchant_reference": merchant_ref},
            status=502,
        )


# ─── Card Payment API Endpoint (Website Only) ───────────────────────


@csrf_exempt
@require_http_methods(["POST"])
def cbz_card_debit_view(request: HttpRequest) -> JsonResponse:
    """
    POST /crm-api/payments/cbz/card/debit/

    Processes a card payment (Visa/Mastercard) via iVeri.
    This endpoint is intended for the public website checkout only.

    Request JSON:
    {
        "pan": "5413330089020020",
        "expiry_date": "0228",
        "cvv": "123",
        "amount": 150.00,
        "currency": "USD",
        "booking_reference": "KS-ABC123",
        "threed_secure_data": {}  // optional 3DS authentication data
    }

    Response (success):
    {
        "success": true,
        "message": "Payment approved",
        "merchant_reference": "KS-XXXXXXXXXXXX",
        "transaction_index": "...",
        "authorisation_code": "..."
    }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    # Validate required fields
    required = ["pan", "expiry_date", "cvv", "amount", "currency"]
    missing = [k for k in required if k not in payload]
    if missing:
        return JsonResponse(
            {"success": False, "message": f"Missing fields: {', '.join(missing)}"},
            status=400,
        )

    # Validate amount
    try:
        amount = Decimal(str(payload['amount']))
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (InvalidOperation, ValueError) as e:
        return JsonResponse(
            {"success": False, "message": f"Invalid amount: {str(e)}"},
            status=400,
        )

    merchant_ref = f"KS-{uuid.uuid4().hex[:12].upper()}"
    pan = payload['pan']
    masked_pan = f"{pan[:4]}****{pan[-4:]}" if len(pan) >= 8 else "****"

    # Link to booking if provided
    booking = None
    booking_ref = payload.get('booking_reference')
    if booking_ref:
        try:
            booking = Booking.objects.get(booking_reference=booking_ref)
        except Booking.DoesNotExist:
            logger.warning(f"Booking {booking_ref} not found for CBZ card payment")

    # Create transaction record (never store raw card number)
    txn = CBZTransaction.objects.create(
        merchant_reference=merchant_ref,
        payment_type=CBZTransaction.PaymentType.CARD,
        masked_pan=masked_pan,
        amount=amount,
        currency=payload['currency'],
        command='Debit',
        status=CBZTransaction.TransactionStatus.INITIATED,
        booking=booking,
    )

    client = _build_client()
    try:
        response = client.debit_card(
            pan=pan,
            expiry_date=payload['expiry_date'],
            cvv=payload['cvv'],
            amount=amount,
            currency=payload['currency'],
            merchant_reference=merchant_ref,
            threed_secure_data=payload.get('threed_secure_data'),
        )

        result = IVeriClient.get_result(response)
        is_approved = IVeriClient.is_approved(response)
        is_pending = IVeriClient.is_pending(response)
        is_3ds_required = IVeriClient.is_3ds_required(response)

        _apply_gateway_result_to_transaction(
            txn,
            result,
            approved=is_approved,
            pending=is_pending or is_3ds_required,
        )

        if is_approved:

            if booking:
                _record_payment(txn, booking)

            return JsonResponse({
                "success": True,
                "message": "Payment approved",
                "merchant_reference": merchant_ref,
                "transaction_index": result.get('transaction_index'),
                "authorisation_code": result.get('authorisation_code'),
            })
        elif is_3ds_required:
            return JsonResponse({
                "success": True,
                "requires_3ds": True,
                "pending": True,
                "message": result.get('result_description', '3DS authentication required'),
                "merchant_reference": merchant_ref,
                "result_code": result.get('result_code'),
                "transaction_index": result.get('transaction_index'),
                "challenge": IVeriClient.get_3ds_challenge_data(response),
                "next_step": {
                    "complete_url": "/crm-api/payments/cbz/card/3ds/complete/",
                    "query_url": f"/crm-api/payments/cbz/query/{merchant_ref}/",
                },
            }, status=202)
        elif is_pending:
            return JsonResponse({
                "success": True,
                "pending": True,
                "message": result.get('result_description', 'Payment initiated and awaiting final confirmation'),
                "merchant_reference": merchant_ref,
                "result_code": result.get('result_code'),
                "transaction_index": result.get('transaction_index'),
            }, status=202)
        else:
            return JsonResponse({
                "success": False,
                "message": result.get('result_description', 'Payment declined'),
                "merchant_reference": merchant_ref,
                "result_code": result.get('result_code'),
            })

    except Exception as e:
        logger.exception("CBZ card debit failed")
        txn.status = CBZTransaction.TransactionStatus.FAILED
        txn.result_description = str(e)[:500]
        txn.save()
        return JsonResponse(
            {"success": False, "message": str(e), "merchant_reference": merchant_ref},
            status=502,
        )


@csrf_exempt
@require_http_methods(["POST"])
def cbz_card_3ds_complete_view(request: HttpRequest) -> JsonResponse:
    """
    POST /crm-api/payments/cbz/card/3ds/complete/

    Finalizes a card payment after 3DS browser flow by reconciling the
    transaction status from iVeri using merchant reference.

    Request JSON:
    {
        "merchant_reference": "KS-XXXXXXXXXXXX"
    }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    merchant_reference = (payload.get('merchant_reference') or '').strip()
    if not merchant_reference:
        return JsonResponse({"success": False, "message": "Missing field: merchant_reference"}, status=400)

    txn = CBZTransaction.objects.filter(
        merchant_reference=merchant_reference,
        payment_type=CBZTransaction.PaymentType.CARD,
    ).first()
    if not txn:
        return JsonResponse({"success": False, "message": "Transaction not found"}, status=404)

    client = _build_client()
    try:
        response = client.query_transaction(merchant_reference=merchant_reference)
        result = IVeriClient.get_result(response)
        is_approved = IVeriClient.is_approved(response)
        is_pending = IVeriClient.is_pending(response)

        _apply_gateway_result_to_transaction(
            txn,
            result,
            approved=is_approved,
            pending=is_pending,
        )

        if is_approved and txn.booking:
            existing_payment = Payment.objects.filter(
                booking=txn.booking,
                transaction_reference=txn.merchant_reference,
            ).exists()
            if not existing_payment:
                _record_payment(txn, txn.booking)

        if is_approved:
            return JsonResponse({
                "success": True,
                "message": "Payment approved",
                "merchant_reference": merchant_reference,
                "transaction_index": result.get('transaction_index'),
                "authorisation_code": result.get('authorisation_code'),
            })

        if is_pending:
            return JsonResponse({
                "success": True,
                "pending": True,
                "message": result.get('result_description', 'Payment still pending'),
                "merchant_reference": merchant_reference,
                "result_code": result.get('result_code'),
            }, status=202)

        return JsonResponse({
            "success": False,
            "message": result.get('result_description', 'Payment declined'),
            "merchant_reference": merchant_reference,
            "result_code": result.get('result_code'),
        })
    except Exception as e:
        logger.exception("CBZ card 3DS completion failed")
        return JsonResponse({"success": False, "message": str(e)}, status=502)


# ─── Transaction Query ──────────────────────────────────────────────


@require_http_methods(["GET"])
def cbz_query_view(request: HttpRequest, reference: str) -> JsonResponse:
    """
    GET /crm-api/payments/cbz/query/<reference>/

    Checks iVeri transaction status by merchant reference.
    """
    client = _build_client()
    try:
        response = client.query_transaction(merchant_reference=reference)
        result = IVeriClient.get_result(response)
        return JsonResponse({
            "success": True,
            "is_approved": IVeriClient.is_approved(response),
            "is_pending": IVeriClient.is_pending(response),
            "data": result,
        })
    except Exception as e:
        logger.exception("CBZ query failed")
        return JsonResponse({"success": False, "message": str(e)}, status=502)


# ─── Out-of-Band Callback ───────────────────────────────────────────


@csrf_exempt
@require_http_methods(["POST"])
def cbz_callback_view(request: HttpRequest) -> JsonResponse:
    """
    POST /crm-api/payments/cbz/callback/

    Receives out-of-band transaction notifications from iVeri.
    iVeri sends these for async transaction results (e.g., EcoCash delayed approval).
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        logger.warning("CBZ callback: invalid JSON received")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    logger.info("CBZ callback received: %s", json.dumps(payload, indent=2)[:500])

    txn_data = payload.get('Transaction', {})
    merchant_ref = txn_data.get('MerchantReference')

    if not merchant_ref:
        logger.warning("CBZ callback: no MerchantReference in payload")
        return JsonResponse({"error": "Missing MerchantReference"}, status=400)

    # Find the transaction
    txn = CBZTransaction.objects.filter(merchant_reference=merchant_ref).first()
    if not txn:
        logger.warning(f"CBZ callback: transaction {merchant_ref} not found")
        return JsonResponse({"error": "Transaction not found"}, status=404)

    # Update transaction with callback data
    result_code = txn_data.get('ResultCode')
    status_text = txn_data.get('Status')

    txn.result_code = result_code
    txn.result_description = txn_data.get('ResultDescription', '')
    txn.transaction_index = txn_data.get('TransactionIndex') or txn.transaction_index
    txn.authorisation_code = txn_data.get('AuthorisationCode') or txn.authorisation_code

    if result_code == RESULT_CODE_SUCCESS and status_text == STATUS_APPROVED:
        if txn.status != CBZTransaction.TransactionStatus.APPROVED:
            txn.status = CBZTransaction.TransactionStatus.APPROVED
            txn.completed_at = timezone.now()
            txn.save()

            # Record the payment
            if txn.booking:
                _record_payment(txn, txn.booking)

            logger.info(f"CBZ callback: transaction {merchant_ref} APPROVED via callback")
        else:
            txn.save()
            logger.info(f"CBZ callback: transaction {merchant_ref} already approved, skipping")
    else:
        if txn.status in {
            CBZTransaction.TransactionStatus.INITIATED,
            CBZTransaction.TransactionStatus.PENDING,
        }:
            txn.status = CBZTransaction.TransactionStatus.DECLINED
        txn.save()
        logger.info(f"CBZ callback: transaction {merchant_ref} status={status_text} code={result_code}")

    return JsonResponse({"message": "OK"})


@csrf_exempt
@require_http_methods(["POST"])
def cbz_certificate_generate_view(request: HttpRequest) -> JsonResponse:
    """Generate a new CertificateID through the iVeri SOAP lifecycle."""
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    config_model = _get_active_config()
    client = _build_certificate_client(config_model)
    try:
        result = client.generate_certificate_id(terminal_id=payload.get('terminal_id', ''))
        if config_model:
            config_model.certificate_id = result['certificate_id']
            config_model.save(update_fields=['certificate_id', 'updated_at'])
        logger.info("CBZ certificate generated | cert=%s", result['certificate_id'])
        return JsonResponse({
            "success": True,
            "certificate_id": result['certificate_id'],
            "data": result['raw'],
        })
    except Exception as exc:
        logger.exception("CBZ certificate generation failed")
        return JsonResponse({"success": False, "message": str(exc)}, status=502)


@require_http_methods(["GET"])
def cbz_certificate_get_view(request: HttpRequest) -> JsonResponse:
    """Retrieve the current certificate content from the iVeri SOAP lifecycle."""
    config_model = _get_active_config()
    certificate_id = request.GET.get('certificate_id') or (config_model.certificate_id if config_model else '')
    client = _build_certificate_client(config_model)
    try:
        result = client.get_certificate(certificate_id=certificate_id)
        return JsonResponse({
            "success": True,
            "certificate_id": result['certificate_id'],
            "certificate": result['certificate'],
            "data": result['raw'],
        })
    except Exception as exc:
        logger.exception("CBZ certificate retrieval failed")
        return JsonResponse({"success": False, "message": str(exc)}, status=502)


@csrf_exempt
@require_http_methods(["POST"])
def cbz_certificate_submit_view(request: HttpRequest) -> JsonResponse:
    """Submit a device certificate or CSR back to iVeri."""
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    config_model = _get_active_config()
    client = _build_certificate_client(config_model)
    try:
        result = client.submit_certificate(
            certificate_id=payload.get('certificate_id', ''),
            certificate_data=payload.get('certificate', ''),
            csr=payload.get('csr', ''),
        )
        logger.info("CBZ certificate submitted | cert=%s", result['certificate_id'])
        return JsonResponse({
            "success": True,
            "certificate_id": result['certificate_id'],
            "data": result['raw'],
        })
    except Exception as exc:
        logger.exception("CBZ certificate submission failed")
        return JsonResponse({"success": False, "message": str(exc)}, status=502)


@csrf_exempt
@require_http_methods(["POST"])
def cbz_certificate_renew_view(request: HttpRequest) -> JsonResponse:
    """Renew the current CertificateID through the iVeri SOAP lifecycle."""
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    config_model = _get_active_config()
    client = _build_certificate_client(config_model)
    try:
        result = client.renew_certificate_id(certificate_id=payload.get('certificate_id', ''))
        if config_model:
            config_model.certificate_id = result['certificate_id']
            config_model.save(update_fields=['certificate_id', 'updated_at'])
        logger.info(
            "CBZ certificate renewed | previous=%s current=%s",
            result['previous_certificate_id'],
            result['certificate_id'],
        )
        return JsonResponse({
            "success": True,
            "certificate_id": result['certificate_id'],
            "previous_certificate_id": result['previous_certificate_id'],
            "data": result['raw'],
        })
    except Exception as exc:
        logger.exception("CBZ certificate renewal failed")
        return JsonResponse({"success": False, "message": str(exc)}, status=502)


# ─── Helper Functions ────────────────────────────────────────────────


def _record_payment(txn: CBZTransaction, booking: Booking):
    """Create Payment record and update booking after successful transaction."""
    try:
        with db_transaction.atomic():
            Payment.objects.create(
                booking=booking,
                amount=txn.amount,
                currency=txn.currency,
                status=Payment.PaymentStatus.SUCCESSFUL,
                payment_method=(
                    Payment.PaymentMethod.CBZ_ECOCASH
                    if txn.payment_type == CBZTransaction.PaymentType.ECOCASH
                    else Payment.PaymentMethod.CBZ_CARD
                ),
                transaction_reference=txn.merchant_reference,
                notes=f"CBZ/iVeri {txn.get_payment_type_display()} payment. Auth: {txn.authorisation_code or 'N/A'}",
            )

            booking = Booking.objects.select_for_update().get(id=booking.id)
            booking.update_amount_paid(commit=False)

            if booking.amount_paid >= booking.total_amount:
                booking.payment_status = Booking.PaymentStatus.PAID
            elif booking.amount_paid > 0:
                booking.payment_status = Booking.PaymentStatus.DEPOSIT_PAID

            booking.save(update_fields=['amount_paid', 'payment_status', 'updated_at'])

            logger.info(
                "Payment recorded | booking=%s txn=%s amount=%s %s",
                booking.booking_reference, txn.merchant_reference,
                txn.amount, txn.currency,
            )
    except Exception as e:
        logger.error(
            "Failed to record payment | txn=%s error=%s",
            txn.merchant_reference, str(e), exc_info=True,
        )
