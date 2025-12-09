"""
Test for the traveler collection loop in the booking flow.
This test validates that the loop correctly collects details for all travelers,
not just the first 2.
"""

from django.test import TestCase
from unittest.mock import Mock
from flows.services import _evaluate_transition_condition
from flows.models import Flow, FlowStep, FlowTransition
from conversations.models import Contact


class TravelerLoopConditionTests(TestCase):
    """Tests for the traveler collection loop condition in booking flow."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects
        self.contact = Mock(spec=Contact)
        self.contact.id = 1
        
        self.flow = Mock(spec=Flow)
        self.flow.id = 1
        self.flow.name = "booking_flow"
        
        self.step = Mock(spec=FlowStep)
        self.step.id = 1
        self.step.flow = self.flow
        
        self.transition = Mock(spec=FlowTransition)
        self.transition.id = 1
        self.transition.current_step = self.step
        
        self.message_data = {'type': 'text', 'text': {'body': 'test'}}
        self.message_obj = Mock()

    def test_traveler_loop_with_2_travelers(self):
        """Test that loop correctly handles 2 travelers."""
        self.transition.condition_config = {
            'type': 'variable_less_than_or_equal',
            'variable_name': 'traveler_index',
            'value_template': '{{ num_travelers|int }}'
        }
        
        # Test cases for 2 travelers (index represents next traveler to collect after increment)
        test_cases = [
            (1, 2, True, "Should continue to collect traveler 1"),
            (2, 2, True, "Should continue to collect traveler 2"),
            (3, 2, False, "Should stop after collecting all 2 travelers"),
        ]
        
        for traveler_index, num_travelers, expected, description in test_cases:
            with self.subTest(traveler_index=traveler_index, num_travelers=num_travelers):
                flow_context = {
                    'traveler_index': traveler_index,
                    'num_travelers': num_travelers
                }
                
                result = _evaluate_transition_condition(
                    self.transition, self.contact, self.message_data, flow_context, self.message_obj
                )
                self.assertEqual(result, expected, description)

    def test_traveler_loop_with_10_travelers(self):
        """Test that loop correctly handles 10 travelers."""
        self.transition.condition_config = {
            'type': 'variable_less_than_or_equal',
            'variable_name': 'traveler_index',
            'value_template': '{{ num_travelers|int }}'
        }
        
        num_travelers = 10
        
        # Should continue for indexes 1 through 10
        for traveler_index in range(1, 11):
            with self.subTest(traveler_index=traveler_index):
                flow_context = {
                    'traveler_index': traveler_index,
                    'num_travelers': num_travelers
                }
                
                result = _evaluate_transition_condition(
                    self.transition, self.contact, self.message_data, flow_context, self.message_obj
                )
                self.assertTrue(result, f"Should continue at index {traveler_index} of {num_travelers}")
        
        # Should stop at index 11
        flow_context = {
            'traveler_index': 11,
            'num_travelers': num_travelers
        }
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertFalse(result, "Should stop at index 11 after collecting all 10 travelers")

    def test_traveler_loop_with_22_travelers(self):
        """Test that loop correctly handles 22 travelers."""
        self.transition.condition_config = {
            'type': 'variable_less_than_or_equal',
            'variable_name': 'traveler_index',
            'value_template': '{{ num_travelers|int }}'
        }
        
        num_travelers = 22
        
        # Test a few key points
        test_cases = [
            (1, True, "Should continue at index 1"),
            (2, True, "Should continue at index 2"),
            (3, True, "Should continue at index 3"),
            (10, True, "Should continue at index 10"),
            (21, True, "Should continue at index 21"),
            (22, True, "Should continue at index 22"),
            (23, False, "Should stop at index 23"),
        ]
        
        for traveler_index, expected, description in test_cases:
            with self.subTest(traveler_index=traveler_index):
                flow_context = {
                    'traveler_index': traveler_index,
                    'num_travelers': num_travelers
                }
                
                result = _evaluate_transition_condition(
                    self.transition, self.contact, self.message_data, flow_context, self.message_obj
                )
                self.assertEqual(result, expected, description)

    def test_traveler_loop_with_string_values(self):
        """Test that loop correctly handles string representations of numbers."""
        self.transition.condition_config = {
            'type': 'variable_less_than_or_equal',
            'variable_name': 'traveler_index',
            'value_template': '{{ num_travelers|int }}'
        }
        
        # Test with string values (as might happen from template rendering)
        flow_context = {
            'traveler_index': '3',  # String representation
            'num_travelers': '10'   # String representation
        }
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertTrue(result, "Should handle string representations correctly")

    def test_num_travelers_calculation(self):
        """Test that num_travelers is calculated correctly from num_adults and num_children."""
        # This tests the template: {{ num_adults|int + num_children|int }}
        from jinja2 import Environment
        
        env = Environment()
        template = env.from_string("{{ num_adults|int + num_children|int }}")
        
        test_cases = [
            ({'num_adults': 2, 'num_children': 0}, '2'),
            ({'num_adults': 10, 'num_children': 0}, '10'),
            ({'num_adults': 20, 'num_children': 2}, '22'),
            ({'num_adults': '5', 'num_children': '5'}, '10'),  # String inputs
        ]
        
        for context, expected in test_cases:
            with self.subTest(context=context):
                result = template.render(context)
                self.assertEqual(result, expected,
                    f"num_adults={context['num_adults']}, num_children={context['num_children']} should equal {expected}")
