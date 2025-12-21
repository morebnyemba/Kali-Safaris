# Omari Payment Integration - Deployment Guide

This guide walks you through deploying and testing the Omari payment integration with WhatsApp.

## Prerequisites

- Django backend running
- WhatsApp Business API configured via `meta_integration`
- PostgreSQL database
- Omari Merchant API credentials (sandbox or production)

## Step 1: Run Database Migrations

```bash
cd d:\Projects\Kali-Safaris\whatsappcrm_backend
python manage.py makemigrations omari_integration
python manage.py migrate
```

This creates the `OmariTransaction` table to track payment transactions.

## Step 2: Configure Environment Variables

Add to your `.env` file:

```bash
# Omari Payment Integration
OMARI_API_BASE_URL=https://omari.v.co.zw/uat/vsuite/omari/api/merchant/api/payment
OMARI_MERCHANT_KEY=your_merchant_key_here
```

**For Production:**
```bash
OMARI_API_BASE_URL=https://omari.v.co.zw/vsuite/omari/api/merchant/api/payment
```

## Step 3: Load Flow Definitions

Load all flow definitions including the Omari payment flow:

```bash
python manage.py load_flow_definitions
```

This will create or update all flows in the database, including:
- Omari Payment Flow (triggered by: `pay`, `payment`, `make payment`, `omari payment`)
- Main Menu with Mobile Payment option

You can also access the flow from the main menu by typing `menu` and selecting "📱 Mobile Payment".

## Step 4: Test the Payment Flow

### 4.1 Start Payment Conversation

Send a WhatsApp message to your bot:
```
pay
```

### 4.2 Expected Flow

**Bot:** "Welcome! To make a payment via Omari, I'll need your booking reference and amount."

**You:** "BOOK12345"

**Bot:** "Great! How much would you like to pay?"

**You:** "50"

**Bot:** "Payment initiated! Reference: [uuid]. Please enter the OTP sent to your phone via SMS."

**You:** "123456" (enter the OTP from SMS)

**Bot:** "Payment successful! Amount: $50.00. Your booking has been updated."

### 4.3 Check Database

```bash
python manage.py shell
```

```python
from omari_integration.models import OmariTransaction
from customer_data.models import Booking

# Check transaction
transaction = OmariTransaction.objects.latest('created_at')
print(f"Status: {transaction.status}")
print(f"Reference: {transaction.reference}")
print(f"OTP Ref: {transaction.otp_reference}")
print(f"Payment Ref: {transaction.payment_reference}")

# Check booking update
booking = transaction.booking
print(f"Amount Paid: {booking.amount_paid}")
print(f"Payment Status: {booking.payment_status}")
```

## Step 5: Admin Monitoring

1. Navigate to Django Admin: `http://localhost:8000/admin/`
2. Go to: **Omari Payment Integration** → **Omari Transactions**
3. View all payment attempts with:
   - Reference (UUID)
   - Phone number (msisdn)
   - Amount and currency
   - Status (INITIATED → OTP_SENT → SUCCESS/FAILED)
   - OTP reference
   - Payment reference
   - Linked booking
   - Timestamps

## Troubleshooting

### OTP Not Received

**Issue:** User doesn't receive OTP SMS

**Solutions:**
- Verify phone number format: `2637XXXXXXXX` (Zimbabwe format)
- Check `OMARI_MERCHANT_KEY` is valid
- Confirm you're using sandbox URL for testing
- Check Omari API status

### Payment Fails After OTP

**Issue:** OTP entered but payment fails

**Checks:**
1. View transaction in admin:
   ```python
   transaction = OmariTransaction.objects.get(reference='uuid-here')
   print(transaction.error_message)
   ```

2. Check Omari API response:
   - `responseCode: '000'` = Success
   - Other codes = Check API documentation

3. Verify OTP is correct (4-6 digits)

### Flow Doesn't Trigger

**Issue:** Bot doesn't respond to "pay" keyword

