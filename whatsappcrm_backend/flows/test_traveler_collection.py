"""
Tests for WhatsApp traveler collection: the booking flow's traveler loop
templates and the save_travelers_to_booking action.
"""
from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from conversations.models import Contact
from customer_data.models import Booking, Traveler
from flows.actions import _extract_media_id, save_travelers_to_booking, validate_travelers_details
from flows.definitions.booking_flow import BOOKING_FLOW
from flows.services import _coerce_literal, _resolve_value


def _step(name):
    return next(s for s in BOOKING_FLOW['steps'] if s['name'] == name)


class TravelerLoopTemplateTests(TestCase):
    def setUp(self):
        self.contact = Mock(spec=Contact)
        self.contact.id = 1

    def _run_actions(self, step_name, ctx):
        for action in _step(step_name)['config']['actions_to_run']:
            value = _resolve_value(action['value_template'], ctx, self.contact)
            ctx[action['variable_name']] = _coerce_literal(value)

    def _prompt(self, ctx):
        body = _step('ask_traveler_name')['config']['message_config']['text']['body']
        return _resolve_value(body, ctx, self.contact)

    def test_text_path_collects_all_travelers_with_correct_labels(self):
        # Text fallback path never sets current_traveler_id_document; that must
        # not corrupt the list, and adult/child labels must follow the index.
        ctx = {'travelers_details': [], 'num_adults': 2, 'num_children': 1}
        self._run_actions('initialize_traveler_loop', ctx)

        people = [('Ann', 30), ('Ben', 32), ('Cara', 0)]
        prompts = []
        for name, age in people:
            prompts.append(self._prompt(ctx))
            ctx.update(
                current_traveler_name=name, current_traveler_age=age,
                current_traveler_nationality='Zimbabwean', current_traveler_gender='female',
                current_traveler_id_number='AB12345', current_traveler_medical='none',
            )
            self._run_actions('add_traveler_to_list', ctx)

        self.assertIn('Adult 1 of 2', prompts[0])
        self.assertIn('Adult 2 of 2', prompts[1])
        self.assertIn('Child 1 of 1', prompts[2])

        travelers = ctx['travelers_details']
        self.assertIsInstance(travelers, list)
        self.assertEqual([t['name'] for t in travelers], ['Ann', 'Ben', 'Cara'])
        self.assertEqual([t['type'] for t in travelers], ['adult', 'adult', 'child'])
        self.assertEqual(travelers[2]['age'], '0')
        self.assertEqual(ctx['traveler_index'], 4)

    def test_photo_picker_payload_survives_list_building(self):
        ctx = {'travelers_details': [], 'num_adults': 1, 'num_children': 0}
        self._run_actions('initialize_traveler_loop', ctx)
        ctx.update(
            current_traveler_name="O'Brien", current_traveler_age='40',
            current_traveler_nationality='Irish', current_traveler_gender='male',
            current_traveler_id_number='P1234567', current_traveler_medical='',
            current_traveler_id_document=[{'media_id': '998877', 'file_name': 'id.jpg'}],
        )
        self._run_actions('add_traveler_to_list', ctx)
        traveler = ctx['travelers_details'][0]
        self.assertEqual(traveler['name'], "O'Brien")
        self.assertEqual(_extract_media_id(traveler['id_document']), '998877')
        self.assertEqual(ctx['current_traveler_id_document'], '')


class ExtractMediaIdTests(TestCase):
    def test_variants(self):
        self.assertEqual(_extract_media_id('12345'), '12345')
        self.assertEqual(_extract_media_id([{'media_id': 'abc', 'cdn_url': 'x'}]), 'abc')
        self.assertEqual(_extract_media_id({'id': 'xyz'}), 'xyz')
        self.assertEqual(_extract_media_id("[{'media_id': 'm1'}]"), 'm1')
        self.assertEqual(_extract_media_id('[{"media_id": "m2"}]'), 'm2')
        self.assertEqual(_extract_media_id(''), '')
        self.assertEqual(_extract_media_id(None), '')
        self.assertEqual(_extract_media_id('None'), '')
        self.assertEqual(_extract_media_id([]), '')


