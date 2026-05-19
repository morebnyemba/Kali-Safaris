"""
Custom flow actions for Omari payment integration.

Register with: from omari_integration.flow_actions import register_payment_actions
Then call: register_payment_actions()
"""
import logging
import requests
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any
from django.utils import timezone

from conversations.models import Contact
from customer_data.models import Booking, Payment
from .whatsapp_handler import get_payment_handler


logger = logging.getLogger(__name__)


def initiate_omari_payment_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """
    Flow action to initiate Omari payment through WhatsApp.
    
    Params expected:
        - booking_reference: str (required) - Booking reference to pay for
        - amount: str/float (optional) - Amount to charge, defaults to booking balance
        - currency: str (optional) - 'USD' or 'ZWG', defaults to 'USD'
        - channel: str (optional) - 'WEB' or 'POS', defaults to 'WEB'
    
    Returns actions to send OTP instructions to customer.
    """
    booking_ref = params.get('booking_reference')
    if not booking_ref:
        # Try to get from flow context
        booking_ref = flow_context.get('booking_reference')
    
    if not booking_ref:
        logger.error(f"initiate_omari_payment action: missing booking_reference for contact {contact.id}")
        return [{
            'type': 'send_text',
            'text': '❌ Payment initiation failed: No booking found. Please contact support.'
        }]
    
    logger.info(
        "initiate_omari_payment action start | contact=%s booking_ref=%s amount_param=%s currency=%s channel=%s",
        contact.id,
        booking_ref,
        params.get('amount'),
        params.get('currency'),
        params.get('channel'),
    )

    # Get booking (scoped to customer to handle multiple bookings with same reference)
    try:
        booking = Booking.objects.get(booking_reference=booking_ref, customer=contact.customer_profile)
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_ref} not found for payment initiation | contact={contact.id}")
        return [{
            'type': 'send_text',
            'text': f'❌ Booking {booking_ref} not found. Please verify your booking reference.'
        }]
    except Booking.MultipleObjectsReturned:
        logger.error(f"Multiple bookings found for {booking_ref} and customer {contact.customer_profile.id}")
        return [{
            'type': 'send_text',
            'text': f'❌ Payment system error. Please contact support.'
        }]
    
    # Determine amount
    amount_str = params.get('amount')
    if amount_str:
        try:
            amount = Decimal(str(amount_str))
        except (InvalidOperation, ValueError, TypeError):
            logger.error(f"Invalid amount '{amount_str}' for payment")
            amount = booking.total_amount - booking.amount_paid
    else:
        # Default to remaining balance
        amount = booking.total_amount - booking.amount_paid
    
    if amount <= 0:
        logger.info("initiate_omari_payment action: booking %s already paid for contact %s", booking_ref, contact.id)
        return [{
            'type': 'send_text',
            'text': f'✅ Booking {booking_ref} is already paid in full!'
        }]
    
    currency = params.get('currency', 'USD')
    channel = params.get('channel', 'WEB')
    
    # Get payment phone from flow context (user-entered phone), fallback to contact phone
    payment_phone = params.get('msisdn') or flow_context.get('payment_phone', contact.whatsapp_id)
    
    # Initiate payment with exception handling
    handler = get_payment_handler()
    try:
        result = handler.initiate_payment(
            contact=contact,
            booking=booking,
            amount=amount,
            currency=currency,
            channel=channel,
            msisdn=payment_phone
        )
    except Exception as exc:
        logger.error(
            "initiate_omari_payment action: payment handler exception | contact=%s booking_ref=%s error=%s",
            contact.id,
            booking_ref,
            exc,
            exc_info=True,
        )
        return [{
            'type': 'send_text',
            'text': f'❌ Payment service error: {str(exc)}\nPlease try again or contact support.'
        }]
    
    if result['success']:
        otp_ref = result.get('otp_reference', 'N/A')
        logger.info(
            "initiate_omari_payment action success | contact=%s booking_ref=%s reference=%s otp_ref=%s amount=%s %s",
            contact.id,
            booking_ref,
            result.get('reference'),
            otp_ref,
            amount,
            currency,
        )
        message = (
            f"💳 *Payment Initiated*\n\n"
            f"Booking: {booking.booking_reference}\n"
            f"Amount: {currency} {amount}\n\n"
            f"🔐 *OTP Reference: {otp_ref}*\n\n"
            f"Please check your phone for an OTP code via SMS/Email.\n"
            f"Reply with your OTP code to complete the payment."
        )
        
        # Store in context for next step
        # CRITICAL: flow transition checks for variable_exists omari_otp_reference
        flow_context['omari_otp_reference'] = result.get('otp_reference')
        flow_context['_payment_reference'] = result['reference']
        
        return [{
            'type': 'send_text',
            'text': message
        }]
    else:
        error_msg = result.get('message', 'Unknown error')
        logger.error(
            "Payment initiation failed for booking %s contact=%s reference=%s: %s",
            booking_ref,
            contact.id,
            result.get('reference'),
            error_msg,
        )
        return [{
            'type': 'send_text',
            'text': f'❌ Payment initiation failed: {error_msg}\nPlease try again or contact support.'
        }]


