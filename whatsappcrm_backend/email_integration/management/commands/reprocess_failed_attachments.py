import logging
from django.core.management.base import BaseCommand
from email_integration.models import EmailAttachment
from email_integration.tasks import process_attachment_with_gemini

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    A Django management command to find and re-queue email attachments that failed
    during the Gemini processing step.

    A "failed" attachment is identified as one where `processed` is True, but the
    `extracted_data` JSON field contains `{'status': 'failed'}`. This command
    resets the status and re-triggers the Celery task.
    """
    help = "Finds and re-queues email attachments that failed during Gemini processing."

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limits the number of failed attachments to reprocess. Default is 0 (no limit).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Lists the attachments that would be re-queued without actually doing anything.",
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE ---"))

        self.stdout.write(self.style.NOTICE("Searching for failed attachments..."))

        # A failed attachment is marked as 'processed' to prevent retries,
        # but its extracted_data contains a 'status': 'failed' key-value pair.
        failed_attachments_query = EmailAttachment.objects.filter(
            processed=True,
            extracted_data__status='failed'
        )

        if not failed_attachments_query.exists():
            self.stdout.write(self.style.SUCCESS("No failed attachments found to reprocess."))
            return

        total_found = failed_attachments_query.count()
        attachments_to_reprocess = list(failed_attachments_query[:limit]) if limit > 0 else list(failed_attachments_query)

        self.stdout.write(f"Found {total_found} failed attachments. Reprocessing up to {len(attachments_to_reprocess)} of them.")

        requeued_count = 0
        for attachment in attachments_to_reprocess:
            self.stdout.write(f"  - Preparing to re-queue attachment ID: {attachment.id} (File: {attachment.filename})")
            if not dry_run:
                # Reset the status to allow reprocessing
                attachment.processed = False
                attachment.extracted_data = None
                attachment.save(update_fields=['processed', 'extracted_data'])

                # Dispatch the Celery task again
                process_attachment_with_gemini.delay(attachment.id)
                requeued_count += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"\nDry run complete. Would have re-queued {len(attachments_to_reprocess)} attachments."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully re-queued {requeued_count} attachments for processing."))