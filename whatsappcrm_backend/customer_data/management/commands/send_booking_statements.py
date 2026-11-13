"""
Email every customer with a paid booking an up-to-date receipt (one per booking,
listing all payments) — e.g. once after deploying, so customers who paid before
receipts existed get one.

    python manage.py send_booking_statements --dry-run      # who would get one, and why others won't
    python manage.py send_booking_statements                # queue them (spaced out, see --every)

Safe to run again and again: a booking gets at most one statement ever, and is
skipped if the customer was already emailed after their last payment. Only
upcoming trips (and on-hold bookings) unless --include-past.
"""
from collections import Counter

from django.core.management.base import BaseCommand

from customer_data.customer_emails import statement_candidates, statement_skip_reason


class Command(BaseCommand):
    help = "Queue one booking & payment receipt email per paid booking (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='List who would get one; send nothing.')
        parser.add_argument('--include-past', action='store_true', help='Also bookings whose trip has passed.')
        parser.add_argument('--every', type=int, default=20, help='Seconds between sends (default 20).')
        parser.add_argument('--limit', type=int, default=0, help='Queue at most this many.')

    def handle(self, *args, **opts):
        from customer_data.tasks import send_booking_statement_email_task

        skipped, queued = Counter(), 0
        for booking in statement_candidates(include_past=opts['include_past']):
            reason = statement_skip_reason(booking)
            if reason:
                skipped[reason] += 1
                continue
            if opts['limit'] and queued >= opts['limit']:
                skipped['over --limit'] += 1
                continue
            if opts['dry_run']:
                self.stdout.write(f"  would send: {booking.booking_reference} · {booking.tour_name} · {booking.start_date}")
            else:
                send_booking_statement_email_task.apply_async(args=[booking.pk], countdown=queued * max(opts['every'], 0))
            queued += 1
        verb = 'Would queue' if opts['dry_run'] else 'Queued'
        self.stdout.write(self.style.SUCCESS(f"{verb} {queued} statement(s)."))
        for reason, count in skipped.most_common():
            self.stdout.write(f"  skipped {count}: {reason}")