def verify_omari_user_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """
    Flow action to verify if the current contact is an eligible Omari user.
    Sets flow_context['is_omari_user'] to True/False. Returns no messages.
    """
    handler = get_payment_handler()
    logger.info("verify_omari_user action start | contact=%s", contact.id)
    try:
        eligibility = handler.is_omari_user(contact)  # 'true' or 'unknown'
        flow_context['is_omari_user'] = eligibility
        logger.info("verify_omari_user action result | contact=%s eligibility=%s", contact.id, eligibility)
    except Exception as exc:  # pragma: no cover - defensive
        flow_context['is_omari_user'] = 'unknown'
        logger.error("verify_omari_user action failed | contact=%s error=%s", contact.id, exc, exc_info=True)
    return []

def set_omari_not_eligible_message_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """Set a shared message explaining Omari eligibility requirements."""
    flow_context['omari_not_eligible_message'] = (
        "Omari payments are available to Omari users only. It looks like your number isn't "
        "linked to an Omari account. Please choose another payment method (e.g., Ecocash/"
        "Innbucks via Paynow) or link your Omari account first."
    )
    return []


def process_otp_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """
    Flow action to process OTP input from customer.
    
    This should be called when customer sends a message while awaiting OTP.
    Params expected:
        - otp: str (required) - The OTP code from user input
    
    Returns actions to confirm payment or show error.
    """
    # Detailed debugging info
    logger.info(
        "=== process_otp_action START === | contact=%s | params=%s | context_keys=%s",
        contact.id,
        {k: ('***' + str(v)[-2:] if k == 'otp' and v else v) for k, v in params.items()},
        list(flow_context.keys())
    )
    
    # Mask sensitive OTP data in params for logging
    otp_from_params = params.get('otp', '')
    masked_otp = '***' + otp_from_params[-2:] if otp_from_params and len(otp_from_params) >= 2 else '<not set>'
    
    otp_input_var = flow_context.get('otp_input', '')
    masked_otp_input = '***' + otp_input_var[-2:] if otp_input_var and len(otp_input_var) >= 2 else '<not set>'
    
    logger.info(
        "process_otp_action called | contact=%s params_otp=%s otp_input_var=%s",
        contact.id,
        masked_otp,
        masked_otp_input
    )
    
    otp = params.get('otp')
    if not otp:
        # Try to get from flow context (captured from user message)
        otp = flow_context.get('user_message', '').strip()
        logger.debug(f"OTP not in params, trying user_message: {otp[:2]}*** (len={len(otp) if otp else 0})")
    
    logger.info(
        "process_otp_action: resolved OTP | contact=%s otp=%s (length=%s, is_digit=%s)",
        contact.id,
        '***' + otp[-2:] if otp and len(otp) >= 2 else '<empty>',
        len(otp) if otp else 0,
        otp.isdigit() if otp else False
    )
    
    if not otp:
        logger.warning("process_otp_action: no OTP provided | contact=%s | flow_context=%s", contact.id, {k: v for k, v in flow_context.items() if k not in ['_payment_reference']})
        return [{
            'type': 'send_text',
            'text': '❌ Please provide your OTP code to complete the payment.'
        }]
    
    logger.info("process_otp_action: calling payment handler with OTP | contact=%s", contact.id)
    handler = get_payment_handler()
    
    try:
        result = handler.process_otp_input(contact, otp)
        logger.info(
            "process_otp_action: handler result | contact=%s success=%s message=%s response_code=%s",
            contact.id,
            result.get('success'),
            result.get('message', 'N/A'),
            result.get('response_code', 'N/A')
        )
    except Exception as e:
        logger.error(
            "process_otp_action: handler exception | contact=%s error=%s",
            contact.id,
            str(e),
            exc_info=True
        )
        result = {'success': False, 'message': f'Error processing OTP: {str(e)}'}
    
    if result['success']:
        booking = result.get('booking')
        payment_ref = result.get('payment_reference', 'N/A')
        
        logger.info(
            "process_otp_action: payment successful | contact=%s payment_ref=%s booking_id=%s",
            contact.id,
            payment_ref,
            booking.id if booking else 'N/A'
        )
        
        message = (
            f"✅ *Payment Successful!*\n\n"
            f"Payment Reference: {payment_ref}\n"
        )
        
        if booking:
            message += (
                f"Booking: {booking.booking_reference}\n"
                f"Status: {booking.get_payment_status_display()}\n"
                f"Amount Paid: {booking.currency if hasattr(booking, 'currency') else 'USD'} {booking.amount_paid}\n"
                f"Total: {booking.currency if hasattr(booking, 'currency') else 'USD'} {booking.total_amount}"
            )
        
        message += "\n\nThank you for your payment! 🎉"
        
        # Set success flag for flow transition
        flow_context['omari_payment_success'] = True
        logger.info(
            "process_otp_action: set context variable | contact=%s omari_payment_success=True",
            contact.id
        )
        
        # Clear payment state from context
        flow_context.pop('_payment_initiated', None)
        flow_context.pop('_payment_reference', None)
        
        logger.info("=== process_otp_action SUCCESS === | contact=%s", contact.id)
        return [{
            'type': 'send_text',
            'text': message
        }]
    else:
        error_msg = result.get('message', 'Payment processing failed')
        response_code = result.get('response_code', '')
        
        logger.warning(
            "process_otp_action: payment failed | contact=%s error=%s response_code=%s",
            contact.id,
            error_msg,
            response_code
        )
        
        message = f"❌ *Payment Failed*\n\n{error_msg}"
        if response_code and response_code != '000':
            message += f"\nError Code: {response_code}"
        message += "\n\nPlease try again or contact support."
        
        logger.info("=== process_otp_action FAILED === | contact=%s", contact.id)
        return [{
            'type': 'send_text',
            'text': message
        }]


