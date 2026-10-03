"""Regression tests for the dashboard-facing API fixes.

Run with: python manage.py test whatsappcrm_backend.tests_dashboard_api
"""
import datetime
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.test import APITestCase

from conversations.models import Contact, Message
from customer_data.models import Booking, CustomerProfile, TourInquiry
from customer_data.serializers import MyTokenObtainPairSerializer
from flows.models import Flow, FlowStep

User = get_user_model()
# Generated per run so no credential-looking literals live in the repo.
PASSWORD = secrets.token_urlsafe(16)


class AdminUserApiTests(APITestCase):
    def setUp(self):
        self.root = User.objects.create_superuser('root', 'root@example.com', PASSWORD)
        self.group_admin = User.objects.create_user('ops', 'ops@example.com', PASSWORD, is_staff=True)
        self.group_admin.groups.add(Group.objects.create(name='admin'))

    def test_group_admin_cannot_promote_self_to_superuser(self):
        self.client.force_authenticate(self.group_admin)
        res = self.client.patch(f'/crm-api/admin/users/{self.group_admin.pk}/', {'is_superuser': True}, format='json')
        self.assertEqual(res.status_code, 400)
        self.group_admin.refresh_from_db()
        self.assertFalse(self.group_admin.is_superuser)

    def test_group_admin_cannot_edit_or_deactivate_superuser(self):
        self.client.force_authenticate(self.group_admin)
        self.assertEqual(self.client.patch(f'/crm-api/admin/users/{self.root.pk}/', {'first_name': 'x'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(f'/crm-api/admin/users/{self.root.pk}/deactivate/').status_code, 403)

    def test_cannot_deactivate_own_account(self):
        self.client.force_authenticate(self.root)
        self.assertEqual(self.client.post(f'/crm-api/admin/users/{self.root.pk}/deactivate/').status_code, 400)
        self.assertEqual(self.client.patch(f'/crm-api/admin/users/{self.root.pk}/', {'is_active': False}, format='json').status_code, 400)
        self.root.refresh_from_db()
        self.assertTrue(self.root.is_active)

    def test_weak_password_rejected_and_strong_password_accepted(self):
        self.client.force_authenticate(self.root)
        weak = self.client.post('/crm-api/admin/users/', {'username': 'agent1', 'password': '1234'}, format='json')
        self.assertEqual(weak.status_code, 400)
        self.assertIn('password', weak.data)
        ok = self.client.post('/crm-api/admin/users/', {'username': 'agent1', 'password': PASSWORD}, format='json')
        self.assertEqual(ok.status_code, 201)
        self.assertTrue(User.objects.get(username='agent1').check_password(PASSWORD))


class FlowStepsApiTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(User.objects.create_superuser('root', 'root@example.com', PASSWORD))
        self.flow = Flow.objects.create(name='long_flow')
        for i in range(25):
            FlowStep.objects.create(flow=self.flow, name=f's{i}', step_type='action', config={'actions_to_run': []})

    def test_nested_steps_are_not_paginated(self):
        res = self.client.get(f'/crm-api/flows/flows/{self.flow.pk}/steps/')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)
        self.assertEqual(len(res.data), 25)

    def test_invalid_step_config_returns_400_not_500(self):
        res = self.client.post(f'/crm-api/flows/flows/{self.flow.pk}/steps/',
                               {'flow': self.flow.pk, 'name': 'bad', 'step_type': 'send_message', 'config': {}}, format='json')
        self.assertEqual(res.status_code, 400)


class DashboardEndpointsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('root', 'root@example.com', PASSWORD)
        self.client.force_authenticate(self.user)
        self.contact = Contact.objects.create(whatsapp_id='263770000001', name='Rudo Moyo')
        self.profile = CustomerProfile.objects.get_or_create(contact=self.contact, defaults={'first_name': 'Rudo'})[0]
        other = Contact.objects.create(whatsapp_id='263770000002', name='Luca Rossi')
        other_profile = CustomerProfile.objects.get_or_create(contact=other, defaults={'first_name': 'Luca'})[0]
        TourInquiry.objects.create(customer=self.profile, destinations='Mana Pools', lead_traveler_name='Rudo Moyo')
        TourInquiry.objects.create(customer=other_profile, destinations='Chobe', lead_traveler_name='Luca Rossi')
        day = timezone.localdate() + datetime.timedelta(days=2)
        Booking.objects.create(customer=self.profile, tour_name='Sunset Cruise', start_date=day, end_date=day,
                               number_of_adults=2, total_amount=100)

    def test_search_filter_backend_is_active(self):
        res = self.client.get('/crm-api/customer-data/inquiries/', {'search': 'Mana'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['count'], 1)

    def test_page_size_param_is_honoured(self):
        res = self.client.get('/crm-api/customer-data/inquiries/', {'page_size': 1})
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['count'], 2)

    def test_booking_stats(self):
        res = self.client.get('/crm-api/stats/bookings/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['kpis']['bookings_created'], 1)
        self.assertEqual(res.data['kpis']['open_inquiries'], 2)
        self.assertEqual(res.data['kpis']['pending_payment'], 1)
        # Unpaid bookings are not departures; they'd inflate the manifest headcount.
        self.assertEqual(res.data['upcoming_departures'], [])

    def test_mark_read_only_touches_incoming_received(self):
        now = timezone.now()
        Message.objects.create(contact=self.contact, wamid='w1', direction='in', message_type='text', content_payload={'body': 'hi'}, text_content='hi', timestamp=now, status='received')
        Message.objects.create(contact=self.contact, wamid='w2', direction='out', message_type='text', content_payload={'body': 'hello'}, text_content='hello', timestamp=now, status='delivered')
        res = self.client.post(f'/crm-api/conversations/contacts/{self.contact.pk}/mark-read/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['marked_read'], 1)
        self.assertEqual(Message.objects.get(wamid='w1').status, 'read')
        self.assertEqual(Message.objects.get(wamid='w2').status, 'delivered')


class TokenSizeTests(APITestCase):
    def test_superuser_token_stays_small(self):
        user = User.objects.create_superuser('root', 'root@example.com', PASSWORD)
        token = MyTokenObtainPairSerializer.get_token(user)
        self.assertEqual(token['permissions'], [])
        self.assertLess(len(str(token.access_token)), 4096)
