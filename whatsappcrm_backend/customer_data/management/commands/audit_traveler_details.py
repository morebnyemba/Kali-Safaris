"""
Finds confirmed bookings (Paid / Deposit Paid) that break the rule
"confirmed => complete passenger details" — data confirmed before the rule
existed — and, with --apply, holds them as 'Paid - Awaiting Passenger Details'
so they drop off manifests until staff complete them.

    python manage.py audit_traveler_details            # report only (upcoming tours)
    python manage.py audit_traveler_details --apply    # hold the offending bookings
    python manage.py audit_traveler_details --all      # include past tour dates
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from customer_data.models import Booking


class Command(BaseCommand):
    help = "Report (and optionally hold) confirmed bookings with incomplete passenger details."

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help="Hold offending bookings as awaiting details.")
        parser.add_argument('--all', action='store_true', help="Include bookings whose tour date has passed.")

    def handle(self, *args, **options):
        bookings = Booking.objects.filter(payment_status__in=Booking.CONFIRMED_PAYMENT_STATUSES)
        if not options['all']:
            bookings = bookings.filter(start_date__gte=timezone.localdate())

        offending = 0
        for booking in bookings.order_by('start_date', 'booking_reference').iterator():
            problems = booking.traveler_details_problems()
            if not problems:
                continue
            offending += 1
            self.stdout.write(
                f"{booking.start_date}  {booking.booking_reference:<24} "
                f"{booking.get_payment_status_display():<14} {' '.join(problems)}"
            )
            if options['apply']:
                with transaction.atomic():
                    # save() applies the rule: holds the booking and alerts staff.
                    booking.save(update_fields=['updated_at'])

        verb = "Held" if options['apply'] else "Found"
        style = self.style.WARNING if offending else self.style.SUCCESS
        self.stdout.write(style(f"{verb} {offending} confirmed booking(s) with incomplete passenger details."))
        if offending and not options['apply']:
            self.stdout.write("Re-run with --apply to hold them until their details are complete.")
