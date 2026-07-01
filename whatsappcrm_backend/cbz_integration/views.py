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
import os
import re
import base64
import binascii
import mimetypes
from datetime import date
from urllib.parse import parse_qs, urlparse, urlunparse, urlencode, quote

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional
import requests
from django.conf import settings
from django.core import signing
from django.http import JsonResponse, HttpRequest, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction as db_transaction
from django.core.files.base import ContentFile

from customer_data.models import Booking, Payment, Traveler, CustomerProfile
from conversations.models import Contact
from products_and_services.models import Tour
from .models import CBZConfig, CBZTransaction
from .services import IVeriClient, IVeriCertificateClient, build_certificate_client_from_settings
from .constants import RESULT_CODE_SUCCESS, STATUS_APPROVED, IVERI_STATUS_MAP, IVERI_RETRIABLE_CODES


logger = logging.getLogger(__name__)


def _save_traveler_document_from_data_url(
    traveler_obj: Traveler,
    data_url: str,
    fallback_name: str = '',
    declared_mime: str = '',
) -> None:
    """Decode a data URL and attach it to traveler.id_document if valid."""
    if not data_url or not isinstance(data_url, str):
        return
    if not data_url.startswith('data:') or ';base64,' not in data_url:
        return

    header, encoded = data_url.split(';base64,', 1)
    mime_type = header.replace('data:', '').strip().lower()
    if declared_mime:
        mime_type = str(declared_mime).strip().lower() or mime_type

    allowed_mimes = {'image/jpeg', 'image/png', 'application/pdf'}
    if mime_type not in allowed_mimes:
        return

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return

    if not raw or len(raw) > 5 * 1024 * 1024:
        return

    extension = mimetypes.guess_extension(mime_type) or ''
    if extension == '.jpe':
        extension = '.jpg'

    base_name = str(fallback_name or '').strip()
    if '.' in base_name:
        base_name = base_name.rsplit('.', 1)[0]
    if not base_name:
        base_name = f"traveler-{traveler_obj.id}"

    file_name = f"{base_name[:80]}{extension}"
    traveler_obj.id_document.save(file_name, ContentFile(raw), save=False)


def _build_client() -> IVeriClient:
    """Build iVeri client from database configuration."""
    return IVeriClient()


def _get_active_config() -> Optional[CBZConfig]:
    return CBZConfig.get_active_config()


def _get_public_payment_config() -> Dict[str, Any]:
    """Return non-sensitive payment config for frontend checkout flows."""
    config = _get_active_config()
    mode = config.mode if config else 'Test'

    raw_test_msisdns = getattr(settings, 'CBZ_TEST_ECOCASH_MSISDNS', '') or os.getenv('CBZ_TEST_ECOCASH_MSISDNS', '')
    test_msisdns = [item.strip() for item in raw_test_msisdns.split(',') if item.strip()]

    raw_test_card_pans = getattr(settings, 'CBZ_TEST_CARD_PANS', '') or os.getenv('CBZ_TEST_CARD_PANS', '')
    test_card_pans = [item.strip() for item in raw_test_card_pans.split(',') if item.strip()]
    # Fall back to the iVeri-documented test PAN when in Test mode and none configured
    if not test_card_pans and mode == 'Test':
        test_card_pans = ['5413330089020020']

    copyandpay_config = _get_copyandpay_config()
    copyandpay_entity_id = copyandpay_config.get('entity_id', '')
    copyandpay_base_url = copyandpay_config.get('base_url', '')
    copyandpay_brands = copyandpay_config.get('brands', '')

    return {
        'mode': mode,
        'ecocash': {
            'accepted_formats': ['2637XXXXXXXX', '07XXXXXXXX'],
            'test_msisdns': test_msisdns,
        },
        'card': {
            'supports_3ds': True,
            'test_pans': test_card_pans,
            'default_provider': 'copyandpay' if copyandpay_entity_id else 'cbz_direct',
            'providers': {
                'copyandpay_enabled': bool(copyandpay_entity_id),
                'cbz_direct_enabled': True,
            },
            'copyandpay': {
                'enabled': bool(copyandpay_entity_id),
                'base_url': copyandpay_base_url,
                'brands': copyandpay_brands or 'PRIVATE_LABEL',
            },
        },
    }


def _get_copyandpay_config() -> Dict[str, str]:
    config = _get_active_config()
    mode = config.mode if config else getattr(settings, 'CBZ_MODE', 'Test')

    base_url = (
        (getattr(config, 'copyandpay_base_url', '') if config else '')
        or getattr(settings, 'COPYANDPAY_BASE_URL', '')
        or os.getenv('COPYANDPAY_BASE_URL', '')
    ).strip()
    if not base_url:
        base_url = 'https://eu-test.oppwa.com' if mode == 'Test' else 'https://eu-prod.oppwa.com'

    return {
        'mode': mode,
        'base_url': base_url.rstrip('/'),
        'entity_id': (
            (getattr(config, 'copyandpay_entity_id', '') if config else '')
            or getattr(settings, 'COPYANDPAY_ENTITY_ID', '')
            or os.getenv('COPYANDPAY_ENTITY_ID', '')
        ).strip(),
        'bearer_token': (
            (getattr(config, 'copyandpay_bearer_token', '') if config else '')
            or getattr(settings, 'COPYANDPAY_BEARER_TOKEN', '')
            or os.getenv('COPYANDPAY_BEARER_TOKEN', '')
        ).strip(),
        'test_mode': (
            (
                (getattr(config, 'copyandpay_test_mode', '') if config else '')
                or getattr(settings, 'COPYANDPAY_TEST_MODE', '')
                or os.getenv('COPYANDPAY_TEST_MODE', '')
            ).strip()
            or ('EXTERNAL' if mode == 'Test' else '')
        ),
        'brands': (
            (getattr(config, 'copyandpay_brands', '') if config else '')
            or getattr(settings, 'COPYANDPAY_BRANDS', '')
            or os.getenv('COPYANDPAY_BRANDS', '')
            or 'PRIVATE_LABEL'
        ).strip(),
        'integrity': (
            (getattr(config, 'copyandpay_widget_integrity', '') if config else '')
            or getattr(settings, 'COPYANDPAY_WIDGET_INTEGRITY', '')
            or os.getenv('COPYANDPAY_WIDGET_INTEGRITY', '')
        ).strip(),
    }


def _copyandpay_result_code(payload: Dict[str, Any]) -> str:
    return str((payload.get('result') or {}).get('code') or '').strip()


def _copyandpay_result_description(payload: Dict[str, Any]) -> str:
    return str((payload.get('result') or {}).get('description') or '').strip()


def _copyandpay_is_approved(code: str) -> bool:
    return bool(re.match(r'^(000\.000\.|000\.100\.1|000\.[36])', code or ''))


def _copyandpay_is_pending(code: str) -> bool:
    return bool(re.match(r'^(000\.200|100\.400\.500|800\.400\.5)', code or ''))


def _extract_checkout_id_from_resource_path(resource_path: str) -> str:
    match = re.search(r'/checkouts/([^/]+)/payment', resource_path or '')
    return match.group(1).strip() if match else ''


