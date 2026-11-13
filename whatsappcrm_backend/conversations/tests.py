from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Contact


class ContactListFilterTests(TestCase):
    """The dashboard pages these server-side, so every filter must run in the query (not in the browser)."""

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(get_user_model().objects.create_user('agent', 'a@example.com', 'x', is_staff=True))
        for i in range(25):
            Contact.objects.create(whatsapp_id=f'2637700000{i:02d}', name=f'C{i}', is_blocked=i < 3,
                                   needs_human_intervention=i % 5 == 0)

    def get(self, **params):
        return self.api.get('/crm-api/conversations/contacts/', params).json()

    def test_blocked_filter_counts_across_pages(self):
        data = self.get(is_blocked='true', page_size=2)
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['results']), 2)
        self.assertEqual(self.get(is_blocked='false')['count'], 22)

    def test_unknown_values_are_ignored_and_filters_combine(self):
        self.assertEqual(self.get(is_blocked='maybe')['count'], 25)
        self.assertEqual(self.get(is_blocked='true', needs_human_intervention='true')['count'], 1)
