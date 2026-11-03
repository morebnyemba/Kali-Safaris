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


import io
import shutil
import tempfile

from PIL import Image

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

    def test_hidden_image_file_still_loads_for_previews(self):
        image = self.make(is_active=False)
        self.assertEqual(self.client.get(f'/crm-api/gallery/{image.pk}/0/').status_code, 200)

    def test_manage_api_requires_login(self):
        self.assertEqual(self.client.get('/crm-api/gallery/manage/').status_code, 401)

    def test_manage_api_upload_edit_delete(self):
        GalleryImage.objects.all().delete()
        user = get_user_model().objects.create_user('agent', password='x')
        self.client.force_login(user)

        photo = io.BytesIO()
        Image.new('RGB', (4, 4), 'orange').save(photo, 'JPEG')
        photo.seek(0)
        photo.name = 'river.jpg'
        response = self.client.post('/crm-api/gallery/manage/', {'image': photo, 'category': 'sunset', 'caption': 'Hippos', 'year': 2025})
        self.assertEqual(response.status_code, 201, response.content)
        created = response.json()
        self.assertEqual((created['caption'], created['year'], created['category']), ('Hippos', 2025, 'sunset'))
        self.assertTrue(created['is_active'])
        self.assertEqual(self.client.get('/crm-api/gallery/').json()['count'], 1)
        self.assertEqual(self.client.get(created['image_url']).status_code, 200)

        # Caption and year are optional and can be cleared.
        response = self.client.patch(f"/crm-api/gallery/manage/{created['id']}/", {'caption': '', 'year': None, 'is_active': False}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual((response.json()['caption'], response.json()['year']), ('', None))
        self.assertEqual(self.client.get('/crm-api/gallery/').json()['count'], 0)

        bad = self.client.patch(f"/crm-api/gallery/manage/{created['id']}/", {'year': 25}, content_type='application/json')
        self.assertEqual(bad.status_code, 400)

        entry = GalleryImage.objects.get(pk=created['id'])
        storage, name = entry.image.storage, entry.image.name
        self.assertEqual(self.client.delete(f"/crm-api/gallery/manage/{created['id']}/").status_code, 204)
        self.assertFalse(storage.exists(name))

    def test_manage_api_requires_a_photo_on_upload(self):
        self.client.force_login(get_user_model().objects.create_user('agent', password='x'))
        response = self.client.post('/crm-api/gallery/manage/', {'category': 'boat'})
        self.assertEqual(response.status_code, 400)

    def test_deleting_or_replacing_removes_file(self):
        image = self.make()
        storage, old = image.image.storage, image.image.name
        image.image = SimpleUploadedFile('new.jpg', b'other', 'image/jpeg')
        image.save()
        self.assertFalse(storage.exists(old))
        new = image.image.name
        GalleryImage.objects.filter(pk=image.pk).delete()
        self.assertFalse(storage.exists(new))