def _resolve_resource_path(raw: str) -> str:
    value = (raw or '').strip()
    if not value:
        return ''
    if value.startswith('http://') or value.startswith('https://'):
        parsed = urlparse(value)
        if parsed.netloc:
            query_value = parse_qs(parsed.query).get('resourcePath', [''])[0]
            if query_value:
                return query_value
        return parsed.path
    return value


def _build_certificate_client(config_model: Optional[CBZConfig] = None) -> IVeriCertificateClient:
    return build_certificate_client_from_settings(config_model or _get_active_config())


def _resolve_gateway_mode(result: Optional[Dict[str, Any]] = None) -> str:
    mode = (result or {}).get('mode') or ''
    if mode:
        return mode
    config = _get_active_config()
    return config.mode if config else 'Test'


def _is_luhn_valid(pan: str) -> bool:
    total = 0
    should_double = False
    for ch in reversed(pan):
        if not ch.isdigit():
            return False
        digit = int(ch)
        if should_double:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
        should_double = not should_double
    return total % 10 == 0


def _is_valid_expiry_mm_yy(expiry: str) -> bool:
    if not re.fullmatch(r'\d{4}', expiry or ''):
        return False

    month = int(expiry[:2])
    year = int(expiry[2:])
    if month < 1 or month > 12:
        return False

    today = date.today()
    current_year = today.year % 100
    current_month = today.month

    if year < current_year:
        return False
    if year == current_year and month < current_month:
        return False

    return True


