# COPYandPAY UAT Checklist (KALAI SAFARIS VIC FALLS)

This checklist is for validating COPYandPAY integration on the ZimSwitch Online test gateway before requesting live credentials.

## 1. Test Configuration Verification

- Environment variables are set in backend runtime:
  - `COPYANDPAY_BASE_URL=https://eu-test.oppwa.com`
  - `COPYANDPAY_ENTITY_ID=<test entity id>`
  - `COPYANDPAY_BEARER_TOKEN=<test auth bearer>`
  - `COPYANDPAY_TEST_MODE=EXTERNAL`
  - `COPYANDPAY_BRANDS=<required brands>`
- Backend service restarted after env update.
- Frontend points to correct backend API base URL.
- Card provider options visible in checkout:
  - `COPYandPAY (Hosted)`
  - `CBZ Direct Card` (if enabled)

Pass criteria:
- Card checkout shows `COPYandPAY (Hosted)` as an available option.

## 2. Checkout Preparation API

Endpoint:
- `POST /crm-api/payments/cbz/copyandpay/prepare/`

Test cases:
- Valid request returns:
  - `success=true`
  - non-empty `checkout_id`
  - non-empty `merchant_reference`
  - `widget_script_url` pointing to `eu-test.oppwa.com`
- Invalid payload (missing amount/currency) returns `400`.
- Missing COPYandPAY config returns `503` and clear message.

Pass criteria:
- Successful prepare call consistently returns a valid checkout session.

## 3. Hosted Widget Rendering

Page:
- `/booking/card-checkout`

Test cases:
- Redirect from booking page includes required query params (`checkoutId`, `merchantRef`, `returnUrl`).
- paymentWidgets.js loads without browser console errors.
- Checkout form renders selected brands from config.
- Cancel action returns user safely to booking page.

Pass criteria:
- Hosted card form loads and is usable in desktop and mobile viewports.

## 4. Payment Flow (COPYandPAY)

Test cases:
- Complete a payment with test card data (to be provided by gateway contact).
- Verify redirect to shopper result page with `resourcePath` parameter.
- Verify status page calls backend status endpoint and shows final result.

Pass criteria:
- User is redirected correctly and receives a clear success/pending/failure message.

## 5. Payment Status Verification API

Endpoint:
- `GET /crm-api/payments/cbz/copyandpay/status/?resourcePath=...`

Test cases:
- Approved response updates transaction to `APPROVED`.
- Pending response updates transaction to `PENDING`.
- Declined response updates transaction to `DECLINED`.
- Missing `resourcePath` returns `400`.

Pass criteria:
- API status mapping and transaction updates match gateway result codes.

## 6. Booking and Reconciliation

Test cases:
- Approved payment records a `Payment` record on linked booking.
- Temporary booking references are finalized correctly after approval.
- Merchant reference is stored and visible for support/reconciliation.

Pass criteria:
- Booking/payment records remain consistent and traceable.

## 7. Dual-Provider Card UX

Test cases:
- Both card methods coexist when enabled:
  - `COPYandPAY (Hosted)`
  - `CBZ Direct Card`
- If one provider is unavailable, fallback provider auto-selects.
- If both card providers are unavailable, user sees clear guidance.

Pass criteria:
- Provider availability behavior is correct and user-safe.

## 8. Security and Compliance Checks

- No real credentials committed to source control.
- No raw card PAN/CVV persisted by backend in COPYandPAY flow.
- HTTPS enforced in test environment.
- Logs do not leak bearer token or full card details.

Pass criteria:
- Integration behavior remains aligned with hosted-field security expectations.

## 9. Regression Checks

- EcoCash payment flow still works.
- Existing CBZ direct card flow still works (if enabled).
- WhatsApp return-link behavior still works where applicable.

Pass criteria:
- No regressions in existing payment channels.

## 10. Signoff Record

Project:
- KALAI SAFARIS VIC FALLS

UAT Run Date:
- ______________________

Executed By:
- ______________________

Summary:
- [ ] All critical tests passed
- [ ] Known issues documented
- [ ] Ready to request live gateway provisioning

Known Issues / Notes:
- _______________________________________________
- _______________________________________________
- _______________________________________________

Approver Name:
- ______________________

Approval Date:
- ______________________