def cancel_payment_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """
    Flow action to cancel pending payment.
    """
    handler = get_payment_handler()
    handler.cancel_payment(contact)
    
    # Clear from context
    flow_context.pop('_payment_initiated', None)
    flow_context.pop('_payment_reference', None)
    
    return [{
        'type': 'send_text',
        'text': '❌ Payment cancelled. You can initiate a new payment anytime.'
    }]


def validate_omari_phone_action(contact: Contact, flow_context: dict, params: dict) -> Dict[str, Any]:
    """
    Validate phone number format for Omari payment.
    
    Params expected:
        - phone_variable: str - Name of context variable containing phone number
    
    Returns context update with 'payment_phone_valid' if valid, otherwise empty dict.
    """
    import re
    
    phone_var = params.get('phone_variable', 'payment_phone')
    phone = flow_context.get(phone_var, '').strip()
    
    # Zimbabwe mobile format: 2637XXXXXXXX (12 digits total)
    PHONE_REGEX = r'^2637[0-9]{8}$'
    
    if not phone:
        logger.warning(
            "validate_omari_phone: no phone number in context | contact=%s variable=%s",
            contact.id,
            phone_var
        )
        return {}
    
    if re.match(PHONE_REGEX, phone):
        logger.info(
            "validate_omari_phone: valid format | contact=%s phone=***%s",
            contact.id,
            phone[-4:] if len(phone) >= 4 else "****"
        )
        # Return context update to set validation flag
        return {'payment_phone_valid': True}
    else:
        logger.warning(
            "validate_omari_phone: invalid format | contact=%s phone=***%s expected_format=2637XXXXXXXX",
            contact.id,
            phone[-4:] if len(phone) >= 4 else "****"
        )
        return {}


