# whatsappcrm_backend/customer_data/management/commands/send_id_reminders.py
"""
Management command to send ID document reminders to travelers.
Checks upcoming tours and sends WhatsApp reminders to travelers
who haven't uploaded their ID documents yet.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from customer_data.models import Booking, Traveler
from meta_integration.models import Contact
from meta_integration.utils import send_whatsapp_message
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send ID document upload reminders to travelers for upcoming tours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours-before',
            type=int,
            default=48,
            help='Send reminders X hours before tour start (default: 48)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Send reminders even if already sent today'
        )

    def handle(self, *args, **options):
        hours_before = options['hours_before']
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(f"Checking for tours starting in {hours_before} hours...")

        # Calculate the target date/time range
        now = timezone.now()
        target_start = now + timedelta(hours=hours_before - 1)  # 1 hour window
        target_end = now + timedelta(hours=hours_before + 1)

        # Find bookings with tours starting in the target window
        bookings = Booking.objects.filter(
            start_date__range=[target_start.date(), target_end.date()],
            payment_status__in=['PAID', 'DEPOSIT_PAID']  # Only confirmed bookings
        ).select_related('customer', 'tour').prefetch_related('travelers')

        self.stdout.write(f"Found {bookings.count()} confirmed bookings")

        reminders_sent = 0
        travelers_without_ids = 0

        for booking in bookings:
            # Get travelers without ID documents
            travelers = booking.travelers.filter(
                id_document__isnull=True
            ) | booking.travelers.filter(
                id_document=''
            )

            if not travelers.exists():
                continue

            travelers_without_ids += travelers.count()

            # Get customer contact
            customer = booking.customer
            if not hasattr(customer, 'phone_number') or not customer.phone_number:
                self.stdout.write(
                    self.style.WARNING(
                        f"  No phone number for customer {customer.id} (Booking {booking.booking_reference})"
                    )
                )
                continue

            # Check if we already sent a reminder today (unless force)
            if not force:
                # You could add a ReminderSent model to track this
                # For now, we'll send it
                pass

            # Format traveler list
            traveler_names = ", ".join([t.name for t in travelers[:3]])
            if travelers.count() > 3:
                traveler_names += f" and {travelers.count() - 3} more"

            # Create reminder message
            message = self._create_reminder_message(
                booking, 
                travelers.count(),
                traveler_names,
                hours_before
            )

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [DRY RUN] Would send to {customer.phone_number}:"
                    )
                )
                self.stdout.write(f"    {message[:100]}...")
            else:
                # Send the reminder
                try:
                    contact = Contact.objects.filter(
                        phone_number=customer.phone_number
                    ).first()
                    
                    if contact:
                        send_whatsapp_message(
                            contact=contact,
                            message_body=message
                        )
                        reminders_sent += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Sent reminder to {customer.name} ({booking.booking_reference})"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  No Contact found for {customer.phone_number}"
                            )
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Error sending to {customer.phone_number}: {str(e)}"
                        )
                    )
                    logger.error(f"Error sending ID reminder: {e}", exc_info=True)

        # Summary
        self.stdout.write("\n" + "="*50)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN: Would send {reminders_sent} reminder(s) for {travelers_without_ids} traveler(s)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sent {reminders_sent} reminder(s) for {travelers_without_ids} traveler(s) without ID documents"
                )
            )

    def _create_reminder_message(self, booking, traveler_count, traveler_names, hours_before):
        """Create the reminder message text."""
        
        tour_name = booking.tour.name if booking.tour else "your tour"
        tour_date = booking.start_date.strftime("%B %d, %Y") if booking.start_date else "soon"
        
        # Calculate deadline
        deadline_time = booking.start_date - timedelta(hours=24) if booking.start_date else None
        deadline_text = deadline_time.strftime("%B %d at %I:%M %p") if deadline_time else "before your tour"
        
        message = f"""⚠️ *ID Document Reminder*

Hi! Your tour is coming up soon:

🌍 *Tour:* {tour_name}
📅 *Date:* {tour_date}
📋 *Booking:* {booking.booking_reference}

📸 *Action Needed:*
We still need ID/Passport photos for:
{traveler_names}

🚨 *Deadline:* {deadline_text}

━━━━━━━━━━━━━━━━

*To upload now:*
Reply with *traveler details* to start the process.

💡 *Why we need this:*
ID documents are required by park authorities for entry.

Questions? Just reply to this message!

Kalai Safaris Team 🦁"""

        return message
