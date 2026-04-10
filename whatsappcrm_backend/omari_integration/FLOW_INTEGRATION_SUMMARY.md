# Omari Payment Flow Integration - Summary

## ✅ What Was Done

Integrated the Omari payment flow following the existing flow definitions pattern used throughout the Kali Safaris WhatsApp CRM.

### Files Created/Modified

#### New Files:
1. **`flows/definitions/omari_payment_flow.py`** - Main flow definition with 18 steps
   - Entry point with welcome message
   - Booking lookup and validation
   - Amount collection with balance display
   - Payment channel selection (Ecocash/OneMoney/ZimSwitch)
   - Phone number validation (Zimbabwe format: 2637XXXXXXXX)
   - OTP collection and processing
   - Success/failure handling
   - Cancellation support

#### Modified Files:
1. **`flows/management/commands/load_flow_definitions.py`**
   - Added import: `from flows.definitions.omari_payment_flow import OMARI_PAYMENT_FLOW`
   - Added `OMARI_PAYMENT_FLOW` to `flow_definitions` list

2. **`flows/definitions/main_menu_flow.py`**
   - Added "📱 Mobile Payment" menu option
   - Added transition to `switch_to_omari_payment_flow`
   - Added `switch_to_omari_payment_flow` step

3. **`omari_integration/DEPLOYMENT.md`**
   - Updated Step 3 to use `python manage.py load_flow_definitions`
   - Updated troubleshooting section

4. **`omari_integration/README.md`**
   - Updated "Creating a Payment Flow" section to reference flow definitions

## 🎯 Flow Features

### Trigger Methods
1. **Direct keywords**: `pay`, `payment`, `make payment`, `omari payment`
2. **Via main menu**: Type `menu` → Select "📱 Mobile Payment"

### User Journey
```
User: "pay"
↓
Bot: Asks for booking reference
↓
User: Enters booking reference (e.g., BK-SLYKER-TECH-20251023)
↓
Bot: Shows booking details + balance due, asks for amount
↓
User: Enters amount (e.g., 50)
↓
Bot: Shows payment channel buttons (Ecocash/OneMoney/ZimSwitch)
↓
User: Selects channel
↓
Bot: Asks for mobile number (2637XXXXXXXX format)
↓
User: Enters phone number
↓
Bot: Initiates payment, asks for OTP
↓
User: Enters OTP received via SMS
↓
Bot: Processes payment, updates booking, shows success message
```

### Flow Steps (18 total)

1. **start_payment** - Welcome message explaining payment options
2. **ask_booking_reference** - Collects booking reference
3. **find_booking** - Queries database for booking
4. **handle_booking_not_found** - Error handling for invalid reference
5. **display_booking_and_ask_amount** - Shows booking details, collects amount
6. **ask_payment_channel** - Interactive buttons for channel selection
7. **ask_phone_number** - Collects and validates mobile number
8. **initiate_payment** - Calls `initiate_omari_payment` action
9. **payment_initiated_success** - Asks for OTP with cancellation option
10. **process_otp** - Calls `process_otp` action
11. **payment_success** - End flow with success message
12. **payment_failed** - Error handling for OTP failure
13. **payment_initiation_failed** - Error handling for API failure
14. **cancel_payment** - Calls `cancel_payment` action
15. **payment_cancelled** - End flow with cancellation message
16. **end_payment_flow** - Generic end point

### Validation & Error Handling

- **Booking Reference**: Case-insensitive lookup
- **Amount**: Regex validation for decimal format (e.g., 50.00)
- **Phone Number**: Strict regex: `^2637[0-9]{8}$`
- **Balance Display**: Shows total, paid, and balance due
- **Retry Logic**: Max 2 retries for invalid inputs
- **Cancellation**: Keywords `cancel`, `stop`, `quit`, `abort` abort payment
- **Error Messages**: User-friendly messages with fallback to technical errors

### Custom Actions Used

1. **initiate_omari_payment** (from `omari_integration/flow_actions.py`)
   - Parameters: booking_reference, amount, currency, channel, msisdn
   - Sets: `omari_otp_reference` on success