def initiate_zimswitch_payment_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """
    Flow action to initiate ZimSwitch (COPYandPAY) payment through WhatsApp.
    
    Params expected:
        - booking_reference: str (required) - Booking reference to pay for
        - amount: str/float (optional) - Amount to charge, defaults to booking balance
        - currency: str (optional) - 'USD' or 'ZWG', defaults to 'USD'
    
    Returns actions to send payment link to customer.
    """
    import json
    import requests
    from decimal import Decimal, InvalidOperation
    from cbz_integration.models import CBZTransaction
    from cbz_integration.views import _get_copyandpay_config
    
    booking_ref = params.get('booking_reference') or flow_context.get('booking_reference')
    if not booking_ref:
        logger.error(f"initiate_zimswitch_payment action: missing booking_reference for contact {contact.id}")
        return [{
            'type': 'send_text',
            'text': '❌ Payment initiation failed: No booking found. Please contact support.'
        }]
    
    try:
        booking = Booking.objects.get(booking_reference=booking_ref, customer=contact.customer_profile)
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_ref} not found for zimswitch payment | contact={contact.id}")
        return [{
            'type': 'send_text',
            'text': f'❌ Booking {booking_ref} not found. Please verify your booking reference.'
        }]
    
    # Determine amount
    amount_str = params.get('amount')
    if amount_str:
        try:
            amount = Decimal(str(amount_str))
        except (InvalidOperation, ValueError, TypeError):
            amount = booking.total_amount - booking.amount_paid
    else:
        amount = booking.total_amount - booking.amount_paid
    
    if amount <= 0:
        logger.info("zimswitch payment: booking %s already paid for contact %s", booking_ref, contact.id)
        return [{
            'type': 'send_text',
            'text': f'✅ Booking {booking_ref} is already paid in full!'
        }]
    
    currency = params.get('currency', 'USD')
    
    # Get COPYandPAY config
    config = _get_copyandpay_config()
    if not config['entity_id'] or not config['bearer_token']:
        logger.error("ZimSwitch payment: COPYandPAY not configured for contact %s", contact.id)
        return [{
            'type': 'send_text',
            'text': '❌ Payment system not configured. Please contact support.'
        }]
    
    # Generate merchant reference
    import uuid
    merchant_ref = f"WA-ZS-{uuid.uuid4().hex[:10].upper()}"
    
    # Create transaction record
    txn = CBZTransaction.objects.create(
        merchant_reference=merchant_ref,
        payment_type=CBZTransaction.PaymentType.CARD,
        amount=amount,
        currency=currency,
        command='Debit',
        status=CBZTransaction.TransactionStatus.INITIATED,
        booking=booking,
    )
    
    # Prepare COPYandPAY checkout
    request_data = {
        'entityId': config['entity_id'],
        'amount': f"{amount:.2f}",
        'currency': currency,
        'paymentType': 'DB',
        'merchantTransactionId': merchant_ref,
    }
    if config['test_mode']:
        request_data['testMode'] = config['test_mode']
    
    headers = {
        'Authorization': f"Bearer {config['bearer_token']}",
    }
    endpoint = f"{config['base_url']}/v1/checkouts"
    
    try:
        response = requests.post(endpoint, data=request_data, headers=headers, timeout=60)
        data = response.json() if response.status_code < 400 else {}
        
        checkout_id = str(data.get('id') or '').strip()
        result_code = str(data.get('result', {}).get('code', '')).strip()
        
        txn.request_id = checkout_id or txn.request_id
        txn.result_code = result_code or txn.result_code
        
        if response.status_code >= 400 or not checkout_id:
            txn.status = CBZTransaction.TransactionStatus.FAILED
            txn.save()
            logger.error("ZimSwitch checkout failed | contact=%s merchant_ref=%s status=%s", 
                        contact.id, merchant_ref, response.status_code)
            return [{
                'type': 'send_text',
                'text': f'❌ Payment system error: {data.get("result", {}).get("description", "Unable to prepare checkout")}. Please try again.'
            }]
        
        txn.save()
        
        # Store payment state
        payment_state = {
            'merchant_reference': merchant_ref,
            'booking_id': booking.id,
            'amount': str(amount),
            'currency': currency,
            'checkout_id': checkout_id,
            'awaiting_payment': True,
            'initiated_at': timezone.now().isoformat(),
        }
        
        logger.info(
            "ZimSwitch payment initiated | contact=%s booking=%s merchant_ref=%s checkout_id=%s amount=%s %s",
            contact.id,
            booking_ref,
            merchant_ref,
            checkout_id,
            amount,
            currency,
        )
        
        # Build payment link (resourcePath is the checkout ID path)
        payment_link = f"https://backend.kalaisafaris.com/crm-api/payments/cbz/copyandpay/status/?resourcePath=/v1/checkouts/{checkout_id}&merchant_reference={merchant_ref}"
        
        return [{
            'type': 'send_text',
            'text': f"""💳 *ZimSwitch Card Payment*

Amount: *${amount:.2f}* {currency}
Booking: *{booking_ref}*

Secure payment link (valid for 15 minutes):
{payment_link}

After payment:
✅ You'll see a confirmation on the website
✅ We'll update your booking status automatically
✅ You'll receive a WhatsApp confirmation

Questions? Reply with your concern or contact support."""
        }]
        
    except Exception as e:
        logger.exception("ZimSwitch payment initiation error | contact=%s booking_ref=%s", contact.id, booking_ref)
        txn.status = CBZTransaction.TransactionStatus.FAILED
        txn.save()
        return [{
            'type': 'send_text',
            'text': f'❌ Payment error: {str(e)}. Please try again or contact support.'
        }]


