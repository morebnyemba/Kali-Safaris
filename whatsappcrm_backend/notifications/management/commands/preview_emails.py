"""
Render every customer email with sample data, without sending or touching the database:

    python manage.py preview_emails --out /tmp/email-previews

Writes <template>[-<variant>].html and .txt plus an index.html linking them all.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from notifications.emailing import brand


def _samples():
    from customer_data.models import Booking, Payment, Traveler

    today = timezone.localdate()
    start = today + timedelta(days=45)
    booking = Booking(
        booking_reference='BK-T003-20261220-1600', tour_name='Sunset Cruise', start_date=start, end_date=start,
        start_time=time(16, 0), end_time=time(18, 0), number_of_adults=2, number_of_children=1,
        total_amount=Decimal('180.00'), amount_paid=Decimal('90.00'),
    )
    travelers = [Traveler(name='Ann Moyo', age=34), Traveler(name='Tom Moyo', age=36), Traveler(name='Rudo Moyo', age=8)]
    payment = Payment(amount=Decimal('40.00'), currency='USD', payment_method='cbz_ecocash', status='successful',
                      transaction_reference='KS-8F2C91A04B7D')
    payment.created_at = timezone.make_aware(datetime.combine(today, time(10, 24)))
    due_by = start - timedelta(days=10)
    base = {
        'booking': booking, 'first_name': 'Ann', 'departure': booking.departure_display, 'travelers': travelers,
        'balance': booking.total_amount - booking.amount_paid, 'due_by': due_by, 'balance_due_by': due_by,
        'manage_url': 'https://kalaisafaris.com/manage/<private-token>', 'missing_ids': ['Tom Moyo'],
    }
    paid_after = {**base, 'balance': Decimal('50.00')}
    reminder = {**base, 'due_days_before': 10, 'min_days_ahead': 30, 'move_on': today + timedelta(days=2),
                'held_from_date': start, 'kind_is_moved': False}
    return [
        ('booking_confirmation', '', 'Booking confirmed: Sunset Cruise on 20 Dec 2026 — BK-T003-20261220-1600', base),
        ('payment_receipt', '', 'Payment received: $40.00 for Sunset Cruise', {**paid_after, 'payment': payment}),
        ('payment_receipt', 'paid-in-full', 'Payment received: $90.00 — fully paid', {**base, 'balance': 0, 'missing_ids': [], 'payment': payment}),
        ('balance_reminder', 'upcoming', 'Balance of $90.00 due soon', {**reminder, 'kind': 'upcoming'}),
        ('balance_reminder', 'final', 'Action needed: pay $90.00 to keep your cruise', {**reminder, 'kind': 'final'}),
        ('balance_reminder', 'moved', 'Your cruise is on hold — choose a new date', {**reminder, 'kind': 'moved', 'kind_is_moved': True}),
        ('booking_rescheduled', '', 'New date confirmed: Sunset Cruise', {**base, 'held_from_date': today + timedelta(days=8)}),
        ('payment_rejected', '', "We couldn't verify your payment", {**base, 'payment': Payment(amount=Decimal('90.00'), payment_method='bank_transfer'), 'reason': 'The amount has not reached our account yet.'}),
        ('booking_statement', '', 'Your booking & payment receipt — Sunset Cruise', {**base, 'payments': [payment, payment]}),
        ('staff_alert', 'payment', '[Kalai] Payment received USD 40.00 · BK-T003-20261220-1600', {
            'headline': 'USD 40.00 received', 'intro': 'EcoCash (CBZ) payment for Sunset Cruise on 20 Dec 2026.', 'tone': 'success',
            'sections': [('Payment', [('Amount', 'USD 40.00'), ('Method', 'CBZ - EcoCash'), ('Payment reference', 'KS-8F2C91A04B7D')]),
                         ('Gateway transaction (CBZ / iVeri)', [('Bank reference', 'BR-445566'), ('Authorisation code', 'AUTH42'), ('EcoCash number', '263771234567')]),
                         ('Booking', [('Booking reference', 'BK-T003-20261220-1600'), ('Customer', 'Ann Moyo'), ('Balance', 'USD 50.00')])],
            'raw': '{\n  "BankReference": "BR-445566",\n  "ResultCode": "0"\n}', 'link': 'https://dashboard.kalaisafaris.com/payments?q=KS-8F2C91A04B7D'}),
        ('document_received', '', 'Re: Booking for 3 guests', {'filenames': ['Kalai booking.pdf', 'passports.jpg'], 'original_subject': 'Booking for 3 guests'}),
        ('document_duplicate', '', 'Re: Booking for 3 guests', {'filename': 'Kalai booking.pdf', 'booking_reference': 'BK-T003-20261220-1600'}),
    ]


class Command(BaseCommand):
    help = "Render every customer email with sample data (no sending, no database writes)."

    def add_arguments(self, parser):
        parser.add_argument('--out', default='email-previews', help='Output directory')

    def handle(self, *args, **options):
        out = Path(options['out'])
        out.mkdir(parents=True, exist_ok=True)
        links = []
        for template, variant, subject, context in _samples():
            name = f"{template}{'-' + variant if variant else ''}"
            ctx = {**context, 'brand': brand(), 'subject': subject, 'preheader': ''}
            (out / f'{name}.html').write_text(render_to_string(f'emails/{template}.html', ctx))
            (out / f'{name}.txt').write_text(render_to_string(f'emails/{template}.txt', ctx))
            links.append(f'<li><a href="{name}.html">{name}</a> · <a href="{name}.txt">text</a> — {subject}</li>')
        (out / 'index.html').write_text(
            '<!doctype html><meta charset="utf-8"><title>Email previews</title>'
            '<body style="font-family:Arial;padding:24px"><h1>Kalai Safaris emails</h1><ul>' + ''.join(links) + '</ul>')
        self.stdout.write(self.style.SUCCESS(f"Wrote {len(links)} previews to {out.resolve()}"))
