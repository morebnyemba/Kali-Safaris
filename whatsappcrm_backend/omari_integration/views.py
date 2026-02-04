import json
import logging
import uuid
from django.utils import timezone

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction as db_transaction

from .services import OmariClient
from .models import OmariTransaction
from customer_data.models import Booking, Payment


logger = logging.getLogger(__name__)


def _build_client() -> OmariClient:
    """Build Omari client from database configuration."""
    return OmariClient()


@csrf_exempt
@require_http_methods(["POST"])
def omari_auth_view(request: HttpRequest) -> JsonResponse:
    """
    POST /crm-api/payments/omari/auth/

    Initiates Omari transaction and triggers OTP.

    Request JSON:
    {
      "msisdn": "263774975187",
      "reference": "<UUID>",  # optional, will be generated if missing
      "amount": 3.50,
      "currency": "USD",
      "channel": "WEB"  # optional, defaults to WEB
    }

    Response:
    {
      "error": false,
      "message": "Auth Success",
      "responseCode": "000",
      "otpReference": "ETDC",
      "reference": "<UUID>"  # echoed back for client tracking
    }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": True, "message": "Invalid JSON"}, status=400)

    # Validate required fields
    required = ["msisdn", "amount", "currency"]
    missing = [k for k in required if k not in payload]
    if missing:
        return JsonResponse({"error": True, "message": f"Missing fields: {', '.join(missing)}"}, status=400)

    # Generate reference if not provided
    reference = payload.get('reference') or str(uuid.uuid4())
    channel = payload.get('channel', 'WEB')

    client = _build_client()
    try:
        result = client.auth(
            msisdn=payload['msisdn'],
            reference=reference,
            amount=payload['amount'],
            currency=payload['currency'],
            channel=channel,
        )
        # Create transaction record
        OmariTransaction.objects.create(
            reference=reference,
            msisdn=payload['msisdn'],
            amount=payload['amount'],
            currency=payload['currency'],
            channel=channel,
            otp_reference=result.get('otpReference'),
            status='OTP_SENT' if not result.get('error') else 'FAILED',
            response_code=result.get('responseCode'),
            response_message=result.get('message'),
        )
        # Add reference to response for client tracking
        result['reference'] = reference
        return JsonResponse(result, status=200)
    except Exception as e:
        logger.exception("Failed to initiate Omari auth")
        # Log failed transaction
        OmariTransaction.objects.create(
            reference=reference,
            msisdn=payload['msisdn'],
            amount=payload['amount'],
            currency=payload['currency'],
            channel=channel,
            status='FAILED',
            response_message=str(e),
        )
        return JsonResponse({"error": True, "message": str(e)}, status=502)


@csrf_exempt
@require_http_methods(["POST"])
def omari_request_view(request: HttpRequest) -> JsonResponse:
    """
    POST /crm-api/payments/omari/request/

    Validates OTP and completes Omari payment.

    Request JSON:
    {
      "msisdn": "263774975187",
      "reference": "<UUID>",
      "otp": "836066"
    }

    Response:
    {
      "error": false,
      "message": "Payment Success",
      "responseCode": "000",
      "paymentReference": "H5PSKURANNR1LKS7AJ0KV50KZG",
      "debitReference": "bc54b38257cf"
    }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": True, "message": "Invalid JSON"}, status=400)

    required = ["msisdn", "reference", "otp"]
    missing = [k for k in required if k not in payload]
    if missing:
        return JsonResponse({"error": True, "message": f"Missing fields: {', '.join(missing)}"}, status=400)

    client = _build_client()
    try:
        result = client.request(
            msisdn=payload['msisdn'],
            reference=payload['reference'],
            otp=payload['otp'],
        )
        # Update transaction record
        txn = OmariTransaction.objects.filter(reference=payload['reference']).first()
        if txn:
            txn.payment_reference = result.get('paymentReference')
            txn.debit_reference = result.get('debitReference')
            txn.response_code = result.get('responseCode')
            txn.response_message = result.get('message')
            if not result.get('error') and result.get('responseCode') == '000':
                txn.status = 'SUCCESS'
                txn.completed_at = timezone.now()
                
                # Update booking and create Payment record when payment succeeds
                if txn.booking:
                    with db_transaction.atomic():
                        booking = Booking.objects.select_for_update().get(id=txn.booking.id)
                        
                        # Create Payment record for this Omari transaction
                        payment = Payment.objects.create(
                            booking=booking,
                            amount=txn.amount,
                            currency=txn.currency,
                            status=Payment.PaymentStatus.SUCCESSFUL,
                            payment_method=Payment.PaymentMethod.OMARI,
                            transaction_reference=result.get('paymentReference', txn.reference),
                            notes=f"Omari payment via API. Debit Ref: {result.get('debitReference', 'N/A')}"
                        )
                        
                        # Booking's amount_paid is automatically updated via Payment.save()
                        # which calls booking.update_amount_paid()
                        
                        # Update payment status based on amount
                        booking.refresh_from_db()
                        if booking.amount_paid >= booking.total_amount:
                            booking.payment_status = Booking.PaymentStatus.PAID
                        elif booking.amount_paid > 0:
                            booking.payment_status = Booking.PaymentStatus.DEPOSIT_PAID
                        
                        booking.save(update_fields=['payment_status', 'updated_at'])
                        
                        logger.info(
                            "Created Payment record and updated booking | booking=%s payment_id=%s amount=%s status=%s",
                            booking.booking_reference,
                            payment.id,
                            txn.amount,
                            booking.payment_status
                        )
            else:
                txn.status = 'FAILED'
            txn.save()
        return JsonResponse(result, status=200)
    except Exception as e:
        logger.exception("Failed to complete Omari payment request")
        # Mark transaction as failed
        txn = OmariTransaction.objects.filter(reference=payload['reference']).first()
        if txn:
            txn.status = 'FAILED'
            txn.response_message = str(e)
            txn.save()
        return JsonResponse({"error": True, "message": str(e)}, status=502)


