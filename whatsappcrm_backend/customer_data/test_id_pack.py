"""ID packs: numbered like the park manifest, as a printable PDF and a ZIP of the ID files."""
import csv
import io
import shutil
import tempfile
import zipfile
from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Booking, Traveler

MEDIA = tempfile.mkdtemp(prefix='idpack-media-')


def _png(color):
    from PIL import Image
    out = io.BytesIO()
    Image.new('RGB', (900, 560), color).save(out, 'PNG')
    return out.getvalue()


@override_settings(MEDIA_ROOT=MEDIA, STAFF_ALERT_EMAILS=[])
class IdPackTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.day = timezone.localdate() + timedelta(days=12)
        self.api = APIClient()
        self.api.force_authenticate(get_user_model().objects.create_user('ops', 'o@example.com', 'x', is_staff=True))
        # Manifest order: 06:00 departure first, then 16:00.
        self.late = self.booking('BK-LATE', time(16, 0), [('Zara Ncube', 'ZN111', 'red'), ('Yemi Ncube', 'YN222', None)])
        self.early = self.booking('BK-EARLY', time(6, 0), [('Ann Moyo', 'AM333', 'blue'), ('Ben Moyo', 'BM444', 'green')])

    def booking(self, ref, start, people, status='paid'):
        booking = Booking.objects.create(tour_name='Sunset Cruise', start_date=self.day, end_date=self.day, start_time=start,
                                         number_of_adults=len(people), total_amount=Decimal('100'), booking_reference=ref)
        for name, id_no, colour in people:
            t = Traveler.objects.create(booking=booking, name=name, age=30, nationality='Zimbabwean', gender='female', id_number=id_no)
            if colour:
                t.id_document.save(f'{id_no}.png', ContentFile(_png(colour)), save=True)
        Booking.objects.filter(pk=booking.pk).update(payment_status=status)
        booking.refresh_from_db()
        return booking

    def get(self, **params):
        return self.api.get('/crm-api/customer-data/export/id-pack/', params)

    def test_zip_files_are_named_with_manifest_numbers(self):
        res = self.get(date=self.day.isoformat(), format='zip')
        self.assertEqual(res.status_code, 200, res.content[:300])
        zf = zipfile.ZipFile(io.BytesIO(res.content))
        names = sorted(n for n in zf.namelist() if n.endswith('.png'))
        # Manifest numbers 1-2 = the 06:00 group (Ann, Ben), 3-4 = the 16:00 group (Yemi has no file, Zara is 4).
        self.assertEqual(names, ['01_Ann-Moyo_AM333.png', '02_Ben-Moyo_BM444.png', '04_Zara-Ncube_ZN111.png'])
        index = list(csv.DictReader(io.StringIO(zf.read('index.csv').decode())))
        self.assertEqual([(r['No'], r['Full name'], r['ID copy']) for r in index],
                         [('1', 'Ann Moyo', 'On file'), ('2', 'Ben Moyo', 'On file'), ('3', 'Yemi Ncube', 'MISSING'),
                          ('4', 'Zara Ncube', 'On file')])

    def test_pdf_has_index_and_images(self):
        res = self.get(date=self.day.isoformat(), format='pdf')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.content.startswith(b'%PDF'))
        self.assertIn(b'/Subtype /Image', res.content)          # ID copies embedded
        self.assertGreater(res.content.count(b'/Subtype /Image'), 2)

    def test_one_booking_keeps_its_manifest_numbers(self):
        res = self.get(booking=self.late.pk, format='zip')
        names = [n for n in zipfile.ZipFile(io.BytesIO(res.content)).namelist() if n.endswith('.png')]
        self.assertEqual(names, ['04_Zara-Ncube_ZN111.png'])
        self.assertIn('id_pack_BK-LATE.zip', res['Content-Disposition'])

    def test_unconfirmed_booking_is_numbered_on_its_own(self):
        held = self.booking('BK-HELD', time(16, 0), [('Cara Dube', 'CD555', 'red')], status='pending')
        res = self.get(booking=held.pk, format='zip')
        index = zipfile.ZipFile(io.BytesIO(res.content)).read('index.csv').decode()
        self.assertIn('1,Cara Dube,CD555', index)
        self.assertIn('not yet', index)

    def test_bad_requests(self):
        self.assertEqual(self.get(format='pdf').status_code, 400)
        self.assertEqual(self.get(date=self.day.isoformat(), format='doc').status_code, 400)
        self.assertEqual(APIClient().get('/crm-api/customer-data/export/id-pack/', {'date': self.day.isoformat()}).status_code, 401)