**Solutions:**
- Confirm flows were loaded: `python manage.py load_flow_definitions`
- Check flow status in admin (must be active)
- Verify keywords: `pay`, `payment`, `make payment`, `omari payment`
- Or access via main menu: Type `menu` → Select "📱 Mobile Payment"
- Check `flows/services.py` has `process_payment_message()` integration

### Booking Not Updated

**Issue:** Payment succeeds but booking doesn't update

**Debug:**
```python
from omari_integration.models import OmariTransaction

transaction = OmariTransaction.objects.get(reference='uuid-here')
print(f"Booking: {transaction.booking}")
print(f"Booking Amount Paid: {transaction.booking.amount_paid}")
```

**Check:**
- `OmariTransaction.booking` is not null
- `Booking.amount_paid` increased
- `Booking.payment_status` changed to 'PAID' or 'PARTIAL'

## Testing with Sandbox

### Get Sandbox Credentials

Contact Omari support to get:
- Sandbox merchant key
- Test phone numbers (Omari provides test numbers that don't send real SMS)

### Sandbox URL

```bash
OMARI_API_BASE_URL=https://omari.v.co.zw/uat/vsuite/omari/api/merchant/api/payment
```

### Test OTPs

Sandbox may use fixed OTPs like `123456` for all transactions. Check Omari sandbox documentation.

## Production Deployment

### 1. Update Environment

```bash
OMARI_API_BASE_URL=https://omari.v.co.zw/vsuite/omari/api/merchant/api/payment
OMARI_MERCHANT_KEY=your_production_key
```

### 2. Security Checklist

- [ ] Merchant key stored in environment variables (not hardcoded)
- [ ] HTTPS enabled on all endpoints
- [ ] Database backups configured
- [ ] Transaction logging enabled
- [ ] Error monitoring setup (Sentry, etc.)

### 3. Monitoring

Set up alerts for:
- Failed payment attempts
- API errors (check `OmariTransaction.error_message`)
- High transaction volumes

### 4. User Communication

- Inform users they'll receive OTP via SMS (not WhatsApp)
- Provide support contact for OTP issues
- Set timeout expectations (OTP usually arrives within 1-2 minutes)

## API Rate Limits

Check Omari documentation for:
- Maximum requests per minute
- Concurrent payment limits
- Retry policies

## Support

**Omari Support:**
- Documentation: [Omari Merchant API v1.2.0]
- Email: support@omari.v.co.zw (verify actual contact)

**Integration Issues:**
- Check transaction table: `OmariTransaction.objects.filter(status='FAILED')`
- Review Django logs
- Test endpoints directly:
  ```bash
  curl -X POST http://localhost:8000/crm-api/payments/omari/auth/ \
    -H "Content-Type: application/json" \
    -d '{"msisdn": "263771234567", "reference": "TEST123", "amount": 10.00, "currency": "USD", "channel": "ECOCASH"}'
  ```

## Next Steps

1. **Custom Flow:** Modify `flows/scripts/create_omari_payment_flow.py` to match your booking system
2. **Multi-Currency:** Test USD, ZWL, ZAR currencies
3. **Channel Selection:** Let users choose payment channel (ECOCASH, ONEMONEY, ZIPIT)
4. **Notifications:** Send confirmation emails/SMS after successful payments
5. **Refunds:** Implement refund flow if needed (check Omari API capabilities)

## Security Notes

- Never log OTP codes
- Encrypt transaction data if storing sensitive info
- Rate-limit payment attempts per user
- Implement fraud detection (multiple failed attempts, etc.)
- Validate booking ownership before payment

## Performance

- OTP validation happens synchronously (user waits for API response)
- Consider caching merchant auth token if Omari supports it
- Monitor API response times

## Backup Plan

If Omari API is down:
- Queue payment attempts with Celery
- Notify users of delays
- Fallback to manual payment methods
- Check status with query endpoint when API recovers