def _apply_gateway_result_to_transaction(
    txn: CBZTransaction,
    result: Dict[str, Any],
    *,
    approved: bool,
    pending: bool,
    raw_response: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist gateway result fields and normalize local transaction status."""
    txn.result_code = result.get('result_code')
    txn.result_description = result.get('result_description')
    txn.transaction_index = result.get('transaction_index') or txn.transaction_index
    txn.authorisation_code = result.get('authorisation_code') or txn.authorisation_code
    txn.request_id = result.get('request_id') or txn.request_id
    txn.bank_reference = result.get('bank_reference') or txn.bank_reference
    txn.consumer_order_id = result.get('consumer_order_id') or txn.consumer_order_id
    txn.card_bin = result.get('card_bin') or txn.card_bin

    if raw_response is not None:
        # Preserve internal 3DS audit markers set before this call so the
        # UAT export can report whether a PaRes was received.
        _3ds_meta = {}
        if isinstance(txn.gateway_response, dict):
            for key in ('_3ds_pares_received', '_3ds_pares_len'):
                if key in txn.gateway_response:
                    _3ds_meta[key] = txn.gateway_response[key]
        scrubbed = _scrub_pci_fields(raw_response)
        if _3ds_meta:
            scrubbed.update(_3ds_meta)
        txn.gateway_response = scrubbed

    if approved:
        txn.status = CBZTransaction.TransactionStatus.APPROVED
        txn.completed_at = timezone.now()
    elif pending:
        txn.status = CBZTransaction.TransactionStatus.PENDING
    elif txn.status != CBZTransaction.TransactionStatus.APPROVED:
        txn.status = CBZTransaction.TransactionStatus.DECLINED

    txn.save()


def _card_status_json_from_txn(txn: CBZTransaction, merchant_reference: str) -> JsonResponse:
    """
    Build the card payment-status response from the stored transaction.

    iVeri has no status-query command, so the authoritative result is written to
    our DB by the server-to-server 3DS ReturnUrl handler. The status page polls
    this endpoint and we report what's stored — read-only, so we never overwrite
    gateway_response (which still holds the signed card data the ReturnUrl needs
    to complete the Debit).
    """
    S = CBZTransaction.TransactionStatus
    if txn.status == S.APPROVED:
        resolved_booking_reference = None
        if txn.booking_id:
            txn.booking = _finalize_booking_reference_if_temporary(txn.booking)
            resolved_booking_reference = txn.booking.booking_reference if txn.booking else None
        return JsonResponse({
            "success": True,
            "message": "Payment approved",
            "merchant_reference": merchant_reference,
            "booking_reference": resolved_booking_reference,
            "gateway_mode": _resolve_gateway_mode(),
            "transaction_index": txn.transaction_index,
            "authorisation_code": txn.authorisation_code,
        })
    if txn.status in (S.INITIATED, S.PENDING):
        return JsonResponse({
            "success": True,
            "pending": True,
            "message": txn.result_description or "Payment still pending",
            "merchant_reference": merchant_reference,
            "gateway_mode": _resolve_gateway_mode(),
            "result_code": txn.result_code,
        }, status=202)
    return JsonResponse({
        "success": False,
        "message": txn.result_description or "Payment declined",
        "merchant_reference": merchant_reference,
        "gateway_mode": _resolve_gateway_mode(),
        "result_code": txn.result_code,
    })


def _scrub_pci_fields(response: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of the response with PCI-sensitive fields removed."""
    SENSITIVE_KEYS = {
        # REST API keys
        'PAN', 'pan', 'CardNumber', 'card_number',
        'CVV', 'cvv', 'CardSecurityCode', 'card_security_code',
        'Password', 'password', 'Secret', 'secret',
        'Token', 'token', 'AccessToken', 'access_token',
        # iVeri Lite — only scrub the CVV field; ECOM_PAYMENT_CARD_NUMBER is
        # already pre-masked by iVeri (e.g. "4242........4242") and is safe to store
        'ECOM_PAYMENT_CARD_VERIFICATION',
    }
    if not isinstance(response, dict):
        return response

    def _clean(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: ('[REDACTED]' if k in SENSITIVE_KEYS else _clean(v)) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(item) for item in obj]
        return obj

    return _clean(response)


def _resolve_or_create_booking(payload: Dict[str, Any], amount: Decimal) -> Optional[Booking]:
    """
    Resolve a booking by reference, or create a website draft booking when
    booking details are supplied without a booking reference.
    """
    booking_ref = payload.get('booking_reference')
    if booking_ref:
        booking = Booking.objects.filter(booking_reference=booking_ref).order_by('-created_at').first()
        if booking:
            return booking
        logger.warning("Booking %s not found for CBZ payment", booking_ref)
        return None

    details = payload.get('booking_details') if isinstance(payload.get('booking_details'), dict) else {}
    tour_name = details.get('tour_name') or payload.get('tour_name')
    selected_date = details.get('selected_date') or payload.get('selected_date')
    number_of_people = details.get('number_of_people') or payload.get('number_of_people') or 1

    if not tour_name or not selected_date:
        return None

    try:
        start_date = date.fromisoformat(str(selected_date))
    except (TypeError, ValueError):
        logger.warning("Invalid selected_date in website payment payload: %s", selected_date)
        return None

    try:
        adults = max(int(number_of_people), 1)
    except (TypeError, ValueError):
        adults = 1

    customer_details = details.get('customer') if isinstance(details.get('customer'), dict) else {}
    customer_name = str(customer_details.get('full_name') or '').strip()
    customer_email = str(customer_details.get('email') or '').strip()
    customer_phone = str(customer_details.get('phone') or '').strip()
    customer_country = str(customer_details.get('country') or '').strip()
    customer_requests = str(customer_details.get('special_requests') or '').strip()

    note_parts = [
        f"Website checkout draft booking. People: {adults}.",
        f"Traveler: {customer_name}" if customer_name else '',
        f"Email: {customer_email}" if customer_email else '',
        f"Phone: {customer_phone}" if customer_phone else '',
        f"Country: {customer_country}" if customer_country else '',
        f"Special requests: {customer_requests}" if customer_requests else '',
    ]

    # Find or create CustomerProfile to link to booking
    customer_profile = None
    if customer_email or customer_name:
        # Try to find existing customer by email
        if customer_email:
            customer_profile = CustomerProfile.objects.filter(email=customer_email).first()
        
        # If not found, try to find by name (loose match)
        if not customer_profile and customer_name:
            customer_profile = CustomerProfile.objects.filter(
                first_name__iexact=str(customer_name).split()[0]
            ).first() if len(str(customer_name).split()) > 0 else None
        
        # If still not found, create new customer
        if not customer_profile:
            try:
                # Create Contact first (required by CustomerProfile)
                contact = Contact.objects.create(
                    phone_number=customer_phone,
                    name=customer_name or 'Unknown'
                )
                # Create CustomerProfile linked to Contact
                names = str(customer_name).split(' ', 1) if customer_name else ['', '']
                customer_profile = CustomerProfile.objects.create(
                    contact=contact,
                    first_name=names[0],
                    last_name=names[1] if len(names) > 1 else '',
                    email=customer_email,
                    country=customer_country,
                )
            except Exception as e:
                logger.warning("Failed to create customer profile for CBZ payment: %s", e)
                customer_profile = None

    tour = Tour.objects.filter(name__iexact=str(tour_name).strip()).first()
    booking = Booking.objects.create(
        booking_reference=f"PENDING-WEB-{uuid.uuid4().hex[:10].upper()}",
        tour=tour,
        tour_name=str(tour_name).strip(),
        start_date=start_date,
        end_date=start_date,
        number_of_adults=adults,
        number_of_children=0,
        total_amount=amount,
        payment_status=Booking.PaymentStatus.PENDING,
        source=Booking.BookingSource.MANUAL_ENTRY,
        customer=customer_profile,  # NOW linking the customer!
        notes='\n'.join(part for part in note_parts if part),
        booking_details_payload=details or None,
    )

    travelers_payload = details.get('travelers') if isinstance(details.get('travelers'), list) else []
    for traveler in travelers_payload:
        if not isinstance(traveler, dict):
            continue

        name = str(traveler.get('name') or '').strip()
        nationality = str(traveler.get('nationality') or '').strip()
        gender = str(traveler.get('gender') or '').strip()
        id_number = str(traveler.get('id_number') or '').strip()
        traveler_type = str(traveler.get('type') or Traveler.TravelerType.ADULT).strip().lower()
        medical = str(traveler.get('medical') or '').strip()
        id_document_data_url = str(traveler.get('id_document_data_url') or '').strip()
        id_document_name = str(traveler.get('id_document_name') or '').strip()
        id_document_mime_type = str(traveler.get('id_document_mime_type') or '').strip()

        try:
            age = int(traveler.get('age') or 0)
        except (TypeError, ValueError):
            age = 0

        if not name or age <= 0 or not nationality or not gender or not id_number:
            continue

        if traveler_type not in {Traveler.TravelerType.ADULT, Traveler.TravelerType.CHILD}:
            traveler_type = Traveler.TravelerType.ADULT

        traveler_obj = Traveler.objects.create(
            booking=booking,
            name=name,
            age=age,
            nationality=nationality,
            gender=gender,
            id_number=id_number,
            traveler_type=traveler_type,
            medical_dietary_requirements=medical or None,
        )

        if id_document_data_url:
            _save_traveler_document_from_data_url(
                traveler_obj,
                id_document_data_url,
                fallback_name=id_document_name,
                declared_mime=id_document_mime_type,
            )
            traveler_obj.save(update_fields=['id_document', 'updated_at'])

    return booking


def _finalize_booking_reference_if_temporary(booking: Optional[Booking]) -> Optional[Booking]:
    """Replace temporary website references with canonical booking references."""
    if not booking:
        return None

    if not str(booking.booking_reference or '').startswith('PENDING-'):
        return booking

    booking.booking_reference = ''
    booking.save(update_fields=['booking_reference', 'updated_at'])
    booking.refresh_from_db(fields=['booking_reference', 'updated_at'])
    return booking


@require_http_methods(["GET"])
def cbz_public_config_view(request: HttpRequest) -> JsonResponse:
    """Expose non-sensitive CBZ payment config for frontend checkout UX."""
    return JsonResponse({
        'success': True,
        'config': _get_public_payment_config(),
    })


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

    # Resolve existing booking reference, or create a website draft booking.
    try:
        booking = _resolve_or_create_booking(payload, amount)
    except Exception as e:
        logger.warning("Error resolving/creating booking for EcoCash payment: %s", e)
        booking = None

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

        _apply_gateway_result_to_transaction(
            txn, result,
            approved=is_approved,
            pending=is_pending,
            raw_response=response,
        )

        if is_approved:
            booking = _finalize_booking_reference_if_temporary(booking)

            # Record payment on booking
            if booking:
                _record_payment(txn, booking)

            return JsonResponse({
                "success": True,
                "message": "Payment approved",
                "merchant_reference": merchant_ref,
                "booking_reference": booking.booking_reference if booking else None,
                "gateway_mode": _resolve_gateway_mode(result),
                "transaction_index": result.get('transaction_index'),
                "authorisation_code": result.get('authorisation_code'),
            })
        elif is_pending:
            booking = _finalize_booking_reference_if_temporary(booking)
            return JsonResponse({
                "success": True,
                "pending": True,
                "message": result.get(
                    'result_description',
                    'Payment initiated and awaiting final confirmation',
                ),
                "merchant_reference": merchant_ref,
                "booking_reference": booking.booking_reference if booking else None,
                "gateway_mode": _resolve_gateway_mode(result),
                "result_code": result.get('result_code'),
            }, status=202)
        else:
            status_label = result.get('status_label', 'UNKNOWN')
            is_retriable = result.get('is_retriable', False)
            return JsonResponse({
                "success": False,
                "message": result.get('result_description', 'Payment declined'),
                "merchant_reference": merchant_ref,
                "gateway_mode": _resolve_gateway_mode(result),
                "result_code": result.get('result_code'),
                "status_label": status_label,
                "retriable": is_retriable,
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

    pan = re.sub(r'\D', '', str(payload.get('pan', '')))
    expiry_date = re.sub(r'\D', '', str(payload.get('expiry_date', '')))
    cvv = re.sub(r'\D', '', str(payload.get('cvv', '')))

    if len(pan) < 13 or len(pan) > 19:
        return JsonResponse({"success": False, "message": "Invalid card number length"}, status=400)
    active_config = _get_active_config()
    is_test_mode = (active_config.mode == 'Test') if active_config else True
    if not is_test_mode and not _is_luhn_valid(pan):
        return JsonResponse({"success": False, "message": "Card number failed validation"}, status=400)
    if not _is_valid_expiry_mm_yy(expiry_date):
        return JsonResponse({"success": False, "message": "Invalid or expired card expiry date"}, status=400)
    if len(cvv) < 3 or len(cvv) > 4:
        return JsonResponse({"success": False, "message": "Invalid CVV"}, status=400)

    merchant_ref = f"KS-{uuid.uuid4().hex[:12].upper()}"
    masked_pan = f"{pan[:4]}****{pan[-4:]}" if len(pan) >= 8 else "****"

    # Resolve existing booking reference, or create a website draft booking.
    try:
        booking = _resolve_or_create_booking(payload, amount)
    except Exception as e:
        logger.warning("Error resolving/creating booking for card payment: %s", e)
        booking = None

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
            expiry_date=expiry_date,
            cvv=cvv,
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
            raw_response=response,
        )

        if is_approved:

            booking = _finalize_booking_reference_if_temporary(booking)

            if booking:
                _record_payment(txn, booking)

            return JsonResponse({
                "success": True,
                "message": "Payment approved",
                "merchant_reference": merchant_ref,
                "booking_reference": booking.booking_reference if booking else None,
                "gateway_mode": _resolve_gateway_mode(result),
                "transaction_index": result.get('transaction_index'),
                "authorisation_code": result.get('authorisation_code'),
            })
        elif is_3ds_required:
            booking = _finalize_booking_reference_if_temporary(booking)
            challenge_data = IVeriClient.get_3ds_challenge_data(response)

            # If iVeri didn't echo TermUrl, fall back to the configured one so the
            # frontend always knows where to direct the ACS redirect.
            fallback_term_url = getattr(settings, 'CBZ_3DS_TERM_URL', '') or ''
            if fallback_term_url and not (
                challenge_data.get('TermUrl') or challenge_data.get('TermURL')
            ):
                challenge_data['TermUrl'] = fallback_term_url

            # Ensure MD (merchant_reference) is in challenge data so the frontend
            # can include it in the ACS POST and the ACS echoes it back to TermUrl.
            if not challenge_data.get('MD'):
                challenge_data['MD'] = merchant_ref

            return JsonResponse({
                "success": True,
                "requires_3ds": True,
                "pending": True,
                "message": result.get('result_description', '3DS authentication required'),
                "merchant_reference": merchant_ref,
                "booking_reference": booking.booking_reference if booking else None,
                "gateway_mode": _resolve_gateway_mode(result),
                "result_code": result.get('result_code'),
                "transaction_index": result.get('transaction_index'),
                "challenge": challenge_data,
                "next_step": {
                    "complete_url": "/crm-api/payments/cbz/card/3ds/complete/",
                    "query_url": f"/crm-api/payments/cbz/query/{merchant_ref}/",
                },
            }, status=202)
        elif is_pending:
            booking = _finalize_booking_reference_if_temporary(booking)
            return JsonResponse({
                "success": True,
                "pending": True,
                "message": result.get('result_description', 'Payment initiated and awaiting final confirmation'),
                "merchant_reference": merchant_ref,
                "booking_reference": booking.booking_reference if booking else None,
                "gateway_mode": _resolve_gateway_mode(result),
                "result_code": result.get('result_code'),
                "transaction_index": result.get('transaction_index'),
            }, status=202)
        else:
            return JsonResponse({
                "success": False,
                "message": result.get('result_description', 'Payment declined'),
                "merchant_reference": merchant_ref,
                "gateway_mode": _resolve_gateway_mode(result),
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
def cbz_copyandpay_prepare_view(request: HttpRequest) -> JsonResponse:
    """
    POST /crm-api/payments/cbz/copyandpay/prepare/

    Prepares a COPYandPAY checkout and returns a checkoutId for paymentWidgets.js.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    required = ["amount", "currency"]
    missing = [k for k in required if k not in payload]
    if missing:
        return JsonResponse(
            {"success": False, "message": f"Missing fields: {', '.join(missing)}"},
            status=400,
        )

    try:
        amount = Decimal(str(payload['amount']))
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (InvalidOperation, ValueError) as exc:
        return JsonResponse(
            {"success": False, "message": f"Invalid amount: {exc}"},
            status=400,
        )

    config = _get_copyandpay_config()
    if not config['entity_id'] or not config['bearer_token']:
        return JsonResponse(
            {
                "success": False,
                "message": "COPYandPAY is not configured. Missing entity ID or bearer token.",
            },
            status=503,
        )

    merchant_ref = f"KS-{uuid.uuid4().hex[:12].upper()}"
    currency = str(payload.get('currency', 'USD')).upper()

    try:
        booking = _resolve_or_create_booking(payload, amount)
    except Exception as exc:
        logger.warning("Error resolving/creating booking for COPYandPAY prepare: %s", exc)
        booking = None

    txn = CBZTransaction.objects.create(
        merchant_reference=merchant_ref,
        payment_type=CBZTransaction.PaymentType.CARD,
        amount=amount,
        currency=currency,
        command='Debit',
        status=CBZTransaction.TransactionStatus.INITIATED,
        booking=booking,
    )

    request_data = {
        'entityId': config['entity_id'],
        'amount': f"{amount:.2f}",
        'currency': currency,
        'paymentType': 'DB',
        'merchantTransactionId': merchant_ref,
    }
    if config['test_mode']:
        request_data['testMode'] = config['test_mode']

    # NOTE: shopperResultUrl must NOT be sent in the /v1/checkouts prepare
    # request. Per OPPWA's integration guide it belongs only on the payment
    # form's action attribute (step 2). Sending it here as well causes OPPWA
    # to reject the later widget submission with "shopperResultUrl was
    # already set and cannot be overwritten" (200.300.404), even when the
    # value is byte-for-byte identical.
    final_shopper_result_url = ''
    raw_shopper_result_url = str(payload.get('shopper_result_url') or '').strip()
    if raw_shopper_result_url:
        parsed = urlparse(raw_shopper_result_url)
        query = parse_qs(parsed.query)
        query['ref'] = [merchant_ref]
        final_shopper_result_url = urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    headers = {
        'Authorization': f"Bearer {config['bearer_token']}",
    }
    endpoint = f"{config['base_url']}/v1/checkouts"

    logger.info(
        "COPYandPAY prepare-checkout request | endpoint=%s | data=%s",
        endpoint,
        {**request_data, 'entityId': request_data['entityId'][:8] + '...'},
    )

    try:
        response = requests.post(endpoint, data=request_data, headers=headers, timeout=60)
        try:
            data = response.json()
        except ValueError:
            data = {'result': {'description': response.text[:500], 'code': ''}}

        logger.info(
            "COPYandPAY prepare-checkout response | status=%s | body=%s",
            response.status_code,
            data,
        )

        code = _copyandpay_result_code(data)
        description = _copyandpay_result_description(data)
        checkout_id = str(data.get('id') or '').strip()

        txn.result_code = code or txn.result_code
        txn.result_description = description or txn.result_description
        txn.request_id = checkout_id or txn.request_id
        if response.status_code >= 400 or not checkout_id:
            txn.status = CBZTransaction.TransactionStatus.FAILED
        txn.save()

        if response.status_code >= 400 or not checkout_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": description or 'Failed to prepare checkout',
                    "merchant_reference": merchant_ref,
                    "result_code": code,
                },
                status=502,
            )

        booking = _finalize_booking_reference_if_temporary(booking)

        widget_url = f"{config['base_url']}/v1/paymentWidgets.js?checkoutId={checkout_id}"
        return JsonResponse({
            "success": True,
            "message": "Checkout prepared",
            "merchant_reference": merchant_ref,
            "booking_reference": booking.booking_reference if booking else None,
            "gateway_mode": config['mode'],
            "checkout_id": checkout_id,
            "widget_script_url": widget_url,
            "brands": config['brands'],
            "integrity": config['integrity'] or None,
            "shopper_result_url": final_shopper_result_url or None,
        })
    except Exception as exc:
        logger.exception("COPYandPAY checkout preparation failed")
        txn.status = CBZTransaction.TransactionStatus.FAILED
        txn.result_description = str(exc)[:500]
        txn.save()
        return JsonResponse(
            {"success": False, "message": str(exc), "merchant_reference": merchant_ref},
            status=502,
        )


@require_http_methods(["GET"])
def cbz_copyandpay_status_view(request: HttpRequest) -> JsonResponse:
    """
    GET /crm-api/payments/cbz/copyandpay/status/?resourcePath=...&merchant_reference=...

    Verifies COPYandPAY payment status using the redirected resourcePath.
    """
    raw_resource_path = request.GET.get('resourcePath', '')
    resource_path = _resolve_resource_path(raw_resource_path)
    merchant_reference = (request.GET.get('merchant_reference', '') or request.GET.get('ref', '')).strip()

    if not resource_path:
        return JsonResponse({"success": False, "message": "Missing query parameter: resourcePath"}, status=400)

    if not resource_path.startswith('/'):
        resource_path = f"/{resource_path}"

    config = _get_copyandpay_config()
    if not config['entity_id'] or not config['bearer_token']:
        return JsonResponse(
            {
                "success": False,
                "message": "COPYandPAY is not configured. Missing entity ID or bearer token.",
            },
            status=503,
        )

    headers = {
        'Authorization': f"Bearer {config['bearer_token']}",
    }
    endpoint = f"{config['base_url']}{resource_path}"

    logger.info(
        "COPYandPAY status request | endpoint=%s | entityId=%s... | merchant_reference=%s",
        endpoint,
        config['entity_id'][:8],
        merchant_reference,
    )

    try:
        response = requests.get(
            endpoint,
            params={'entityId': config['entity_id']},
            headers=headers,
            timeout=60,
        )
        try:
            data = response.json()
        except ValueError:
            data = {'result': {'description': response.text[:500], 'code': ''}}

        logger.info(
            "COPYandPAY status response | status=%s | body=%s",
            response.status_code,
            data,
        )

        result_code = _copyandpay_result_code(data)
        result_description = _copyandpay_result_description(data)

        response_merchant_ref = str(data.get('merchantTransactionId') or '').strip()
        if not merchant_reference:
            merchant_reference = response_merchant_ref

        checkout_id = _extract_checkout_id_from_resource_path(resource_path)
        txn = None
        if merchant_reference:
            txn = CBZTransaction.objects.filter(merchant_reference=merchant_reference).first()
        if not txn and checkout_id:
            txn = CBZTransaction.objects.filter(request_id=checkout_id).first()
        if txn and not merchant_reference:
            merchant_reference = txn.merchant_reference

        is_approved = _copyandpay_is_approved(result_code)
        is_pending = _copyandpay_is_pending(result_code)

        if txn:
            txn.result_code = result_code or txn.result_code
            txn.result_description = result_description or txn.result_description
            txn.transaction_index = str(data.get('id') or txn.transaction_index or '').strip() or txn.transaction_index
            txn.request_id = checkout_id or txn.request_id

            if is_approved:
                txn.status = CBZTransaction.TransactionStatus.APPROVED
                txn.completed_at = timezone.now()
            elif is_pending:
                txn.status = CBZTransaction.TransactionStatus.PENDING
            elif txn.status != CBZTransaction.TransactionStatus.APPROVED:
                txn.status = CBZTransaction.TransactionStatus.DECLINED
            txn.save()

            if is_approved and txn.booking:
                existing_payment = Payment.objects.filter(
                    booking=txn.booking,
                    transaction_reference=txn.merchant_reference,
                ).exists()
                if not existing_payment:
                    _record_payment(txn, txn.booking)

        resolved_booking_reference = None
        if txn and txn.booking_id:
            txn.booking = _finalize_booking_reference_if_temporary(txn.booking)
            resolved_booking_reference = txn.booking.booking_reference if txn.booking else None

        if response.status_code >= 400:
            return JsonResponse({
                "success": False,
                "message": result_description or 'Unable to verify payment status',
                "merchant_reference": merchant_reference,
                "booking_reference": resolved_booking_reference,
                "gateway_mode": config['mode'],
                "result_code": result_code,
            }, status=502)

        if is_approved:
            return JsonResponse({
                "success": True,
                "message": result_description or 'Payment approved',
                "merchant_reference": merchant_reference,
                "booking_reference": resolved_booking_reference,
                "gateway_mode": config['mode'],
                "result_code": result_code,
                "payment_id": data.get('id'),
            })

        if is_pending:
            return JsonResponse({
                "success": True,
                "pending": True,
                "message": result_description or 'Payment is pending final confirmation',
                "merchant_reference": merchant_reference,
                "booking_reference": resolved_booking_reference,
                "gateway_mode": config['mode'],
                "result_code": result_code,
                "payment_id": data.get('id'),
            }, status=202)

        return JsonResponse({
            "success": False,
            "message": result_description or 'Payment was not approved',
            "merchant_reference": merchant_reference,
            "booking_reference": resolved_booking_reference,
            "gateway_mode": config['mode'],
            "result_code": result_code,
            "payment_id": data.get('id'),
        })
    except Exception as exc:
        logger.exception("COPYandPAY status verification failed")
        return JsonResponse({"success": False, "message": str(exc)}, status=502)


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

    # PaRes is the bank ACS authentication response forwarded from the browser
    pares = (payload.get('pares') or payload.get('PaRes') or '').strip()

    txn = CBZTransaction.objects.filter(
        merchant_reference=merchant_reference,
        payment_type=CBZTransaction.PaymentType.CARD,
    ).first()
    if not txn:
        return JsonResponse({"success": False, "message": "Transaction not found"}, status=404)

    if pares:
        logger.info(
            "3DS PaRes received | ref=%s pares_len=%d",
            merchant_reference, len(pares),
        )
        # Store PaRes in the transaction gateway response for audit
        existing = txn.gateway_response or {}
        if isinstance(existing, dict):
            existing['_3ds_pares_received'] = True
            existing['_3ds_pares_len'] = len(pares)
            txn.gateway_response = existing
            txn.save(update_fields=['gateway_response'])

    if txn.status == CBZTransaction.TransactionStatus.APPROVED:
        resolved_booking_reference = None
        if txn.booking_id:
            txn.booking = _finalize_booking_reference_if_temporary(txn.booking)
            resolved_booking_reference = txn.booking.booking_reference if txn.booking else None
        return JsonResponse({
            "success": True,
            "message": "Payment approved",
            "merchant_reference": merchant_reference,
            "booking_reference": resolved_booking_reference,
            "gateway_mode": _resolve_gateway_mode(),
            "transaction_index": txn.transaction_index,
            "authorisation_code": txn.authorisation_code,
        })

    # If the browser forwarded a PaRes and we have a TransactionIndex, submit it
    # to iVeri to complete 3DS authentication (3DS v1 path — liability shifts to
    # the issuer on success). Otherwise there is nothing to send: the
    # authoritative result is written to our DB by the server-to-server 3DS
    # ReturnUrl handler, and iVeri has no status-query command.
    if pares and txn.transaction_index:
        client = _build_client()
        try:
            logger.info(
                "Submitting 3DS PaRes to iVeri | ref=%s txn_idx=%s",
                merchant_reference, txn.transaction_index,
            )
            response = client.complete_3ds_auth(
                transaction_index=txn.transaction_index,
                merchant_reference=merchant_reference,
                pares=pares,
                amount=txn.amount,
                currency=txn.currency,
            )
            result = IVeriClient.get_result(response)
            is_approved = IVeriClient.is_approved(response)
            is_pending = IVeriClient.is_pending(response)

            _apply_gateway_result_to_transaction(
                txn,
                result,
                approved=is_approved,
                pending=is_pending,
                raw_response=response,
            )

            if is_approved and txn.booking:
                existing_payment = Payment.objects.filter(
                    booking=txn.booking,
                    transaction_reference=txn.merchant_reference,
                ).exists()
                if not existing_payment:
                    _record_payment(txn, txn.booking)
        except Exception as e:
            logger.exception("CBZ card 3DS PaRes completion failed")
            return JsonResponse({"success": False, "message": str(e)}, status=502)

    # Report the authoritative status from our DB (refresh in case the ReturnUrl
    # updated it concurrently). Read-only — must not overwrite gateway_response.
    txn.refresh_from_db()
    return _card_status_json_from_txn(txn, merchant_reference)


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
            "gateway_mode": _resolve_gateway_mode(result),
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

    Handles iVeri out-of-band callback notifications in TWO formats:

    1. iVeri Lite (hosted payment page) — flat form-POST with LITE_*/ECOM_* keys:
       - MERCHANTREFERENCE        → merchant_reference (transaction lookup)
       - LITE_PAYMENT_CARD_STATUS → result code ("0"/"1"/"4"/"255")
       - LITE_TRANSACTIONINDEX    → transaction_index
       - LITE_BANKREFERENCE       → bank_reference
       - ECOM_CONSUMERORDERID     → consumer_order_id
       - LITE_PAYMENT_CARD_BIN    → card_bin
       - LITE_ORDER_AUTHORISATIONCODE → authorisation_code
       - LITE_RESULT_DESCRIPTION  → result_description
       Detected when payload contains "LITE_PAYMENT_CARD_STATUS".

    2. iVeri REST — JSON body with nested Transaction object:
       - Transaction.MerchantReference, Transaction.ResultCode, etc.
       Detected when payload contains "Transaction".

    Status codes (both formats use same numeric values):
      "0"   → SUCCESS — mark APPROVED
      "1"   → ERROR / timeout — leave PENDING for reconciliation
      "4"   → DECLINED — terminal failure
      "255" → INVALID_CARD — terminal failure
    """
    # ── Parse incoming body (JSON or form-encoded) ──────────────────
    payload: Dict[str, Any] = {}
    content_type = request.content_type or ''
    if 'application/json' in content_type:
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            logger.warning("CBZ callback: invalid JSON body")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
        payload = dict(request.POST)
        # QueryDict gives lists; flatten single-value lists
        payload = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in payload.items()}
    else:
        # Attempt JSON first, fall back to form data
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            payload = dict(request.POST)
            payload = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in payload.items()}

    logger.info(
        "CBZ callback received",
        extra={"payload_preview": str(payload)[:500]},
    )

    # ── Detect format and extract normalised fields ──────────────────
    is_lite_format = 'LITE_PAYMENT_CARD_STATUS' in payload

    if is_lite_format:
        merchant_ref = payload.get('MERCHANTREFERENCE') or payload.get('MerchantReference')
        result_code = str(payload.get('LITE_PAYMENT_CARD_STATUS') or '')
        transaction_index = payload.get('LITE_TRANSACTIONINDEX')
        bank_reference = payload.get('LITE_BANKREFERENCE')
        consumer_order_id = payload.get('ECOM_CONSUMERORDERID')
        card_bin = payload.get('LITE_PAYMENT_CARD_BIN')
        authorisation_code = payload.get('LITE_ORDER_AUTHORISATIONCODE')
        result_description = payload.get('LITE_RESULT_DESCRIPTION', '')
        # ECOM_PAYMENT_CARD_NUMBER is pre-masked by iVeri (e.g. "4242........4242") — safe to store
        masked_pan_from_callback = payload.get('ECOM_PAYMENT_CARD_NUMBER') or ''
        callback_format = 'IVERI_LITE'
    else:
        txn_data = payload.get('Transaction', {})
        merchant_ref = txn_data.get('MerchantReference')
        result_code = str(txn_data.get('ResultCode') or '')
        transaction_index = txn_data.get('TransactionIndex')
        bank_reference = txn_data.get('BankReference')
        consumer_order_id = txn_data.get('ConsumerOrderID')
        card_bin = txn_data.get('CardBin') or txn_data.get('BIN')
        authorisation_code = txn_data.get('AuthorisationCode')
        result_description = txn_data.get('ResultDescription', '')
        masked_pan_from_callback = ''
        callback_format = 'IVERI_REST'

    if not merchant_ref:
        logger.warning("CBZ callback (%s): no MerchantReference in payload", callback_format)
        return JsonResponse({"error": "Missing MerchantReference"}, status=400)

    txn = CBZTransaction.objects.filter(merchant_reference=merchant_ref).first()
    if not txn:
        logger.warning("CBZ callback: transaction %s not found", merchant_ref)
        return JsonResponse({"error": "Transaction not found"}, status=404)

    status_label = IVERI_STATUS_MAP.get(result_code, 'UNKNOWN')
    old_status = txn.status

    # ── Persist all callback data ────────────────────────────────────
    txn.result_code = result_code
    txn.result_description = result_description
    txn.transaction_index = transaction_index or txn.transaction_index
    txn.authorisation_code = authorisation_code or txn.authorisation_code
    txn.bank_reference = bank_reference or txn.bank_reference
    txn.consumer_order_id = consumer_order_id or txn.consumer_order_id
    txn.card_bin = card_bin or txn.card_bin
    if masked_pan_from_callback:
        txn.masked_pan = masked_pan_from_callback
    txn.gateway_response = _scrub_pci_fields(payload)

    # ── Update transaction status ────────────────────────────────────
    if result_code == RESULT_CODE_SUCCESS:
        # Idempotent: skip re-recording if already approved
        if txn.status == CBZTransaction.TransactionStatus.APPROVED:
            txn.save()
            logger.info(
                "CBZ callback (%s): transaction %s already APPROVED — skipping payment record",
                callback_format, merchant_ref,
            )
        else:
            txn.status = CBZTransaction.TransactionStatus.APPROVED
            txn.completed_at = timezone.now()
            txn.save()
            if txn.booking:
                _record_payment(txn, txn.booking)
            logger.info(
                "Payment status changed",
                extra={
                    "transaction_id": str(txn.id),
                    "merchant_reference": merchant_ref,
                    "old_status": old_status,
                    "new_status": "APPROVED",
                    "gateway": "IVERI",
                    "callback_format": callback_format,
                    "result_code": result_code,
                },
            )
    elif result_code in IVERI_RETRIABLE_CODES:
        # Transient error (code "1") — leave PENDING for reconciliation
        if txn.status in {
            CBZTransaction.TransactionStatus.INITIATED,
            CBZTransaction.TransactionStatus.PENDING,
        }:
            txn.status = CBZTransaction.TransactionStatus.PENDING
        txn.save()
        logger.warning(
            "CBZ callback (%s): retriable error on %s (code=%s, desc=%s) — leaving PENDING",
            callback_format, merchant_ref, result_code, result_description,
        )
    else:
        # DECLINED (4), INVALID_CARD (255), or unknown — terminal failure
        if txn.status not in {
            CBZTransaction.TransactionStatus.APPROVED,
            CBZTransaction.TransactionStatus.DECLINED,
        }:
            txn.status = CBZTransaction.TransactionStatus.DECLINED
        txn.save()
        logger.info(
            "Payment status changed",
            extra={
                "transaction_id": str(txn.id),
                "merchant_reference": merchant_ref,
                "old_status": old_status,
                "new_status": "DECLINED",
                "gateway": "IVERI",
                "callback_format": callback_format,
                "result_code": result_code,
                "status_label": status_label,
                "result_description": result_description,
            },
        )

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


# ─── 3DS 2 Enrollment + ReturnUrl ───────────────────────────────────

_3DS_PAN_SALT = 'cbz_3ds_pan_v1'
_3DS_PAN_MAX_AGE = 900  # 15 minutes — enough for a 3DS challenge


@csrf_exempt
@require_http_methods(["POST"])
def cbz_card_3ds_enroll_view(request: HttpRequest) -> JsonResponse:
    """
    POST /crm-api/payments/cbz/card/3ds/enroll/

    Prepares a 3DS 2 enrollment request for the iVeri Gateway.

    The frontend must auto-submit the returned form fields to enrollment_url
    so that iVeri can drive the browser through the 3DS challenge and POST
    the authentication result back to the ReturnUrl (cbz_card_3ds_return_view).

    Request JSON:
    {
        "pan": "4070427646039018",
        "expiry_date": "0228",
        "cvv": "123",
        "amount": 25.00,
        "currency": "USD",
        "booking_reference": "KS-ABC123"   // optional
    }

    Response:
    {
        "success": true,
        "merchant_reference": "KS-XXXXXXXXXXXX",
        "enrollment_url": "https://portal.host.iveri.com/threedsecure/EnrollmentInitial",
        "fields": {
            "ApplicationID": "...",
            "MerchantReference": "...",
            "Amount": "2500",
            "Currency": "USD",
            "PAN": "4070427646039018",
            "ExpiryDate": "0228",
            "CardSecurityCode": "123",
            "ReturnUrl": "https://backend.kalaisafaris.com/crm-api/payments/cbz/card/3ds/return/"
        }
    }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    required = ["pan", "expiry_date", "cvv", "amount", "currency"]
    missing = [k for k in required if k not in payload]
    if missing:
        return JsonResponse(
            {"success": False, "message": f"Missing fields: {', '.join(missing)}"},
            status=400,
        )

    try:
        amount = Decimal(str(payload['amount']))
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (InvalidOperation, ValueError) as e:
        return JsonResponse({"success": False, "message": f"Invalid amount: {e}"}, status=400)

    pan = re.sub(r'\D', '', str(payload.get('pan', '')))
    expiry_date = re.sub(r'\D', '', str(payload.get('expiry_date', '')))
    cvv = re.sub(r'\D', '', str(payload.get('cvv', '')))

    if len(pan) < 13 or len(pan) > 19:
        return JsonResponse({"success": False, "message": "Invalid card number length"}, status=400)
    active_config = _get_active_config()
    is_test_mode = (active_config.mode == 'Test') if active_config else True
    if not is_test_mode and not _is_luhn_valid(pan):
        return JsonResponse({"success": False, "message": "Card number failed validation"}, status=400)
    if not _is_valid_expiry_mm_yy(expiry_date):
        return JsonResponse({"success": False, "message": "Invalid or expired card expiry date"}, status=400)
    if len(cvv) < 3 or len(cvv) > 4:
        return JsonResponse({"success": False, "message": "Invalid CVV"}, status=400)

    currency = str(payload.get('currency', 'USD')).upper()
    merchant_ref = f"KS-{uuid.uuid4().hex[:12].upper()}"
    masked_pan = f"{pan[:4]}****{pan[-4:]}" if len(pan) >= 8 else "****"

    # ReturnUrl — backend endpoint that receives the 3DS result from iVeri
    return_url = getattr(settings, 'CBZ_3DS_RETURN_URL', '') or ''
    if not return_url:
        logger.warning(
            "CBZ_3DS_RETURN_URL not configured — iVeri cannot POST 3DS result back. "
            "Set CBZ_3DS_RETURN_URL to the public URL of /crm-api/payments/cbz/card/3ds/return/"
        )
        return JsonResponse(
            {"success": False, "message": "3DS return URL not configured. Contact support."},
            status=503,
        )

    try:
        booking = _resolve_or_create_booking(payload, amount)
    except Exception as e:
        logger.warning("Error resolving/creating booking for 3DS enrollment: %s", e)
        booking = None

    txn = CBZTransaction.objects.create(
        merchant_reference=merchant_ref,
        payment_type=CBZTransaction.PaymentType.CARD,
        masked_pan=masked_pan,
        amount=amount,
        currency=currency,
        command='Debit',
        status=CBZTransaction.TransactionStatus.INITIATED,
        booking=booking,
    )

    # Temporarily sign the card data so the ReturnUrl handler can complete the Debit
    # without the frontend needing to re-submit the PAN.
    signed_card = signing.dumps(
        {'pan': pan, 'expiry': expiry_date, 'cvv': cvv},
        salt=_3DS_PAN_SALT,
    )
    txn.gateway_response = {'_signed_card': signed_card, '_3ds_enrollment_initiated': True}
    txn.save(update_fields=['gateway_response'])

    client = _build_client()
    enrollment = client.get_3ds_enrollment_form_data(
        pan=pan,
        expiry_date=expiry_date,
        amount=amount,
        currency=currency,
        merchant_reference=merchant_ref,
        return_url=return_url,
        cvv=cvv,
    )

    return JsonResponse({
        "success": True,
        "merchant_reference": merchant_ref,
        "booking_reference": booking.booking_reference if booking else None,
        "enrollment_url": enrollment['enrollment_url'],
        "fields": enrollment['fields'],
    })


@csrf_exempt
@require_http_methods(["POST"])
def cbz_card_3ds_return_view(request: HttpRequest) -> HttpResponseRedirect:
    """
    POST /crm-api/payments/cbz/card/3ds/return/

    iVeri POSTs the 3DS 2 authentication result to this URL after the
    cardholder completes the enrollment/challenge flow.

    On ResultCode "0": retrieves signed card data, submits the Debit with
    3DS authentication fields, then redirects the browser to the frontend
    payment-status page.

    On non-zero ResultCode: marks the transaction failed and redirects to
    the frontend with an error.
    """
    # Parse the form POST from iVeri
    payload: Dict[str, Any] = {}
    content_type = request.content_type or ''
    if 'application/json' in content_type:
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            payload = {}
    else:
        payload = {
            k: (v[0] if isinstance(v, list) and len(v) == 1 else v)
            for k, v in request.POST.items()
        }

    logger.info("3DS ReturnUrl received | keys=%s", list(payload.keys()))

    merchant_ref = str(payload.get('MerchantReference') or '').strip()
    result_code = str(payload.get('ResultCode') or '').strip()

    frontend_base = getattr(settings, 'CBZ_3DS_FRONTEND_BASE', '') or ''

    def _redirect(path: str) -> HttpResponseRedirect:
        return HttpResponseRedirect(f"{frontend_base.rstrip('/')}{path}")

    if not merchant_ref:
        logger.warning("3DS ReturnUrl: no MerchantReference in payload")
        return _redirect('/booking/payment-status?channel=card&error=no_reference')

    txn = CBZTransaction.objects.filter(merchant_reference=merchant_ref).first()
    if not txn:
        logger.warning("3DS ReturnUrl: transaction %s not found", merchant_ref)
        return _redirect(f'/booking/payment-status?channel=card&error=not_found&ref={merchant_ref}')

    # Store the 3DS auth data on the transaction
    stored = txn.gateway_response or {}
    stored['_3ds_return_payload'] = _scrub_pci_fields(payload)
    stored['_3ds_pares_received'] = True  # reuse existing UAT export field

    if result_code != '0':
        result_desc = str(payload.get('ResultDescription') or 'Authentication failed')
        txn.result_code = result_code
        txn.result_description = result_desc
        txn.status = CBZTransaction.TransactionStatus.DECLINED
        txn.gateway_response = stored
        txn.save()
        # Log the description value (not just keys) so the real iVeri reason is
        # visible, and forward it to the status page instead of a bare code.
        logger.warning(
            "3DS ReturnUrl: authentication failed | ref=%s code=%s desc=%s",
            merchant_ref, result_code, result_desc,
        )
        return _redirect(
            f'/booking/payment-status?channel=card&ref={merchant_ref}'
            f'&error=3ds_failed&result_code={result_code}'
            f'&result_description={quote(result_desc)}'
        )

    # 3DS authentication succeeded — collect auth fields for the Debit
    three_ds_auth = {}
    for field in (
        'CardHolderAuthenticationData',
        'CardHolderAuthenticationID',
        'ElectronicCommerceIndicator',
        'ThreeDSecure_DSTransID',
        'ThreeDSecure_ProtocolVersion',
        'ThreeDSecure_AuthenticationType',
        'ThreeDSecure_VEResEnrolled',
        'ThreeDSecure_RequestID',
        'JWT',
    ):
        value = payload.get(field)
        if value:
            three_ds_auth[field] = str(value)

    stored['_3ds_auth_data'] = three_ds_auth
    txn.gateway_response = stored

    # iVeri's Debit hard-requires CardHolderAuthenticationData whenever a 3DS
    # ECI is sent. Cards that aren't 3DS-enrolled never get this field from
    # the ACS/enrollment step, and iVeri rejects the Debit with -255 "Missing
    # CardHolderAuthenticationData" — there's no valid substitute value, so
    # decline here rather than attempt a Debit that's guaranteed to fail (or
    # risk an unauthenticated charge by dropping the 3DS fields).
    if not three_ds_auth.get('CardHolderAuthenticationData'):
        logger.warning(
            "3DS ReturnUrl: no CardHolderAuthenticationData (card not 3DS-enrolled) "
            "— declining without attempting the Debit | ref=%s enrolled=%s",
            merchant_ref, three_ds_auth.get('ThreeDSecure_VEResEnrolled'),
        )
        stored.pop('_signed_card', None)
        txn.gateway_response = stored
        txn.status = CBZTransaction.TransactionStatus.DECLINED
        txn.result_description = 'Card is not enrolled in 3D Secure. Please try a different card.'
        txn.save(update_fields=['status', 'result_description', 'gateway_response'])
        return _redirect(
            f'/booking/payment-status?channel=card&ref={merchant_ref}&error=3ds_not_enrolled'
        )

    txn.save(update_fields=['gateway_response'])

    # Retrieve the temporarily signed card data and complete the Debit
    signed_card = stored.get('_signed_card', '')
    if not signed_card:
        logger.error("3DS ReturnUrl: no signed card data for %s — cannot complete Debit", merchant_ref)
        txn.status = CBZTransaction.TransactionStatus.FAILED
        txn.result_description = '3DS completed but card data unavailable for charge'
        txn.save(update_fields=['status', 'result_description', 'gateway_response'])
        return _redirect(f'/booking/payment-status?channel=card&ref={merchant_ref}&error=card_data_missing')

    try:
        card_data = signing.loads(signed_card, salt=_3DS_PAN_SALT, max_age=_3DS_PAN_MAX_AGE)
    except signing.SignatureExpired:
        logger.error("3DS ReturnUrl: signed card data expired for %s", merchant_ref)
        txn.status = CBZTransaction.TransactionStatus.FAILED
        txn.result_description = '3DS session expired — please restart payment'
        txn.save(update_fields=['status', 'result_description'])
        return _redirect(f'/booking/payment-status?channel=card&ref={merchant_ref}&error=session_expired')
    except Exception:
        logger.exception("3DS ReturnUrl: could not load signed card data for %s", merchant_ref)
        txn.status = CBZTransaction.TransactionStatus.FAILED
        txn.result_description = '3DS completion error'
        txn.save(update_fields=['status', 'result_description'])
        return _redirect(f'/booking/payment-status?channel=card&ref={merchant_ref}&error=internal')

    # Clear the signed card data before making the Debit call
    stored.pop('_signed_card', None)
    txn.gateway_response = stored
    txn.save(update_fields=['gateway_response'])

    client = _build_client()
    try:
        response = client.debit_card(
            pan=card_data['pan'],
            expiry_date=card_data['expiry'],
            cvv=card_data.get('cvv', ''),
            amount=txn.amount,
            currency=txn.currency,
            merchant_reference=merchant_ref,
            threed_secure_data=three_ds_auth or None,
        )

        result = IVeriClient.get_result(response)
        is_approved = IVeriClient.is_approved(response)
        is_pending = IVeriClient.is_pending(response)

        _apply_gateway_result_to_transaction(
            txn, result,
            approved=is_approved,
            pending=is_pending,
            raw_response=response,
        )

        if is_approved:
            txn.booking = _finalize_booking_reference_if_temporary(txn.booking)
            if txn.booking:
                existing = Payment.objects.filter(
                    booking=txn.booking,
                    transaction_reference=txn.merchant_reference,
                ).exists()
                if not existing:
                    _record_payment(txn, txn.booking)

        logger.info(
            "3DS ReturnUrl: Debit complete | ref=%s approved=%s pending=%s",
            merchant_ref, is_approved, is_pending,
        )

    except Exception:
        logger.exception("3DS ReturnUrl: Debit failed | ref=%s", merchant_ref)
        txn.status = CBZTransaction.TransactionStatus.FAILED
        txn.save(update_fields=['status'])

    return _redirect(f'/booking/payment-status?channel=card&ref={merchant_ref}&provider=cbz')


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
