from django.core.management.base import BaseCommand
from django.db.models import Count
from meta_integration.models import WebhookEventLog

class Command(BaseCommand):
    help = 'Finds and deletes duplicate WebhookEventLog entries based on event_identifier, keeping the newest one.'

    def handle(self, *args, **options):
        # Find identifiers that are duplicated
        duplicates = (
            WebhookEventLog.objects.values('event_identifier')
            .annotate(identifier_count=Count('id'))
            .filter(identifier_count__gt=1)
        )

        duplicate_count = duplicates.count()
        self.stdout.write(self.style.SUCCESS(f"Found {duplicate_count} event_identifiers with duplicate entries."))

        if duplicate_count == 0:
            self.stdout.write("No duplicates to clean up.")
            return

        # For each duplicated identifier, find and delete all but the most recent entry
        for item in duplicates:
            identifier = item['event_identifier']
            if not identifier:
                continue

            # Get all log entries for this identifier, ordered from newest to oldest
            entries = WebhookEventLog.objects.filter(event_identifier=identifier).order_by('-received_at')

            # The first one in the list is the newest one, which we want to keep
            entries_to_delete = entries[1:]
            
            self.stdout.write(f"Identifier '{identifier}': Keeping 1 entry, deleting {len(entries_to_delete)}.")

            # Perform the deletion
            for entry in entries_to_delete:
                entry.delete()

        self.stdout.write(self.style.SUCCESS("Cleanup complete."))
