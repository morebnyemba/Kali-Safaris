# Manual Payment Approval - User Guide

## Overview

When customers record manual payments via WhatsApp, the finance team needs to verify and approve them. This guide explains how the approval process works and what happens automatically when payments are approved or rejected.

---

## The Complete Flow

### 1. Customer Records Payment (WhatsApp)

**Customer Actions:**
1. Types "manual payment" in WhatsApp
2. Enters booking reference
3. System shows booking details and balance
4. Enters payment amount
5. Selects payment method (Bank Transfer/Omari)
6. Uploads proof of payment screenshot
7. Receives confirmation: "Our finance team will verify it and update your booking status shortly."

**System Actions:**
- Creates Payment record with `status='pending'`
- Sends notification to Finance Team and System Admins
- Stores proof of payment reference (if uploaded)

### 2. Finance Team Reviews (Admin)

**Navigate to Admin:**
```
Admin → Customer Data → Payments
```

**Filter to Pending:**
- Click "Status" filter → Select "Pending"
- See all payments awaiting approval

**Review Details:**
- Booking reference
- Amount
- Payment method
- Notes (includes who submitted)
- Created date

### 3. Approve or Reject

**Select Payment(s):**
- Check boxes next to one or more pending payments
- Can approve/reject in bulk

**Choose Action:**
- From "Action" dropdown, select:
  - **"Approve selected payments"** - If payment is valid
  - **"Reject selected payments"** - If payment cannot be verified

**Click "Go"**

---

## What Happens on Approval

### Automatic Actions

#### 1. Payment Status Updated
```
PENDING → SUCCESSFUL
```
- Note added: "[Approved by {username} on {date}]"
- Timestamp recorded

#### 2. Booking Reference Updated
**IF** booking has tour + start_date:
```
BK12345678 → BK-T005-20260210
```
**Shared format:** `BK-T{tour_id}-{YYYYMMDD}`

This groups all travelers on the same tour/date under one reference (same as Omari payments).

#### 3. Booking Payment Status Updated
```python
if amount_paid >= total_amount:
    status = PAID  # Fully paid
elif amount_paid > 0:
    status = DEPOSIT_PAID  # Partially paid
```

#### 4. WhatsApp Notification Sent

**Example Message (Partial Payment):**
```
✅ *Payment Approved!*

Your payment of $500.00 for booking *BK-T005-20260210* has been approved.

Tour: Victoria Falls Safari
Date: February 10, 2026
Amount Paid: $500.00
Total: $1000.00

Balance Due: $500.00

📋 *Next Step:* Please provide traveler details for all passengers.
Reply with *traveler details* to get started.
```

**Example Message (Full Payment):**
```
✅ *Payment Approved!*

Your payment of $1000.00 for booking *BK-T005-20260210* has been approved.

Tour: Victoria Falls Safari
Date: February 10, 2026
Amount Paid: $1000.00
Total: $1000.00

✅ Your booking is now fully paid!

📋 *Next Step:* Please provide traveler details for all passengers.
Reply with *traveler details* to get started.
```

#### 5. Triggers Traveler Details Collection

**IF** no travelers recorded yet:
- Message includes prompt: "Reply with *traveler details*"
- Customer can start traveler details flow immediately
- Flow collects: name, age, nationality, gender, ID number, medical needs
- **Flow requests ID document upload via PhotoPicker**

---

## What Happens on Rejection

### Automatic Actions

#### 1. Payment Status Updated
```
PENDING → FAILED
```
- Note added: "[Rejected by {username} on {date}]"
- Timestamp recorded

#### 2. WhatsApp Notification Sent

**Example Message:**
```
❌ *Payment Not Approved*

Unfortunately, we couldn't verify your payment of $500.00 for booking *BK-T005-20260210*.

Please contact our finance team or try submitting the payment again with a clear proof of payment.

You can record a new payment by typing *manual payment*.
```

#### 3. Customer Can Resubmit
- Customer types "manual payment"
- Goes through flow again
- Can upload new/clearer proof of payment

---

## Admin Workflow Examples

