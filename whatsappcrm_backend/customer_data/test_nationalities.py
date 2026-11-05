"""Nationality picker: one list everywhere, canonical values on manifests."""
import re
from pathlib import Path

from django.test import SimpleTestCase, TestCase

from conversations.models import Contact
from flows.models import FlowStep
from flows.services import _execute_step_actions

from .nationalities import (
    COMMON, COMMON_COUNTRIES, COUNTRIES, COUNTRY_OF, NATIONALITIES, OTHER_COUNTRIES, OTHERS,
    nationality_id, normalize_country, normalize_nationality, whatsapp_options,
)
from .traveler_validation import normalize_traveler

REPO = Path(__file__).resolve().parents[2]


def _js_array(path, name):
    source = (REPO / path).read_text()
    body = re.search(rf"export const {name}[^=]*=\s*\[(.*?)\];", source, re.S).group(1)
    return re.findall(r"'((?:[^'\\]|\\.)*)'", body)


class NationalityListTests(SimpleTestCase):
    def test_list_is_clean(self):
        self.assertEqual(len(NATIONALITIES), len({n.lower() for n in NATIONALITIES}))
        self.assertEqual(len({nationality_id(n) for n in NATIONALITIES}), len(NATIONALITIES))
        self.assertEqual(OTHERS, sorted(OTHERS))
        self.assertEqual(COMMON[0], 'Zimbabwean')

    def test_website_and_dashboard_copies_match(self):
        for path in ('public-website/src/lib/nationalities.ts', 'whatsapp-crm-frontend/src/lib/nationalities.js'):
            with self.subTest(path=path):
                self.assertEqual(_js_array(path, 'COMMON_NATIONALITIES'), COMMON)
                self.assertEqual(_js_array(path, 'OTHER_NATIONALITIES'), OTHERS)
                self.assertEqual(_js_array(path, 'COMMON_COUNTRIES'), COMMON_COUNTRIES)
                self.assertEqual(_js_array(path, 'OTHER_COUNTRIES'), OTHER_COUNTRIES)

    def test_every_nationality_has_its_country(self):
        self.assertEqual(set(COUNTRY_OF), set(NATIONALITIES))
        self.assertEqual(len(COUNTRIES), len(set(COUNTRIES)))
        self.assertEqual(COMMON_COUNTRIES[:3], ['Zimbabwe', 'South Africa', 'Zambia'])
        self.assertEqual(OTHER_COUNTRIES, sorted(OTHER_COUNTRIES))
        self.assertEqual(normalize_country('  zimbabwe '), 'Zimbabwe')
        self.assertEqual(normalize_country('Atlantis'), 'Atlantis')

    def test_normalize(self):
        self.assertEqual(normalize_nationality('zimbabwean'), 'Zimbabwean')
        self.assertEqual(normalize_nationality('south_african'), 'South African')
        self.assertEqual(normalize_nationality('  congolese_drc '), 'Congolese (DRC)')
        self.assertEqual(normalize_nationality('Martian'), 'Martian')  # typed under "Other": kept as typed

    def test_whatsapp_dropdown_fits_the_200_option_cap(self):
        options = whatsapp_options()
        self.assertLessEqual(len(options), 200)
        self.assertEqual(len({o['id'] for o in options}), len(options))
        self.assertEqual(options[-1]['id'], 'other')

    def test_validation_stores_canonical_value_and_rejects_bare_other(self):
        base = {'name': 'Ann Moyo', 'age': 30, 'gender': 'female', 'id_number': 'AB123456'}
        cleaned, error = normalize_traveler({**base, 'nationality': 'south_african'})
        self.assertIsNone(error)
        self.assertEqual(cleaned['nationality'], 'South African')
        _, error = normalize_traveler({**base, 'nationality': 'other'})
        self.assertIn('nationality is required', error)


class WhatsAppNationalityStepsTests(TestCase):
    def setUp(self):
        from flows.definitions.booking_flow import BOOKING_FLOW
        self.steps = {s['name']: s for s in BOOKING_FLOW['steps']}
        self.contact = Contact.objects.create(whatsapp_id='263770000077', name='Nat Test')

    def run_step(self, name, context):
        step_def = self.steps[name]
        step = FlowStep(name=name, step_type=step_def['type'], config=step_def['config'])
        _, ctx = _execute_step_actions(step, self.contact, dict(context))
        return ctx

    def test_form_answers_become_readable_names(self):
        ctx = self.run_step('process_traveler_details_response', {'traveler_details_response': {
            'traveler_name': 'Ann', 'traveler_nationality': 'south_african', 'traveler_gender': 'female'}})
        self.assertEqual(ctx['current_traveler_nationality'], 'South African')
        ctx = self.run_step('process_traveler_details_response', {'traveler_details_response': {
            'traveler_name': 'Ann', 'traveler_nationality': 'other', 'traveler_nationality_other': ' Kenyan '}})
        self.assertEqual(ctx['current_traveler_nationality'], 'Kenyan')

    def test_text_fallback_choice_becomes_readable_name(self):
        ctx = self.run_step('set_traveler_nationality_name', {'current_traveler_nationality': 'zambian'})
        self.assertEqual(ctx['current_traveler_nationality'], 'Zambian')

    def test_fallback_list_and_buttons_fit_whatsapp_limits(self):
        rows = self.steps['ask_traveler_nationality']['config']['message_config']['interactive']['action']['sections'][0]['rows']
        self.assertLessEqual(len(rows), 10)
        self.assertTrue(all(len(r['title']) <= 24 for r in rows))
        self.assertTrue(all(normalize_nationality(r['id']) == r['title'] for r in rows if r['id'] != 'other'))
        buttons = self.steps['ask_traveler_gender']['config']['message_config']['interactive']['action']['buttons']
        self.assertEqual([b['reply']['id'] for b in buttons], ['male', 'female', 'other'])


class CountryStorageTests(TestCase):
    def test_website_checkout_and_profile_api_store_canonical_country(self):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        from cbz_integration.views import _resolve_web_customer_profile
        from .models import CustomerProfile

        profile = _resolve_web_customer_profile('Ann Moyo', 'ann@example.com', '0771234567', 'south africa')
        self.assertEqual(profile.country, 'South Africa')

        client = APIClient()
        client.force_authenticate(get_user_model().objects.create_superuser('root', 'r@example.com', 'x'))
        response = client.patch(f'/crm-api/customer-data/profiles/{profile.pk}/', {'country': 'united kingdom'}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(CustomerProfile.objects.get(pk=profile.pk).country, 'United Kingdom')
