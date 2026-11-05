"""
Payment-plan policy: one place for the deposit / instalment rules.

- Trips more than INSTALMENT_MIN_DAYS_AHEAD days away may be booked with a
  DEPOSIT_PERCENT deposit; the rest is paid in instalments (each at least
  manage_links.MIN_INSTALMENT) through the customer's secure link.
- The balance is due BALANCE_DUE_DAYS_BEFORE days before the trip.
- A booking's first payment is never less than the deposit, and a website
  booking that chose "pay in full" must be paid in full — so a tampered or
  retried checkout can't confirm a booking for $1.

The website mirrors the three constants in src/lib/paymentPlan.ts (a test keeps them equal).
"""
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

INSTALMENT_MIN_DAYS_AHEAD = 30
DEPOSIT_PERCENT = 50
BALANCE_DUE_DAYS_BEFORE = 14

PLAN_FULL = 'full'
PLAN_DEPOSIT = 'deposit'
CENT = Decimal('0.01')


def days_ahead(start_date: date, today: date | None = None) -> int:
    return (start_date - (today or timezone.localdate())).days


def instalments_allowed(start_date: date, today: date | None = None) -> bool:
    return start_date is not None and days_ahead(start_date, today) > INSTALMENT_MIN_DAYS_AHEAD


def deposit_amount(total) -> Decimal:
    return (Decimal(total) * DEPOSIT_PERCENT / 100).quantize(CENT, rounding=ROUND_HALF_UP)


def balance_due_date(booking) -> date | None:
    return booking.start_date - timedelta(days=BALANCE_DUE_DAYS_BEFORE) if booking.start_date else None


def chosen_plan(booking) -> str:
    payload = booking.booking_details_payload if isinstance(booking.booking_details_payload, dict) else {}
    return payload.get('payment_plan') or ''


def minimum_charge(booking) -> Decimal:
    """Smallest payment accepted now for this booking."""
    from .manage_links import balance_due, minimum_payment

    due = balance_due(booking)
    if (booking.amount_paid or 0) > 0:
        return minimum_payment(booking)
    if chosen_plan(booking) == PLAN_FULL:
        return due
    return min(deposit_amount(booking.total_amount or 0), due)
