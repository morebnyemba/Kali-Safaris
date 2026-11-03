"""
Every flow definition must only transition to steps that exist. A missing
target is skipped by `load_flows` with just a warning, which leaves the
customer stuck with no reply (as happened with booking_creation_failed).
"""
import importlib
import pkgutil

from django.test import SimpleTestCase

import flows.definitions as definitions


def _flow_definitions():
    for module_info in pkgutil.iter_modules(definitions.__path__):
        module = importlib.import_module(f'flows.definitions.{module_info.name}')
        for attr, value in vars(module).items():
            steps = value.get('steps') if isinstance(value, dict) else None
            if isinstance(steps, list) and steps and all(isinstance(s, dict) and 'name' in s for s in steps):
                yield f'{module_info.name}.{attr}', steps


class FlowStepReferenceTests(SimpleTestCase):
    def test_definitions_are_found(self):
        self.assertIn('booking_flow.BOOKING_FLOW', dict(_flow_definitions()))

    def test_every_transition_targets_an_existing_step(self):
        for flow, steps in _flow_definitions():
            names = {s['name'] for s in steps}
            dangling = sorted(
                (s['name'], t.get('to_step'))
                for s in steps for t in s.get('transitions', [])
                if t.get('to_step') not in names
            )
            with self.subTest(flow=flow):
                self.assertEqual(dangling, [], f'{flow} has transitions to missing steps')

    def test_step_names_are_unique(self):
        for flow, steps in _flow_definitions():
            names = [s['name'] for s in steps]
            with self.subTest(flow=flow):
                self.assertEqual(len(names), len(set(names)), f'{flow} has duplicate step names')


class BookingCreationFailedTests(SimpleTestCase):
    def setUp(self):
        from flows.definitions.booking_flow import BOOKING_FLOW
        self.steps = {s['name']: s for s in BOOKING_FLOW['steps']}

    def test_failed_booking_save_hands_over_to_staff(self):
        step = self.steps['booking_creation_failed']
        self.assertEqual(step['type'], 'human_handover')
        self.assertIn('not been charged', step['config']['pre_handover_message_text'])

    def test_only_reached_when_no_booking_was_created(self):
        for name, success_step in (('create_booking_for_card_web', 'save_travelers_for_card_web'),
                                   ('create_booking_for_cbz', 'save_travelers_for_cbz')):
            transitions = sorted(self.steps[name]['transitions'], key=lambda t: t['priority'])
            with self.subTest(step=name):
                self.assertEqual(transitions[0]['to_step'], success_step)
                self.assertEqual(transitions[0]['condition_config'],
                                 {'type': 'variable_exists', 'variable_name': 'created_booking.id'})
                self.assertEqual(transitions[-1]['to_step'], 'booking_creation_failed')