@require_http_methods(["GET"])
def omari_query_view(request: HttpRequest, reference: str) -> JsonResponse:
    """
    GET /crm-api/payments/omari/query/<reference>/

    Checks Omari transaction status.

    Response:
    {
      "error": false,
      "message": "Success",
      "status": "Success",
      "responseCode": "000",
      "reference": "<UUID>",
      "amount": 3.50,
      "currency": "USD",
      "channel": "WEB",
      "paymentReference": "H5PSKURANNR1LKS7AJ0KV50KZG",
      "debitReference": "bc54b38257cf",
      "created": "2024-09-20T16:27:40"
    }
    """
    client = _build_client()
    try:
        result = client.query(reference=reference)
        return JsonResponse(result, status=200)
    except Exception as e:
        logger.exception("Failed to query Omari transaction")
        return JsonResponse({"error": True, "message": str(e)}, status=502)


@csrf_exempt
@require_http_methods(["POST"])
def omari_void_view(request: HttpRequest) -> JsonResponse:
    """
    POST /crm-api/payments/omari/void/

    Cancels/voids a pending Omari transaction.

    Request JSON:
    {
      "reference": "<UUID>"
    }

    Response:
    {
      "error": false,
      "message": "Transaction voided successfully",
      "responseCode": "000"
    }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning(f"Invalid JSON in void request: {e}")
        return JsonResponse({"error": True, "message": "Invalid JSON"}, status=400)

    if 'reference' not in payload:
        return JsonResponse({"error": True, "message": "Missing field: reference"}, status=400)

    client = _build_client()
    try:
        result = client.void(reference=payload['reference'])
        # Update transaction record atomically
        OmariTransaction.objects.filter(reference=payload['reference']).update(
            status='VOIDED',
            response_code=result.get('responseCode'),
            response_message=result.get('message')
        )
        return JsonResponse(result, status=200)
    except Exception as e:
        logger.exception("Failed to void Omari transaction")
        return JsonResponse({"error": True, "message": str(e)}, status=502)
