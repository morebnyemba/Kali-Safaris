from django.core.management.base import BaseCommand

from customer_data.draft_cleanup import DEFAULT_MAX_AGE_HOURS, cancel_stale_website_drafts


class Command(BaseCommand):
    help = "Cancel unpaid website checkout draft bookings older than --hours (default 48)."

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=DEFAULT_MAX_AGE_HOURS)
        parser.add_argument('--dry-run', action='store_true', help="List what would be cancelled without changing anything.")

    def handle(self, *args, hours, dry_run, **options):
        refs = cancel_stale_website_drafts(max_age_hours=hours, dry_run=dry_run)
        verb = 'Would cancel' if dry_run else 'Cancelled'
        self.stdout.write(self.style.SUCCESS(f"{verb} {len(refs)} draft booking(s)."))
        for ref in refs:
            self.stdout.write(f"  {ref}")
