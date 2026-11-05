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
def send_balance_reminders_task() -> list:
    """Daily: remind customers with a balance outstanding (see balance_reminders)."""
    from .balance_reminders import send_balance_reminders
    return send_balance_reminders()
