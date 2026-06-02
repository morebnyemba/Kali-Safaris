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
from urllib.parse import parse_qs, urlparse

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional
import requests
from django.conf import settings
from django.http import JsonResponse, HttpRequest
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
                'brands': copyandpay_brands or 'VISA MASTER AMEX',
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
            or 'VISA MASTER AMEX'
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
        txn.gateway_response = _scrub_pci_fields(raw_response)

    if approved:
        txn.status = CBZTransaction.TransactionStatus.APPROVED
        txn.completed_at = timezone.now()
    elif pending:
        txn.status = CBZTransaction.TransactionStatus.PENDING
    elif txn.status != CBZTransaction.TransactionStatus.APPROVED:
        txn.status = CBZTransaction.TransactionStatus.DECLINED

    txn.save()


def _scrub_pci_fields(response: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of the response with PCI-sensitive fields removed."""
    SENSITIVE_KEYS = {
        'PAN', 'pan', 'CardNumber', 'card_number',
        'CVV', 'cvv', 'CardSecurityCode', 'card_security_code',
        'Password', 'password', 'Secret', 'secret',
        'Token', 'token', 'AccessToken', 'access_token',
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
    if not _is_luhn_valid(pan):
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
                "challenge": IVeriClient.get_3ds_challenge_data(response),
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
    if payload.get('shopper_result_url'):
        request_data['shopperResultUrl'] = str(payload.get('shopper_result_url')).strip()

    headers = {
        'Authorization': f"Bearer {config['bearer_token']}",
    }
    endpoint = f"{config['base_url']}/v1/checkouts"

    try:
        response = requests.post(endpoint, data=request_data, headers=headers, timeout=60)
        try:
            data = response.json()
        except ValueError:
            data = {'result': {'description': response.text[:500], 'code': ''}}

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

    txn = CBZTransaction.objects.filter(
        merchant_reference=merchant_reference,
        payment_type=CBZTransaction.PaymentType.CARD,
    ).first()
    if not txn:
        return JsonResponse({"success": False, "message": "Transaction not found"}, status=404)

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
            raw_response=response,
        )

        if is_approved and txn.booking:
            existing_payment = Payment.objects.filter(
                booking=txn.booking,
                transaction_reference=txn.merchant_reference,
            ).exists()
            if not existing_payment:
                _record_payment(txn, txn.booking)

        if is_approved:
            resolved_booking_reference = None
            if txn.booking_id:
                txn.booking = _finalize_booking_reference_if_temporary(txn.booking)
                resolved_booking_reference = txn.booking.booking_reference if txn.booking else None

            return JsonResponse({
                "success": True,
                "message": "Payment approved",
                "merchant_reference": merchant_reference,
                "booking_reference": resolved_booking_reference,
                "gateway_mode": _resolve_gateway_mode(result),
                "transaction_index": result.get('transaction_index'),
                "authorisation_code": result.get('authorisation_code'),
            })

        if is_pending:
            return JsonResponse({
                "success": True,
                "pending": True,
                "message": result.get('result_description', 'Payment still pending'),
                "merchant_reference": merchant_reference,
                "gateway_mode": _resolve_gateway_mode(result),
                "result_code": result.get('result_code'),
            }, status=202)

        return JsonResponse({
            "success": False,
            "message": result.get('result_description', 'Payment declined'),
            "merchant_reference": merchant_reference,
            "gateway_mode": _resolve_gateway_mode(result),
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

    Receives out-of-band transaction notifications from iVeri.
    iVeri sends these for async transaction results (e.g., EcoCash delayed approval).

    Status codes:
      "0"   → SUCCESS (approved)
      "1"   → ERROR / timeout — leave PENDING for reconciliation
      "4"   → DECLINED — terminal, update to DECLINED
      "255" → INVALID_CARD — terminal, update to DECLINED
      other → DECLINED as safe default
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        logger.warning("CBZ callback: invalid JSON received")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    logger.info(
        "CBZ callback received",
        extra={"payload_preview": json.dumps(payload)[:500]},
    )

    txn_data = payload.get('Transaction', {})
    merchant_ref = txn_data.get('MerchantReference')

    if not merchant_ref:
        logger.warning("CBZ callback: no MerchantReference in payload")
        return JsonResponse({"error": "Missing MerchantReference"}, status=400)

    txn = CBZTransaction.objects.filter(merchant_reference=merchant_ref).first()
    if not txn:
        logger.warning("CBZ callback: transaction %s not found", merchant_ref)
        return JsonResponse({"error": "Transaction not found"}, status=404)

    result_code = str(txn_data.get('ResultCode') or '')
    status_text = txn_data.get('Status', '')
    status_label = IVERI_STATUS_MAP.get(result_code, 'UNKNOWN')

    # Persist all new data from callback, always storing the raw payload
    txn.result_code = result_code
    txn.result_description = txn_data.get('ResultDescription', '')
    txn.transaction_index = txn_data.get('TransactionIndex') or txn.transaction_index
    txn.authorisation_code = txn_data.get('AuthorisationCode') or txn.authorisation_code
    txn.bank_reference = txn_data.get('BankReference') or txn.bank_reference
    txn.consumer_order_id = txn_data.get('ConsumerOrderID') or txn.consumer_order_id
    txn.card_bin = txn_data.get('CardBin') or txn_data.get('BIN') or txn.card_bin
    txn.gateway_response = _scrub_pci_fields(payload)

    if status_label == 'SUCCESS' and (result_code == RESULT_CODE_SUCCESS and status_text == STATUS_APPROVED):
        # Idempotent: skip if already approved, still persist raw payload
        if txn.status == CBZTransaction.TransactionStatus.APPROVED:
            txn.save()
            logger.info(
                "CBZ callback: transaction %s already APPROVED — skipping payment record",
                merchant_ref,
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
                    "old_status": "PENDING",
                    "new_status": "APPROVED",
                    "gateway": "IVERI",
                    "result_code": result_code,
                },
            )
    elif status_label == 'ERROR' or result_code in IVERI_RETRIABLE_CODES:
        # Transient gateway error — leave transaction PENDING for reconciliation
        if txn.status in {
            CBZTransaction.TransactionStatus.INITIATED,
            CBZTransaction.TransactionStatus.PENDING,
        }:
            txn.status = CBZTransaction.TransactionStatus.PENDING
        txn.save()
        logger.warning(
            "CBZ callback: retriable error on %s (code=%s) — leaving PENDING",
            merchant_ref, result_code,
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
                "old_status": "PENDING",
                "new_status": "DECLINED",
                "gateway": "IVERI",
                "result_code": result_code,
                "status_label": status_label,
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
