"""
Departure-slot rules shared by every booking channel (website checkout and the
WhatsApp bot), so "which times can I still book?" has exactly one answer.
Times are Victoria Falls local time (settings.TIME_ZONE = Africa/Harare).
"""
from datetime import date, datetime, time, timedelta
from typing import Optional

from django.db.models import F, Q, Sum
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


# An unpaid booking holds its seats this long after it's created — long enough
# to finish a website or WhatsApp checkout, short enough that abandoned ones
# don't block a departure. Paid bookings hold their seats for good.
SEAT_HOLD = timedelta(minutes=30)


def seats_taken(tour: Tour, on_date: date, start_time: time, exclude_booking_id=None, now=None) -> int:
    """Passengers (adults + children) holding seats on one departure."""
    from customer_data.models import Booking  # customer_data imports this app's models

    now = now or timezone.now()
    S = Booking.PaymentStatus
    holding = Q(payment_status__in=[S.PAID, S.DEPOSIT_PAID, S.AWAITING_DETAILS, S.PENDING_MANUAL]) | Q(
        payment_status=S.PENDING, created_at__gte=now - SEAT_HOLD,
    )
    qs = Booking.objects.filter(holding, tour=tour, start_date=on_date, start_time=start_time)
    if exclude_booking_id:
        qs = qs.exclude(pk=exclude_booking_id)
    return qs.aggregate(n=Sum(F('number_of_adults') + F('number_of_children')))['n'] or 0


def seats_left(slot: TourTimeSlot, on_date: date, exclude_booking_id=None, now=None) -> Optional[int]:
    """Seats still free on `on_date`, or None when the slot has no limit."""
    if slot.capacity is None:
        return None
    taken = seats_taken(slot.tour, on_date, slot.start_time, exclude_booking_id, now)
    return max(slot.capacity - taken, 0)


def has_room(slot: TourTimeSlot, on_date: date, party: int, exclude_booking_id=None) -> bool:
    left = seats_left(slot, on_date, exclude_booking_id)
    return left is None or left >= party


def full_message(slot: TourTimeSlot, on_date: date, party: int, left: Optional[int]) -> str:
    when = f"{slot.time_range} departure on {on_date.strftime('%d %b')}"
    if not left:
        return f"The {when} is fully booked — please choose another time or date."
    return (f"Only {left} seat{'s' if left != 1 else ''} left on the {when} "
            f"(you asked for {party}) — please choose another time or date.")


def availability(tour: Tour, on_date: date, now: Optional[datetime] = None) -> list[dict]:
    """Every active slot for a date with whether it has departed and the seats left."""
    now = now or timezone.localtime()
    open_ids = {s.id for s in open_slots(tour, on_date, now)}
    return [
        {**serialize_slot(s), 'departed': s.id not in open_ids, 'seats_left': seats_left(s, on_date)}
        for s in tour.active_time_slots()
    ]


def serialize_slot(slot: TourTimeSlot) -> dict:
    return {
        'id': slot.id,
        'start': slot.start_time.strftime('%H:%M'),
        'end': slot.end_time.strftime('%H:%M') if slot.end_time else None,
        'label': slot.label,
        'display': slot.display,
        'capacity': slot.capacity,
    }