### Example 1: Approving Single Payment

**Scenario:**
- Customer John submits $500 payment for booking BK12345678
- Uploads bank transfer screenshot

**Steps:**
1. Go to Admin → Payments
2. Filter: Status = Pending
3. Click on payment to review
4. Verify:
   - Amount matches bank transfer
   - Booking exists and is valid
   - Proof of payment is clear
5. Go back to list
6. Select payment checkbox
7. Action: "Approve selected payments"
8. Click "Go"

**Result:**
- Payment approved
- Booking reference updated to BK-T005-20260210 (if tour exists)
- Booking status updated to DEPOSIT_PAID
- John receives WhatsApp confirmation
- John prompted to provide traveler details

### Example 2: Bulk Approval

**Scenario:**
- 5 payments pending from different customers
- All verified via bank statements

**Steps:**
1. Go to Admin → Payments
2. Filter: Status = Pending
3. Review all 5 payments
4. Select all 5 checkboxes
5. Action: "Approve selected payments"
6. Click "Go"

**Result:**
- All 5 payments approved
- Each booking reference updated (if applicable)
- Each booking status updated
- All 5 customers receive WhatsApp notifications
- Admin sees: "Successfully approved 5 payment(s)."

### Example 3: Rejecting Invalid Payment

**Scenario:**
- Customer uploads unclear proof of payment
- Cannot verify bank transfer

**Steps:**
1. Go to Admin → Payments
2. Filter: Status = Pending
3. Click on payment to review
4. Determine proof is insufficient
5. Go back to list
6. Select payment checkbox
7. Action: "Reject selected payments"
8. Click "Go"

**Result:**
- Payment rejected
- Customer receives rejection message
- Customer instructed to resubmit with clearer proof
- Can reach out to customer via phone if needed

---

## Admin Messages

### Success Messages

**Approval:**
```
Successfully approved 1 payment(s).
```

**With Reference Update:**
```
Updated booking reference: BK12345678 → BK-T005-20260210
Successfully approved 1 payment(s).
```

**Rejection:**
```
Successfully rejected 1 payment(s).
```

### Warning Messages

**Notification Failed:**
```
Payment approved but failed to send WhatsApp notification: [error details]
```
- Payment is still approved
- Manually contact customer

### Error Messages

**Approval Failed:**
```
Error approving payment {id}: [error details]
```
- Payment not approved
- Transaction rolled back
- Check error details
- Try again or contact support

---

## Consistency with Omari Payments

Manual payment approval now works **exactly like Omari payments**:

| Feature | Omari Payments | Manual Approval |
|---------|----------------|-----------------|
| Booking reference update | ✅ | ✅ |
| Status update (PAID/DEPOSIT_PAID) | ✅ | ✅ |
| WhatsApp notification | ✅ | ✅ |
| Traveler details prompt | ✅ | ✅ |
| Atomic transactions | ✅ | ✅ |
| Audit trail | ✅ | ✅ |

**Benefits:**
- Consistent customer experience
- Same booking reference format
- Same data flow
- Same reports work for both

---

## Integration with Other Features

### 1. Booking Reference Grouping

After approval, bookings with same tour/date share a reference:

**Before Approval:**
```
Booking 1: BK12345678 (Jane)
Booking 2: BK87654321 (John)
Both for Tour ID 5, Date 2026-02-10
```

**After Approval:**
```
Booking 1: BK-T005-20260210 (Jane)
Booking 2: BK-T005-20260210 (John)
Grouped together!
```

### 2. Traveler Details Flow

After approval message, customer can immediately:
1. Reply with "traveler details"
2. Fill in traveler information
3. **Upload ID documents via PhotoPicker**
4. Submit for each traveler

### 3. Passenger Manifests

Once travelers recorded, they appear in manifests:

**Summary Report:**
```
BK-T005-20260210: Jane(2), John(3) total: 5
ID Documents Uploaded: 4 of 5
```

