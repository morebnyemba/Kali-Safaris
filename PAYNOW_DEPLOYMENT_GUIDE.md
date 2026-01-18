# Paynow Payment Integration - Deployment Guide

## Overview
This guide covers the deployment and configuration of the Paynow payment integration for the Kali Safaris booking flow.

## Changes Summary

### 1. Payment Model Enhancement
- Added three new Paynow payment methods:
  - `paynow_ecocash` - Paynow - Ecocash
  - `paynow_onemoney` - Paynow - OneMoney
  - `paynow_innbucks` - Paynow - Innbucks

### 2. Booking Flow Updates
- Added "Mobile Money (Paynow)" section to payment options
- Integrated WhatsApp payment flow for collecting payment details
- Added automated payment initiation after user submits payment details
- Proper error handling and user feedback

### 3. New Webhook Endpoints
- **Payment Flow Webhook**: `/crm-api/flows/paynow-payment-webhook/`
  - Handles WhatsApp flow data exchanges
  - Initiates Paynow payments
  - Returns success/error screens
  
- **Paynow IPN Handler**: `/crm-api/paynow/ipn/`
  - Receives payment status callbacks from Paynow
  - Updates Payment records
  - Verifies IPN hash for security

### 4. Services and Actions
- Enhanced `PaynowService` with `initiate_payment()` method
- New `initiate_paynow_payment` flow action
- Automatic Payment record creation and tracking

## Deployment Steps

### Step 1: Run Database Migrations

```bash
cd whatsappcrm_backend
source venv/bin/activate
python manage.py migrate customer_data
```

This will apply the migration that adds new payment method choices.

### Step 2: Configure Paynow Settings

1. Log in to Django Admin
2. Navigate to **Paynow Integration** → **Paynow Configurations**
3. Create or update the configuration with:
   - **Integration ID**: Your Paynow integration ID from Paynow dashboard
   - **Integration Key**: Your Paynow integration key
   - **API Base URL**: `https://www.paynow.co.zw/interface/remotetransaction`

### Step 3: Update Environment Variables

Ensure `SITE_URL` is set in your `.env` file:

```env
SITE_URL=https://backend.kalaisafaris.com
```

This is used to construct webhook URLs for Paynow callbacks.

### Step 4: Create WhatsApp Payment Flow

1. **Export the Flow Definition**:
   ```bash
   cd whatsappcrm_backend
   python manage.py shell
   ```
   
   In the Python shell:
   ```python
   from flows.definitions.payment_whatsapp_flow import PAYMENT_WHATSAPP_FLOW
   import json
   
   # Export to file
   with open('/tmp/payment_flow.json', 'w') as f:
       json.dump(PAYMENT_WHATSAPP_FLOW, f, indent=2)
   
   print("Flow exported to /tmp/payment_flow.json")
   ```

2. **Create Flow in Meta Flow Manager**:
   - Go to Meta Flow Manager: https://business.facebook.com/wa/manage/flows/
   - Create a new flow
   - Import or manually create the flow using the exported JSON as reference
   - **IMPORTANT**: Update `data_channel_uri` to match your environment:
     - Production: `https://backend.kalaisafaris.com/crm-api/flows/paynow-payment-webhook/`
     - Staging: `https://staging.kalaisafaris.com/crm-api/flows/paynow-payment-webhook/`
     - Development: `http://localhost:8000/crm-api/flows/paynow-payment-webhook/` (requires ngrok or similar for local testing)
   - Publish the flow

3. **Create WhatsAppFlow Record**:
   In Django admin:
   - Navigate to **Flows** → **WhatsApp Flows**
   - Create new record:
     - **Name**: `payment_whatsapp_flow`
     - **Flow ID**: (Copy from Meta Flow Manager)
     - **Sync Status**: `published`
     - **Status**: `PUBLISHED`

### Step 5: Configure Paynow Webhook URLs

In your Paynow merchant dashboard:

1. Set **Result URL** (IPN): `https://backend.kalaisafaris.com/crm-api/paynow/ipn/`
2. Set **Return URL**: `https://backend.kalaisafaris.com/crm-api/paynow/return/`

Note: For Express Checkout (mobile money), the Result URL is the most important as it receives payment status updates.

### Step 6: Test the Integration

1. **Test Booking Flow**:
   - Start a booking via WhatsApp
   - Complete traveler details
   - Select "Pay Full via Paynow" or "Pay 50% Deposit via Paynow"
   - Verify WhatsApp payment flow launches correctly

2. **Test Payment Collection**:
   - In the payment flow, select a payment method (e.g., Ecocash)
   - Enter a valid phone number (format: 263771234567)
   - Enter email address
   - Submit payment
   - Verify success screen shows payment instructions

3. **Test IPN Callbacks**:
   - Complete a real payment on mobile money
   - Check Django logs for IPN receipt
   - Verify Payment record status is updated to "successful"
   - Check booking's `amount_paid` field is updated

