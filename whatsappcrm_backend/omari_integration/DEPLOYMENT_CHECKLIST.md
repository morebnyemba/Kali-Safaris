# Omari Payment Integration - Deployment Checklist

Use this checklist to deploy the Omari payment integration to your environment.

## ✅ Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Obtain Omari Merchant API credentials (sandbox or production)
- [ ] Add to `.env` file:
  ```bash
  OMARI_API_BASE_URL=https://omari.v.co.zw/uat/vsuite/omari/api/merchant/api/payment
  OMARI_MERCHANT_KEY=your_merchant_key_here
  ```
- [ ] Restart Django server to load new environment variables

### 2. Database Setup
- [ ] Run migrations:
  ```bash
  cd d:\Projects\Kali-Safaris\whatsappcrm_backend
  python manage.py makemigrations omari_integration
  python manage.py migrate
  ```
- [ ] Verify `OmariTransaction` table created:
  ```bash
  python manage.py dbshell
  \dt omari_integration_omaritransaction
  ```

### 3. Flow Definitions
- [ ] Load all flow definitions:
  ```bash
  python manage.py load_flow_definitions
  ```
- [ ] Verify in Django admin:
  - Navigate to: **Flows** → **Flows**
  - Confirm "Omari Mobile Payment" flow exists
  - Check "Is Active" is enabled
  - Verify trigger keywords: `pay`, `payment`, `make payment`, `omari payment`

### 4. Main Menu Integration
- [ ] Test main menu flow:
  - Send WhatsApp message: `menu`
  - Verify "📱 Mobile Payment" option appears
  - Select option and confirm flow starts

### 5. Test Booking Reference
- [ ] Create a test booking in the system
- [ ] Note the booking reference (e.g., BK-SLYKER-TECH-20251023)
- [ ] Verify booking has:
  - Customer name
  - Total amount
  - Amount paid (can be 0)

## 🧪 Testing Checklist

### Test 1: Direct Keyword Trigger
- [ ] Send WhatsApp message: `pay`
- [ ] Verify bot responds with welcome message
- [ ] Verify bot asks for booking reference

### Test 2: Menu Navigation
- [ ] Send: `menu`
- [ ] Select: "📱 Mobile Payment"
- [ ] Verify flow starts correctly

### Test 3: Invalid Booking Reference
- [ ] Start payment flow
- [ ] Enter invalid booking reference: `INVALID123`
- [ ] Verify error message appears
- [ ] Verify flow ends gracefully

### Test 4: Valid Booking Reference
- [ ] Start payment flow
- [ ] Enter valid booking reference
- [ ] Verify booking details displayed:
  - Tour name
  - Total amount
  - Amount paid
  - Balance due
- [ ] Verify bot asks for payment amount

### Test 5: Amount Validation
- [ ] Enter invalid amount: `abc`
- [ ] Verify re-prompt message appears
- [ ] Enter valid amount: `50`
- [ ] Verify bot asks for payment channel

### Test 6: Payment Channel Selection
- [ ] Verify 3 buttons appear:
  - Ecocash
  - OneMoney
  - ZimSwitch
- [ ] Select a channel
- [ ] Verify bot asks for phone number

### Test 7: Phone Number Validation
- [ ] Enter invalid number: `0771234567`
- [ ] Verify re-prompt message
- [ ] Enter valid number: `263771234567`
- [ ] Verify payment initiation

### Test 8: OTP Flow (Sandbox)
- [ ] Verify OTP reference shown in message
- [ ] Check SMS for OTP (if using real credentials)
- [ ] Enter sandbox OTP (check Omari docs for test OTP)
- [ ] Verify payment success message

### Test 9: Payment Cancellation
- [ ] Start payment flow
- [ ] Proceed to OTP step
- [ ] Type: `cancel`
- [ ] Verify cancellation message
- [ ] Verify flow ends

### Test 10: Database Verification
- [ ] Navigate to Django admin
- [ ] Go to: **Omari Payment Integration** → **Omari Transactions**
- [ ] Verify transaction record created with:
  - Reference (UUID)
  - Phone number (msisdn)
  - Amount and currency
  - Status (INITIATED → OTP_SENT → SUCCESS/FAILED)
  - OTP reference
  - Payment reference (if successful)
  - Linked booking

### Test 11: Booking Update
- [ ] After successful payment, check booking in admin
- [ ] Verify `amount_paid` increased by payment amount
- [ ] Verify `payment_status` updated (PAID or PARTIAL)

## 🔧 Production Deployment Checklist

### 1. Configuration
- [ ] Update `.env` with production URL:
  ```bash
  OMARI_API_BASE_URL=https://omari.v.co.zw/vsuite/omari/api/merchant/api/payment
  ```
- [ ] Update `OMARI_MERCHANT_KEY` with production key
- [ ] Restart application servers

### 2. Security
- [ ] Verify merchant key NOT in version control
- [ ] Confirm HTTPS enabled on all endpoints
- [ ] Test API rate limits
- [ ] Set up error monitoring (Sentry, etc.)

### 3. Monitoring
- [ ] Configure alerts for:
  - Failed payment attempts
  - API errors
  - High transaction volumes
- [ ] Set up logging for all Omari API calls
- [ ] Create dashboard for payment metrics

### 4. User Communication
- [ ] Update help documentation
- [ ] Notify users about new payment option
- [ ] Provide support contact for OTP issues

### 5. Backup Plan
- [ ] Document rollback procedure
- [ ] Test fallback to manual payment
- [ ] Verify queued payments (if using Celery)

## 📊 Post-Deployment Verification

### Week 1
- [ ] Monitor transaction success rate
- [ ] Review error logs
- [ ] Collect user feedback
- [ ] Check API performance

### Week 2-4
- [ ] Analyze payment patterns
- [ ] Optimize error messages if needed
- [ ] Review cancellation rate
- [ ] Update documentation based on issues

## 🐛 Troubleshooting Quick Reference

### Issue: Flow doesn't start
**Check:**
- Flow is active in admin
- Trigger keywords correct
- `load_flow_definitions` was run

### Issue: OTP not received
**Check:**
- Phone number format (2637XXXXXXXX)
- Merchant key is valid
- Using correct API URL (sandbox vs production)

### Issue: Payment fails after OTP
**Check:**
- OTP is correct (4-6 digits)
- Transaction status in admin
- Omari API response code
- Check `error_message` field in transaction

### Issue: Booking not updated
**Check:**
- Transaction has booking FK
- Booking exists in database
- Check `amount_paid` and `payment_status` fields

## 📞 Support Contacts

**Omari Support:**
- Documentation: Omari Merchant API v1.2.0
- Email: support@omari.v.co.zw (verify)

**Internal:**
- Django Admin: `/admin/`
- Logs: Check application logs for errors
- Database: Query `OmariTransaction` table

## ✅ Sign-Off

- [ ] All tests passed
- [ ] Production deployment complete
- [ ] Monitoring configured
- [ ] Team trained on new feature
- [ ] Documentation updated

**Deployed by:** _______________  
**Date:** _______________  
**Environment:** [ ] Sandbox [ ] Production
