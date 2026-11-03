"""
Departure-slot rules shared by every booking channel (website checkout and the
WhatsApp bot), so "which times can I still book?" has exactly one answer.
Times are Victoria Falls local time (settings.TIME_ZONE = Africa/Harare).
"""
from datetime import date, datetime, time
from typing import Optional

from django.utils import timezone

from .models import Tour, TourTimeSlot


def open_slots(tour: Tour, on_date: date, now: Optional[datetime] = None) -> list[TourTimeSlot]:
    """Active slots for `on_date` that haven't departed yet. Empty for past dates."""
    now = now or timezone.localtime()
    if on_date < now.date():
        return []
    slots = tour.active_time_slots()
    if on_date > now.date():
        return slots
    return [s for s in slots if timezone.make_aware(datetime.combine(on_date, s.start_time), now.tzinfo) > now]


def parse_time(raw) -> Optional[time]:
    """'8:00' / '08:00' / '08:00:00' -> time, else None."""
    if isinstance(raw, time):
        return raw
    text = str(raw or '').strip()
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def serialize_slot(slot: TourTimeSlot) -> dict:
    return {
        'id': slot.id,
        'start': slot.start_time.strftime('%H:%M'),
        'end': slot.end_time.strftime('%H:%M') if slot.end_time else None,
        'label': slot.label,
        'display': slot.display,
    }
