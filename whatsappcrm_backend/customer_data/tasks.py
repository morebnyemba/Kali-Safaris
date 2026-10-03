# whatsappcrm_backend/customer_data/tasks.py
from celery import shared_task

from .draft_cleanup import DEFAULT_MAX_AGE_HOURS, cancel_stale_website_drafts


@shared_task(name='customer_data.cancel_stale_website_drafts')
def cancel_stale_website_drafts_task(max_age_hours: int = DEFAULT_MAX_AGE_HOURS) -> int:
    """Nightly: cancel unpaid website checkout drafts (see draft_cleanup)."""
    return len(cancel_stale_website_drafts(max_age_hours=max_age_hours))