2. **process_otp** (from `omari_integration/flow_actions.py`)
   - Parameters: otp
   - Sets: `omari_payment_success`, `omari_payment_reference` on success

3. **cancel_payment** (from `omari_integration/flow_actions.py`)
   - Cleans up payment state

## 🚀 Deployment Steps

### 1. Run Migrations
```bash
cd d:\Projects\Kali-Safaris\whatsappcrm_backend
python manage.py makemigrations omari_integration
python manage.py migrate
```

### 2. Configure Environment
Add to `.env`:
```bash
OMARI_API_BASE_URL=https://omari.v.co.zw/vsuite/omari/api/merchant/api/payment
OMARI_MERCHANT_KEY=your_merchant_key_here
```

### 3. Load Flows
```bash
python manage.py load_flow_definitions
```

This loads ALL flow definitions including the new Omari payment flow.

### 4. Test
Send WhatsApp message: `pay`

Or: `menu` → Select "📱 Mobile Payment"

## 📋 Integration Points

### With Existing Systems

1. **Flow Engine** (`flows/services.py`)
   - Already integrated via `process_payment_message()` for automatic OTP detection
   - Flow actions registered in `omari_integration/apps.py`

2. **Booking System** (`customer_data.Booking`)
   - Flow queries bookings by reference
   - Updates `amount_paid` and `payment_status` on success

3. **Transaction Tracking** (`omari_integration.OmariTransaction`)
   - Each payment creates a transaction record
   - Links to booking via FK
   - Tracks OTP reference, payment reference, status

4. **Main Menu** (`flows/definitions/main_menu_flow.py`)
   - New "📱 Mobile Payment" option in "Support & Info" section
   - Positioned between FAQs and Manual Payment

## 🔧 Pattern Compliance

The flow follows the exact pattern used in existing flows:

- **Dictionary-based definition** (not class-based)
- **Standard fields**: `name`, `friendly_name`, `description`, `trigger_keywords`, `is_active`, `steps`
- **Step structure**: `name`, `type`, `config`, `transitions`
- **Step types**: `send_message`, `question`, `action`, `switch_flow`, `end_flow`
- **Transition priorities**: Explicit priority ordering for conditions
- **Jinja2 templates**: Used for dynamic content and variable interpolation
- **Interactive messages**: WhatsApp button/list format for user input
- **Validation**: Regex patterns and fallback configurations

## 📁 File Locations

```
whatsappcrm_backend/
├── omari_integration/
│   ├── apps.py                    # Registers flow actions
│   ├── flow_actions.py            # Custom actions: initiate, process_otp, cancel
│   ├── whatsapp_handler.py        # OTP flow logic
│   ├── message_processor.py       # Automatic OTP detection
│   ├── models.py                  # OmariTransaction model
│   ├── services.py                # OmariClient API wrapper
│   ├── README.md                  # Integration docs
│   └── DEPLOYMENT.md              # Deployment guide
│
└── flows/
    ├── definitions/
    │   ├── omari_payment_flow.py  # ⭐ NEW: Flow definition
    │   ├── main_menu_flow.py      # Modified: Added payment option
    │   └── ...
    ├── management/commands/
    │   └── load_flow_definitions.py  # Modified: Added OMARI_PAYMENT_FLOW
    └── services.py                # Already integrated: process_payment_message()
```

## ✨ Key Differences from Script Approach

### Before (Script-based):
- Flow created via `flows/scripts/create_omari_payment_flow.py`
- Required manual execution: `python manage.py shell < script.py`
- Not integrated with `load_flow_definitions`
- Separate from other flow definitions

### After (Definition-based):
- Flow defined in `flows/definitions/omari_payment_flow.py`
- Loaded with all other flows: `python manage.py load_flow_definitions`
- Follows consistent pattern across codebase
- Integrated with main menu

## 🎉 Result

Users can now make Omari payments via WhatsApp in two ways:
1. Type `pay` (or `payment`, `make payment`, `omari payment`)
2. Type `menu` → Select "📱 Mobile Payment"

The flow handles the complete payment journey with proper validation, error handling, booking updates, and transaction tracking.
