import importlib
from decimal import Decimal

from django.apps import apps
from django.test import TestCase

from .models import Tour

dedupe = importlib.import_module('products_and_services.migrations.0006_deactivate_duplicate_tours')


class DeactivateDuplicateToursMigrationTests(TestCase):
    """The 0005 seed already ran on the test DB, so all nine default tours exist and are active."""

    def run_migration(self):
        dedupe.deactivate_duplicates(apps, None)

    def active(self, name):
        return Tour.objects.get(name=name).is_active

    def test_same_priced_duplicates_are_deactivated_not_deleted(self):
        Tour.objects.filter(name__in=['Dinner Cruise Package (Per Person)', 'River Cruise with Cash Bar']).update(is_active=True)
        self.run_migration()
        self.assertFalse(self.active('Dinner Cruise Package (Per Person)'))
        self.assertFalse(self.active('River Cruise with Cash Bar'))
        for name in ['Dinner Cruise', 'Sunrise Cruise', 'Lunch Cruise', 'Sunset Cruise',
                     'Premium River Cruise (Breakfast, Lunch or Sunset)', 'Learners Special Cruise Package', 'Jetty Venue Hire']:
            self.assertTrue(self.active(name), name)

    def test_duplicate_repriced_by_owner_is_left_alone(self):
        Tour.objects.filter(name='Dinner Cruise Package (Per Person)').update(is_active=True, base_price=Decimal('90.00'))
        self.run_migration()
        self.assertTrue(self.active('Dinner Cruise Package (Per Person)'))

    def test_no_canonical_tour_means_no_change(self):
        Tour.objects.filter(name='Dinner Cruise Package (Per Person)').update(is_active=True)
        Tour.objects.filter(name='Dinner Cruise').update(is_active=False)
        self.run_migration()
        self.assertTrue(self.active('Dinner Cruise Package (Per Person)'))

    def test_public_tour_list_hides_duplicates(self):
        self.run_migration()
        names = [t['name'] for t in self.client.get('/crm-api/tours/', HTTP_HOST='localhost').json()['tours']]
        self.assertNotIn('Dinner Cruise Package (Per Person)', names)
        self.assertNotIn('River Cruise with Cash Bar', names)
        self.assertIn('Dinner Cruise', names)
