# Omari Payment Integration

Django app for Omari Merchant API v1.2.0 (OTP-based payment flow).

## Overview
Omari uses a two-step OTP flow:
1. **Auth** – Initiate transaction, customer receives OTP via SMS/Email
2. **Request** – Customer enters OTP, payment is completed
3. **Query** (optional) – Check transaction status

## Environment Variables
Add to `.env`:
```bash
# Production: https://omari.v.co.zw/vsuite/omari/api/merchant/api/payment
# Sandbox: https://omari.v.co.zw/uat/vsuite/omari/api/merchant/api/payment
OMARI_API_BASE_URL=https://omari.v.co.zw/vsuite/omari/api/merchant/api/payment
OMARI_MERCHANT_KEY=your-api-key-here
```

## API Endpoints

### 1. POST /crm-api/payments/omari/auth/
Initiates transaction and triggers OTP.

**Request:**
```json
{
  "msisdn": "263774975187",
  "reference": "optional-uuid",  // auto-generated if omitted
  "amount": 3.50,
  "currency": "USD",  // ZWG or USD
  "channel": "WEB"    // optional, defaults to WEB (POS or WEB)
}
```

**Response:**
```json
{
  "error": false,
  "message": "Auth Success",
  "responseCode": "000",
  "otpReference": "ETDC",
  "reference": "9ee57919-b4f0-4d86-95ae-a1311ad1de7d"
}
```

### 2. POST /crm-api/payments/omari/request/
Validates OTP and completes payment.

**Request:**
```json
{
  "msisdn": "263774975187",
  "reference": "9ee57919-b4f0-4d86-95ae-a1311ad1de7d",
  "otp": "836066"
}
```

**Response:**
```json
{
  "error": false,
  "message": "Payment Success",
  "responseCode": "000",
  "paymentReference": "H5PSKURANNR1LKS7AJ0KV50KZG",
  "debitReference": "bc54b38257cf"
}
```

### 3. GET /crm-api/payments/omari/query/<reference>/
Checks transaction status.

**Response:**
```json
{
  "error": false,
  "message": "Success",
  "status": "Success",
  "responseCode": "000",
  "reference": "9ee57919-b4f0-4d86-95ae-a1311ad1de7d",
  "amount": 3.50,
  "currency": "USD",
  "channel": "WEB",
  "paymentReference": "H5PSKURANNR1LKS7AJ0KV50KZG",
  "debitReference": "bc54b38257cf",
  "created": "2024-09-20T16:27:40"
}
```

## Integration Flow
```
Frontend/Backend → POST /auth → Display OTP reference to user
User receives OTP via SMS/Email → enters OTP
Frontend/Backend → POST /request with OTP → Payment completed
(Optional) → GET /query/{reference} → Check status
```

## Response Codes
- `000` – Success
- Other codes indicate errors (check `message` field)

## Notes
- Mobile numbers must be in `2637XXXXXXXX` format
- `reference` must be UUID format
- Currency must be `ZWG` or `USD`
- Channel must be `POS` or `WEB`
- No webhook support in v1.2.0 spec (synchronous flow only)

## WhatsApp Integration

### Automatic OTP Flow
When integrated with WhatsApp conversations, the payment flow is fully automated:

1. **Initiate Payment** - Use the `initiate_omari_payment` flow action
2. **OTP Sent** - Customer receives SMS/Email with OTP
3. **Auto-Detection** - System automatically detects OTP replies
4. **Payment Complete** - Booking status updated automatically

### Flow Actions

#### `initiate_omari_payment`
Starts payment process in a WhatsApp flow.

**Parameters:**
```json
{
  "booking_reference": "{{ booking_reference }}",
  "amount": "{{ amount_to_pay }}",  // optional, defaults to balance
  "currency": "USD",  // optional, defaults to USD
  "channel": "WEB"    // optional, defaults to WEB
}
```

**Example Flow Step:**
```python
{
    'step_type': 'action',
    'config': {
        'actions_to_run': [{
            'action_type': 'initiate_omari_payment',
            'params_template': {
                'booking_reference': '{{ booking_reference }}',
                'amount': '{{ amount_to_pay }}',
                'currency': 'USD'
            }
        }]
    }
}
```

### Creating a Payment Flow

The Omari payment flow is defined in `flows/definitions/omari_payment_flow.py` following the standard flow pattern.

Load all flows into the database:
```bash
python manage.py load_flow_definitions
```

Trigger with keywords: `pay`, `payment`, `make payment`, `omari payment`  
Or via main menu: Type `menu` → Select "📱 Mobile Payment"

### How It Works

**User Flow:**
1. User: "pay"
2. Bot: "Please provide your booking reference"
3. User: "KS-2024-001"
4. Bot: "How much would you like to pay?"
5. User: "100"
6. Bot: "💳 Payment Initiated. OTP Reference: ABCD. Check your phone for OTP"
7. User: "123456" (enters OTP)
8. Bot: "✅ Payment Successful! Reference: H5PSKURANNR1LKS7AJ0KV50KZG"

**Behind the Scenes:**
- OTP detection happens automatically via `message_processor.py`
- Payment state stored in contact's `conversation_context`
- **Payment record created** in `customer_data.Payment` model with method='omari'
- Booking `amount_paid` manually updated within locked transaction for concurrency safety
- Booking `payment_status` updated on success:
  - `DEPOSIT_PAID` if partial payment
  - `PAID` if full amount paid
- Transaction logged in `OmariTransaction` model

### Canceling Payments

Users can cancel anytime by typing: `cancel`, `cancel payment`, `stop`, or `quit`

### Payment Records

When an Omari payment succeeds, the system automatically:
1. Locks the booking with `select_for_update()` for concurrent safety
2. Creates a `Payment` record in the database with:
   - `payment_method` = 'omari'
   - `status` = 'successful'
   - `transaction_reference` = Omari payment reference
   - `notes` = Includes debit reference from Omari
3. Updates the `Booking` within the locked transaction:
   - `amount_paid` is incremented by the payment amount
   - `payment_status` is updated based on total amount:
     - `PAID` when `amount_paid >= total_amount`
     - `DEPOSIT_PAID` when `amount_paid > 0` but less than total
     - `PENDING` when no payments made yet
4. **Updates booking reference to shared format** (if applicable):
   - If booking has a `tour_id` and `start_date`, reference updates to `BK-T{tour_id}-{YYYYMMDD}`
   - Groups all users booking the same tour on the same date
   - Example: `BK-T005-20260210` for Tour ID 5 on Feb 10, 2026
   - Idempotent - won't update if already in shared format

This ensures full payment tracking, audit trail, and concurrency safety for all Omari transactions.

### Booking Reference Grouping

After payment, bookings for the same tour and date share a common reference:

**Example:**
- **Before Payment:**
  - User A: `BK12345678` (random)
  - User B: `BK87654321` (random)
  - Both booking "Victoria Falls Safari" starting Feb 10, 2026

- **After Payment:**
  - User A: `BK-T005-20260210` (shared)
  - User B: `BK-T005-20260210` (shared)
  - Both grouped together for easy management

**Benefits:**
- Easy to identify travelers on same tour/date
- Simplifies group coordination and logistics
- Tour operators can see all bookings at a glance
- Payment status tracked individually per customer

### Admin Monitoring

View all transactions in Django Admin:
- Navigate to: **Omari Payment Integration** → **Omari Transactions**
- Filter by status, currency, date
- Track OTP references and payment refs
- View linked bookings and payment records