def poll_zimswitch_payment_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """
    Flow action to poll ZimSwitch payment status from COPYandPAY.
    
    Params expected:
        - merchant_reference: str (required) - Merchant reference to query
        - checkout_id: str (required) - COPYandPAY checkout ID
    
    Returns actions to send payment status to customer.
    """
    merchant_ref = params.get('merchant_reference') or flow_context.get('merchant_reference')
    checkout_id = params.get('checkout_id') or flow_context.get('checkout_id')
    
    if not merchant_ref or not checkout_id:
        logger.warning("poll_zimswitch_payment: missing parameters | contact=%s", contact.id)
        return [{
            'type': 'send_text',
            'text': '❌ Unable to check payment status. Missing transaction reference.'
        }]
    
    from cbz_integration.models import CBZTransaction
    from cbz_integration.views import _get_copyandpay_config, _copyandpay_result_code, _copyandpay_is_approved, _copyandpay_is_pending
    
    try:
        # Find transaction
        txn = CBZTransaction.objects.filter(merchant_reference=merchant_ref).first()
        if not txn:
            logger.warning("poll_zimswitch_payment: transaction not found | merchant_ref=%s", merchant_ref)
            return [{
                'type': 'send_text',
                'text': '❌ Payment transaction not found.'
            }]
        
        # Get COPYandPAY config
        config = _get_copyandpay_config()
        if not config['entity_id'] or not config['bearer_token']:
            return [{
                'type': 'send_text',
                'text': '❌ Payment system not configured. Please contact support.'
            }]
        
        # Query payment status
        headers = {
            'Authorization': f"Bearer {config['bearer_token']}",
        }
        resource_path = f"/v1/checkouts/{checkout_id}"
        endpoint = f"{config['base_url']}{resource_path}"
        
        response = requests.get(
            endpoint,
            params={'entityId': config['entity_id']},
            headers=headers,
            timeout=60,
        )
        
        data = response.json() if response.status_code < 400 else {}
        result_code = _copyandpay_result_code(data)
        is_approved = _copyandpay_is_approved(result_code)
        is_pending = _copyandpay_is_pending(result_code)
        
        # Update transaction
        txn.result_code = result_code or txn.result_code
        
        if is_approved:
            txn.status = CBZTransaction.TransactionStatus.APPROVED
            txn.completed_at = timezone.now()
            txn.save()
            
            # Record payment if not already recorded
            if txn.booking:
                existing_payment = Payment.objects.filter(
                    booking=txn.booking,
                    transaction_reference=merchant_ref,
                ).exists()
                if not existing_payment:
                    from cbz_integration.views import _record_payment
                    _record_payment(txn, txn.booking)
            
            logger.info("ZimSwitch payment approved | contact=%s merchant_ref=%s", contact.id, merchant_ref)
            return [{
                'type': 'send_text',
                'text': f"""✅ *Payment Successful!*

Your ZimSwitch payment has been approved!

Booking: *{txn.booking.booking_reference if txn.booking else 'N/A'}*
Amount: *${txn.amount}* {txn.currency}
Reference: {merchant_ref}

Your booking is now confirmed. Thank you for choosing Kali Safaris!"""
            }]
        
        elif is_pending:
            txn.status = CBZTransaction.TransactionStatus.PENDING
            txn.save()
            logger.info("ZimSwitch payment pending | contact=%s merchant_ref=%s", contact.id, merchant_ref)
            return [{
                'type': 'send_text',
                'text': f"""⏳ *Payment Pending*

Your payment is still processing. Please wait a few moments and try checking status again.

If you continue to experience issues, please reply with your booking reference."""
            }]
        
        else:
            txn.status = CBZTransaction.TransactionStatus.DECLINED
            txn.save()
            logger.warning("ZimSwitch payment declined | contact=%s merchant_ref=%s result_code=%s", 
                          contact.id, merchant_ref, result_code)
            return [{
                'type': 'send_text',
                'text': f"""❌ *Payment Declined*

Your payment could not be processed.

Please try again with a different card or payment method. If you need help, reply with your booking reference."""
            }]
    
    except Exception as e:
        logger.exception("poll_zimswitch_payment error | contact=%s merchant_ref=%s", contact.id, merchant_ref)
        return [{
            'type': 'send_text',
            'text': f'⚠️ Unable to check payment status. Error: {str(e)}. Please try again.'
        }]


def register_payment_actions():
    """Register Omari payment actions with the flow action registry."""
    from flows.services import flow_action_registry

    flow_action_registry.register('initiate_omari_payment', initiate_omari_payment_action)
    flow_action_registry.register('initiate_zimswitch_payment', initiate_zimswitch_payment_action)
    flow_action_registry.register('poll_zimswitch_payment', poll_zimswitch_payment_action)
    flow_action_registry.register('verify_omari_user', verify_omari_user_action)
    flow_action_registry.register('set_omari_not_eligible_message', set_omari_not_eligible_message_action)
    flow_action_registry.register('process_otp', process_otp_action)
    flow_action_registry.register('cancel_payment', cancel_payment_action)
    flow_action_registry.register('validate_omari_phone', validate_omari_phone_action)

    logger.info("Registered Omari payment flow actions")

