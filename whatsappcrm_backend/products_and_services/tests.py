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


import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from .models import GalleryImage

seed_gallery = importlib.import_module('products_and_services.migrations.0008_seed_gallery_images')


class GalleryTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        override = override_settings(MEDIA_ROOT=self.media)
        override.enable()
        self.addCleanup(override.disable)

    def make(self, **kwargs):
        return GalleryImage.objects.create(image=SimpleUploadedFile('p.jpg', b'jpegbytes', 'image/jpeg'), **kwargs)

    def test_seed_runs_once_and_files_are_served(self):
        GalleryImage.objects.all().delete()
        seed_gallery.seed_gallery(apps, None)
        self.assertEqual(GalleryImage.objects.count(), len(seed_gallery.SEED_IMAGES))
        seed_gallery.seed_gallery(apps, None)
        self.assertEqual(GalleryImage.objects.count(), len(seed_gallery.SEED_IMAGES))

        body = self.client.get('/crm-api/gallery/').json()
        self.assertEqual(body['count'], len(seed_gallery.SEED_IMAGES))
        first = body['images'][0]
        self.assertEqual(first['caption'], 'Kalai Safari Enigma Boat')
        response = self.client.get(first['url'] + '/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')

    def test_list_includes_optional_caption_and_year_and_hides_inactive(self):
        GalleryImage.objects.all().delete()
        self.make(caption='Hippos', year=2024, category='sunset')
        self.make()
        self.make(is_active=False)
        images = self.client.get('/crm-api/gallery/').json()['images']
        self.assertEqual(len(images), 2)
        self.assertEqual({(i['caption'], i['year']) for i in images}, {('Hippos', 2024), ('', None)})

    def test_hidden_image_file_is_staff_only(self):
        image = self.make(is_active=False)
        url = f'/crm-api/gallery/{image.pk}/0/'
        self.assertEqual(self.client.get(url).status_code, 404)
        staff = get_user_model().objects.create_user('staff', password='x', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_deleting_or_replacing_removes_file(self):
        image = self.make()
        storage, old = image.image.storage, image.image.name
        image.image = SimpleUploadedFile('new.jpg', b'other', 'image/jpeg')
        image.save()
        self.assertFalse(storage.exists(old))
        new = image.image.name
        GalleryImage.objects.filter(pk=image.pk).delete()
        self.assertFalse(storage.exists(new))