class SaveTravelersToBookingTests(TestCase):
    def setUp(self):
        self.contact = Contact.objects.create(whatsapp_id='263770000001', name='Tester')
        start = timezone.now().date() + timedelta(days=10)
        self.booking = Booking.objects.create(
            booking_reference='BK-TEST-0001', tour_name='Sunset Cruise',
            start_date=start, end_date=start, number_of_adults=2, number_of_children=1,
        )

    def _save(self, travelers):
        context = {'created_booking': {'id': self.booking.id}, 'travelers_details': travelers}
        return save_travelers_to_booking(self.contact, context, {})

    def _traveler(self, name, age='30', **extra):
        data = {'name': name, 'age': age, 'nationality': 'Zimbabwean', 'gender': 'f',
                'id_number': f'ID{name}', 'medical': 'none', 'type': 'adult', 'id_document': ''}
        data.update(extra)
        return data

    def test_saves_infant_normalises_fields_and_is_idempotent(self):
        travelers = [
            self._traveler('Ann'),
            self._traveler('Ben', type='bogus'),
            self._traveler('Cara', age='0', type='child'),
        ]
        ctx = self._save(travelers)
        self.assertEqual(ctx['travelers_saved_count'], 3)

        saved = {t.name: t for t in self.booking.travelers.all()}
        self.assertEqual(saved['Cara'].age, 0)
        self.assertEqual(saved['Cara'].traveler_type, Traveler.TravelerType.CHILD)
        self.assertEqual(saved['Ben'].traveler_type, Traveler.TravelerType.ADULT)
        self.assertEqual(saved['Ann'].gender, 'Female')
        self.assertEqual(saved['Ann'].medical_dietary_requirements, '')

        # Re-running (flow retry) must not duplicate travelers.
        ctx = self._save(travelers)
        self.assertEqual(ctx['travelers_saved_count'], 0)
        self.assertEqual(self.booking.travelers.count(), 3)

    def test_never_exceeds_booked_passengers(self):
        travelers = [self._traveler(n) for n in ('Ann', 'Ben', 'Cal', 'Dan', 'Eve')]
        self._save(travelers)
        self.assertEqual(self.booking.travelers.count(), 3)

    def test_skips_missing_or_invalid_age(self):
        self._save([self._traveler('NoAge', age=''), self._traveler('Words', age='thirty'),
                    self._traveler('NoneStr', age='None')])
        self.assertEqual(self.booking.travelers.count(), 0)

    @patch('meta_integration.utils.download_whatsapp_media', return_value=(b'\xff\xd8jpeg', 'image/jpeg'))
    def test_photo_picker_list_downloads_by_media_id(self, mock_download):
        self._save([self._traveler('Ann', id_document=[{'media_id': 'MEDIA42', 'file_name': 'x.jpg'}])])
        mock_download.assert_called_once()
        self.assertEqual(mock_download.call_args[0][0], 'MEDIA42')
        self.assertTrue(self.booking.travelers.get().id_document)


class BookingCreationGateTests(TestCase):
    """No booking may be created in the WhatsApp flow without full traveler details."""

    def _ctx(self, travelers, adults=2, children=0):
        return {'travelers_details': travelers, 'num_adults': adults, 'num_children': children}

    def _traveler(self, name, **extra):
        data = {'name': name, 'age': '30', 'nationality': 'Zimbabwean', 'gender': 'male',
                'id_number': f'ID-{name}', 'medical': '', 'type': 'adult'}
        data.update(extra)
        return data

    def test_complete_details_pass(self):
        ctx = validate_travelers_details(None, self._ctx([self._traveler('Ann'), self._traveler('Ben')]), {})
        self.assertEqual(ctx['travelers_valid'], 'yes')
        self.assertEqual(ctx['travelers_validation_error'], '')

    def test_blocks_missing_count_fields_and_duplicates(self):
        cases = [
            [self._traveler('Ann')],                                    # 1 of 2
            [self._traveler('Ann'), self._traveler('Ben', id_number='')],
            [self._traveler('Ann'), self._traveler('Ben', nationality='None')],
            [self._traveler('Ann'), self._traveler('Ben', age='thirty')],
            [self._traveler('Ann'), self._traveler('Ben', gender='x')],
            [self._traveler('Ann'), self._traveler('Ann')],             # duplicate
            'not-a-list',
        ]
        for travelers in cases:
            ctx = validate_travelers_details(None, self._ctx(travelers), {})
            self.assertEqual(ctx['travelers_valid'], 'no', travelers)
            self.assertTrue(ctx['travelers_validation_error'])

    def test_every_booking_create_step_is_behind_the_gate(self):
        """All paths to a Booking create step pass through validate_travelers_before_booking."""
        steps = {s['name']: s for s in BOOKING_FLOW['steps']}
        creates = {
            name for name, s in steps.items()
            if any(a.get('action_type') == 'create_model_instance' and a.get('model_name') == 'Booking'
                   for a in s.get('config', {}).get('actions_to_run', []))
        }
        self.assertTrue(creates)

        # Walk from the entry point without passing through the gate.
        entry = next(n for n, s in steps.items() if s.get('is_entry_point'))
        seen, stack = set(), [entry]
        while stack:
            name = stack.pop()
            if name in seen or name == 'validate_travelers_before_booking' or name not in steps:
                continue
            seen.add(name)
            stack.extend(t['to_step'] for t in steps[name].get('transitions', []))
        self.assertFalse(creates & seen, f"Reachable without the traveler gate: {creates & seen}")

        gate = steps['validate_travelers_before_booking']
        self.assertEqual(gate['transitions'][0]['to_step'], 'ask_email')
        self.assertEqual(gate['transitions'][0]['condition_config']['value'], 'yes')