### Step 7: Verify Logs

Monitor the logs for any issues:

```bash
# In production
tail -f /var/log/django/app.log | grep -i paynow

# Or in Docker
docker logs -f whatsappcrm_backend | grep -i paynow
```

Look for:
- "Paynow payment webhook called"
- "Payment initiated successfully"
- "Paynow IPN received"
- "Payment X marked as successful"

## Testing Checklist

- [ ] Database migration applied successfully
- [ ] PaynowConfig created in admin with valid credentials
- [ ] SITE_URL environment variable set correctly
- [ ] WhatsApp payment flow published in Meta
- [ ] WhatsAppFlow record created in database
- [ ] Paynow webhook URLs configured in Paynow dashboard
- [ ] Booking flow shows Paynow payment options
- [ ] WhatsApp payment flow launches correctly
- [ ] Payment initiation works (check logs)
- [ ] IPN callbacks update payment status
- [ ] Payment records created with correct data
- [ ] Booking amount_paid updates after successful payment

## Troubleshooting

### Payment Flow Doesn't Launch

**Symptom**: User selects Paynow option but WhatsApp flow doesn't open

**Solutions**:
1. Check WhatsAppFlow record exists with name `payment_whatsapp_flow`
2. Verify flow is published in Meta
3. Check flow_id matches the one in Meta
4. Review logs for "payment_whatsapp_flow not found"

### Payment Initiation Fails

**Symptom**: Payment flow submits but shows error screen

**Solutions**:
1. Check Paynow credentials in PaynowConfig
2. Verify phone number format (should be 263XXXXXXXXX)
3. Review webhook logs for error details
4. Test Paynow SDK connection manually
5. Ensure paynow package is installed: `pip list | grep paynow`

### IPN Not Received

**Symptom**: Payment completes but status doesn't update

**Solutions**:
1. Verify IPN URL in Paynow dashboard
2. Check if URL is accessible from external networks
3. Review server logs for incoming POST requests to `/crm-api/paynow/ipn/`
4. Verify IPN hash verification isn't failing
5. Check firewall/security group rules allow Paynow IPs

### Hash Verification Fails

**Symptom**: IPN received but rejected with "Invalid IPN signature"

**Solutions**:
1. Verify integration_key in PaynowConfig matches Paynow dashboard
2. Check IPN data format matches expected fields
3. Review PaynowSDK.verify_ipn_callback implementation
4. Test hash calculation manually with known values

## Security Considerations

1. **Webhook Security**:
   - IPN webhook verifies hash signature
   - Payment flow webhook validates booking existence
   - Both use CSRF exempt but have other security checks

2. **Sensitive Data**:
   - Integration key stored in database (should be encrypted in production)
   - Phone numbers validated for format
   - Payment amounts verified against booking

3. **Production Recommendations**:
   - Use HTTPS for all webhook URLs
   - Set up rate limiting on webhook endpoints
   - Monitor for suspicious payment attempts
   - Implement webhook replay protection
   - Consider encrypting PaynowConfig sensitive fields

## Monitoring and Maintenance

### Key Metrics to Monitor

1. **Payment Success Rate**:
   - Track ratio of successful to failed payments
   - Alert if success rate drops below threshold

2. **IPN Processing Time**:
   - Monitor how quickly IPNs are processed
   - Alert on delays

3. **Payment Flow Completion Rate**:
   - Track how many users complete the payment flow
   - Identify drop-off points

### Database Queries for Monitoring

```python
# In Django shell
from customer_data.models import Payment

# Payment success rate (last 7 days)
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q

week_ago = timezone.now() - timedelta(days=7)
stats = Payment.objects.filter(
    created_at__gte=week_ago,
    payment_method__startswith='paynow_'
).aggregate(
    total=Count('id'),
    successful=Count('id', filter=Q(status='successful')),
    failed=Count('id', filter=Q(status='failed')),
    pending=Count('id', filter=Q(status='pending'))
)
print(f"Success rate: {stats['successful']}/{stats['total']}")

# Recent failed payments
failed_payments = Payment.objects.filter(
    status='failed',
    payment_method__startswith='paynow_'
).order_by('-created_at')[:10]

for payment in failed_payments:
    print(f"{payment.booking.booking_reference}: {payment.notes}")
```

## Support and Contact

For issues with this integration:
1. Check application logs first
2. Review this guide for common issues
3. Contact development team with:
   - Error messages from logs
   - Steps to reproduce
   - Affected booking references
   - Screenshots if applicable

## Rollback Plan

If issues arise, you can temporarily disable Paynow payments:

1. Remove Paynow options from booking flow:
   - Edit `flows/definitions/booking_flow.py`
   - Comment out Paynow payment options in `ask_payment_option` step
   - Restart application

2. Revert database migration if needed:
   ```bash
   python manage.py migrate customer_data 0007
   ```

3. Direct customers to alternative payment methods (Omari, Bank Transfer)
