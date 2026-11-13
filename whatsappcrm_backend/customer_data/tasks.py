# whatsappcrm_backend/customer_data/tasks.py
from celery import shared_task

from .draft_cleanup import DEFAULT_MAX_AGE_HOURS, cancel_stale_website_drafts


@shared_task(name='customer_data.cancel_stale_website_drafts')
def cancel_stale_website_drafts_task(max_age_hours: int = DEFAULT_MAX_AGE_HOURS) -> int:
    """Nightly: cancel unpaid website checkout drafts (see draft_cleanup)."""
    return len(cancel_stale_website_drafts(max_age_hours=max_age_hours))


@shared_task(name='customer_data.send_booking_confirmation_email', bind=True, max_retries=6,
             autoretry_for=(Exception,), retry_backoff=60, retry_backoff_max=3600, retry_jitter=True)
def send_booking_confirmation_email_task(self, booking_id: int) -> bool:
    """Email the customer their confirmed booking (retries with backoff while mail is unreachable)."""
    from .booking_emails import send_booking_confirmation
    return send_booking_confirmation(booking_id)


@shared_task(name='customer_data.send_balance_reminders')
def send_balance_reminders_task() -> dict:
    """Daily: move unpaid bookings past their grace period to hold, then send balance notices (see balance_reminders)."""
    from .balance_reminders import run_daily
    return run_daily()


_EMAIL_RETRY = dict(bind=True, max_retries=6, autoretry_for=(Exception,), retry_backoff=60,
                    retry_backoff_max=3600, retry_jitter=True)


@shared_task(name='customer_data.send_payment_receipt_email', **_EMAIL_RETRY)
def send_payment_receipt_email_task(self, payment_id) -> bool:
    from .customer_emails import send_payment_receipt
    return bool(send_payment_receipt(payment_id))


@shared_task(name='customer_data.send_booking_rescheduled_email', **_EMAIL_RETRY)
def send_booking_rescheduled_email_task(self, booking_id, held_from_date=None) -> bool:
    from datetime import date
    from .customer_emails import send_booking_rescheduled
    held = date.fromisoformat(held_from_date) if held_from_date else None
    return bool(send_booking_rescheduled(booking_id, held))


@shared_task(name='customer_data.send_payment_rejected_email', **_EMAIL_RETRY)
def send_payment_rejected_email_task(self, payment_id, reason='') -> bool:
    from .customer_emails import send_payment_rejected
    return bool(send_payment_rejected(payment_id, reason))


@shared_task(name='customer_data.send_booking_statement_email', **_EMAIL_RETRY)
def send_booking_statement_email_task(self, booking_id) -> bool:
    from .customer_emails import send_booking_statement
    return bool(send_booking_statement(booking_id))
