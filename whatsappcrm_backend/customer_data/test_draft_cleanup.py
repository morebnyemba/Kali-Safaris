import datetime
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from cbz_integration.models import CBZTransaction
from customer_data.draft_cleanup import WEBSITE_DRAFT_NOTE_PREFIX, cancel_stale_website_drafts
from customer_data.models import Booking
from omari_integration.models import OmariTransaction


class StaleWebsiteDraftTests(TestCase):
    def make(self, ref, hours_old, notes=f"{WEBSITE_DRAFT_NOTE_PREFIX}. People: 1.", **kw):
        day = timezone.localdate() + datetime.timedelta(days=10)
        b = Booking.objects.create(booking_reference=ref, tour_name='Sunset Cruise', start_date=day, end_date=day,
                                   number_of_adults=1, total_amount=Decimal('50'), notes=notes, **kw)
        Booking.objects.filter(pk=b.pk).update(created_at=timezone.now() - datetime.timedelta(hours=hours_old))
        return b

    def age_txns(self, model, booking, hours):
        model.objects.filter(booking=booking).update(updated_at=timezone.now() - datetime.timedelta(hours=hours))

    def test_cancels_only_stale_unpaid_website_drafts(self):
        stale = self.make('PENDING-WEB-OLD', 72)
        young = self.make('PENDING-WEB-NEW', 5)
        whatsapp = self.make('KS-WA-1', 72, notes='Created from WhatsApp booking flow')
        paid = self.make('KS-PAID', 72, payment_status=Booking.PaymentStatus.CANCELLED)

        refs = cancel_stale_website_drafts()

        self.assertEqual(refs, ['PENDING-WEB-OLD'])
        stale.refresh_from_db()
        self.assertEqual(stale.payment_status, Booking.PaymentStatus.CANCELLED)
        self.assertIn('Auto-cancelled', stale.notes)
        for b in (young, whatsapp):
            b.refresh_from_db()
            self.assertEqual(b.payment_status, Booking.PaymentStatus.PENDING)
        paid.refresh_from_db()
        self.assertNotIn('Auto-cancelled', paid.notes)

    def test_keeps_drafts_with_recent_or_successful_gateway_activity(self):
        in_flight = self.make('PENDING-WEB-INFLIGHT', 72)
        CBZTransaction.objects.create(merchant_reference='KS-A', payment_type='ECOCASH', amount=50, currency='USD',
                                      command='Debit', status='PENDING', booking=in_flight)
        approved = self.make('PENDING-WEB-APPROVED', 72)
        CBZTransaction.objects.create(merchant_reference='KS-B', payment_type='CARD', amount=50, currency='USD',
                                      command='Debit', status='APPROVED', booking=approved)
        self.age_txns(CBZTransaction, approved, 100)
        omari_ok = self.make('PENDING-WEB-OMARI', 72)
        OmariTransaction.objects.create(reference='OM-1', msisdn='263771234567', amount=50, status='SUCCESS', booking=omari_ok)
        self.age_txns(OmariTransaction, omari_ok, 100)
        dead = self.make('PENDING-WEB-DEAD', 72)
        CBZTransaction.objects.create(merchant_reference='KS-C', payment_type='ECOCASH', amount=50, currency='USD',
                                      command='Debit', status='PENDING', booking=dead)
        self.age_txns(CBZTransaction, dead, 60)

        self.assertEqual(cancel_stale_website_drafts(), ['PENDING-WEB-DEAD'])

    def test_dry_run_command_changes_nothing(self):
        stale = self.make('PENDING-WEB-OLD', 72)
        out = StringIO()
        call_command('cancel_stale_drafts', '--dry-run', stdout=out)
        self.assertIn('Would cancel 1', out.getvalue())
        stale.refresh_from_db()
        self.assertEqual(stale.payment_status, Booking.PaymentStatus.PENDING)