**Full Manifest:**
```
| Name       | ID Number | Nationality | Age | ID Doc |
|------------|-----------|-------------|-----|--------|
| Jane Doe   | 12345678  | Zimbabwean  | 35  |   ✓    |
| John Doe   | 87654321  | Zimbabwean  | 32  |   ✓    |
```

---

## Troubleshooting

### Problem: Payment approved but customer didn't receive message

**Cause:** WhatsApp notification failed

**Solution:**
1. Check admin messages for warning
2. Manually send message via WhatsApp
3. Or call customer to confirm

### Problem: Booking reference didn't update

**Cause:** Booking doesn't have tour_id or start_date

**Solution:**
- This is expected for custom bookings
- Reference remains as-is
- No issue with functionality

### Problem: Customer can't find booking reference

**Cause:** Typing error or wrong reference

**Solution:**
1. Ask customer for booking details
2. Find booking in admin by customer name/phone
3. Share correct reference via WhatsApp

### Problem: Multiple payments for same booking

**Cause:** Legitimate (split payments) or error (duplicate)

**Solution:**
- Review all payments for that booking
- Approve legitimate ones
- Reject duplicates
- System handles multiple approved payments correctly

---

## Best Practices

### Review Process

**DO:**
- ✅ Verify amount matches bank records
- ✅ Check proof of payment is clear
- ✅ Confirm booking exists
- ✅ Process promptly (within 24 hours)
- ✅ Use bulk approval when possible

**DON'T:**
- ❌ Approve without verifying proof
- ❌ Leave payments pending too long
- ❌ Forget to check bank statements
- ❌ Ignore customer follow-ups

### Communication

**Proactive:**
- Approve quickly
- System sends automatic confirmation
- Follow up if issues arise

**Reactive:**
- Respond to customer queries
- Explain rejections if customer asks
- Guide through resubmission if needed

### Audit Trail

**Track:**
- Who approved/rejected each payment
- When action was taken
- All notes in payment record
- WhatsApp message history

---

## FAQ

**Q: Can I approve multiple payments at once?**
A: Yes! Select multiple checkboxes and use "Approve selected payments" action.

**Q: What if I approve by mistake?**
A: You can manually change the payment status back to PENDING or FAILED in the payment detail page. However, the booking updates and WhatsApp notification cannot be automatically reversed.

**Q: Do customers need to provide traveler details immediately?**
A: No, they can do it anytime. The prompt is a reminder, but they can come back to it later by typing "traveler details".

**Q: What happens if a customer pays via Omari after recording a manual payment?**
A: Both payments are recorded separately. The system handles multiple payments for the same booking and tracks the total `amount_paid`.

**Q: Can I add notes before approving?**
A: Yes! Click on the payment to open its detail page, add notes, save, then go back and approve.

**Q: What if the booking reference changes after approval?**
A: The customer receives the updated reference in the confirmation message. All future references will use the new format.

**Q: How do I see all approved payments?**
A: Filter by Status = "Successful" in the Payments admin list.

**Q: Can I undo an approval?**
A: You can change the status manually, but it won't reverse the booking updates or unsend the WhatsApp message. Contact customer if needed.

---

## Related Documentation

- **Manual Payment Flow:** `flows/definitions/manual_payment_flow.py`
- **Traveler Details Flow:** `flows/definitions/traveler_details_whatsapp_flow.py`
- **ID Document Capture:** `flows/ID_DOCUMENT_CAPTURE.md`
- **Passenger Manifests:** `customer_data/PASSENGER_MANIFEST_GUIDE.md`
- **Booking Reference Updates:** Previous commits on Omari integration

---

## Summary

✅ **Finance team** - Easy one-click approval from admin  
✅ **Customers** - Instant confirmation via WhatsApp  
✅ **Consistency** - Same process as Omari payments  
✅ **Automation** - Reference updates and status changes  
✅ **Guidance** - Automatic prompt for traveler details  
✅ **Complete** - From payment to ID documents

The manual payment approval process is now fully integrated with all other booking features, providing a seamless experience from payment submission to tour departure.

---

**Document Version:** 1.0  
**Last Updated:** February 2026  
**Maintained By:** Slyker Tech Web Services
