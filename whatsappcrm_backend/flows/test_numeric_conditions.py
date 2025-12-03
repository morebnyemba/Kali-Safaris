"""
Tests for numeric comparison conditions in flow transitions.
Validates that the newly added variable comparison conditions work correctly.
"""

from django.test import TestCase
from unittest.mock import Mock
from flows.services import _evaluate_transition_condition
from flows.models import Flow, FlowStep, FlowTransition
from conversations.models import Contact


class NumericComparisonConditionTests(TestCase):
    """Tests for numeric comparison conditions: less_than, greater_than, etc."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects
        self.contact = Mock(spec=Contact)
        self.contact.id = 1
        
        self.flow = Mock(spec=Flow)
        self.flow.id = 1
        self.flow.name = "test_flow"
        
        self.step = Mock(spec=FlowStep)
        self.step.id = 1
        self.step.flow = self.flow
        
        self.transition = Mock(spec=FlowTransition)
        self.transition.id = 1
        self.transition.current_step = self.step
        
        self.message_data = {'type': 'text', 'text': {'body': 'test'}}
        self.message_obj = Mock()

    def test_variable_less_than_or_equal_true(self):
        """Test variable_less_than_or_equal returns True when condition is met."""
        self.transition.condition_config = {
            'type': 'variable_less_than_or_equal',
            'variable_name': 'traveler_index',
            'value_template': '{{ num_travelers }}'
        }
        flow_context = {
            'traveler_index': 3,
            'num_travelers': 5
        }
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertTrue(result)

    def test_variable_less_than_or_equal_equal(self):
        """Test variable_less_than_or_equal returns True when values are equal."""
        self.transition.condition_config = {
            'type': 'variable_less_than_or_equal',
            'variable_name': 'traveler_index',
            'value_template': '{{ num_travelers }}'
        }
        flow_context = {
            'traveler_index': 5,
            'num_travelers': 5
        }
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertTrue(result)

    def test_variable_less_than_or_equal_false(self):
        """Test variable_less_than_or_equal returns False when condition is not met."""
        self.transition.condition_config = {
            'type': 'variable_less_than_or_equal',
            'variable_name': 'traveler_index',
            'value_template': '{{ num_travelers }}'
        }
        flow_context = {
            'traveler_index': 6,
            'num_travelers': 5
        }
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertFalse(result)

    def test_variable_less_than_true(self):
        """Test variable_less_than returns True when condition is met."""
        self.transition.condition_config = {
            'type': 'variable_less_than',
            'variable_name': 'current_value',
            'value_template': '10'
        }
        flow_context = {'current_value': 5}
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertTrue(result)

    def test_variable_less_than_false_equal(self):
        """Test variable_less_than returns False when values are equal."""
        self.transition.condition_config = {
            'type': 'variable_less_than',
            'variable_name': 'current_value',
            'value_template': '10'
        }
        flow_context = {'current_value': 10}
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertFalse(result)

    def test_variable_greater_than_or_equal_true(self):
        """Test variable_greater_than_or_equal returns True when condition is met."""
        self.transition.condition_config = {
            'type': 'variable_greater_than_or_equal',
            'variable_name': 'age',
            'value_template': '18'
        }
        flow_context = {'age': 25}
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertTrue(result)

    def test_variable_greater_than_true(self):
        """Test variable_greater_than returns True when condition is met."""
        self.transition.condition_config = {
            'type': 'variable_greater_than',
            'variable_name': 'score',
            'value_template': '50'
        }
        flow_context = {'score': 75}
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertTrue(result)

    def test_variable_greater_than_false(self):
        """Test variable_greater_than returns False when condition is not met."""
        self.transition.condition_config = {
            'type': 'variable_greater_than',
            'variable_name': 'score',
            'value_template': '50'
        }
        flow_context = {'score': 50}
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertFalse(result)

    def test_numeric_comparison_with_string_numbers(self):
        """Test that numeric comparisons work with string representations of numbers."""
        self.transition.condition_config = {
            'type': 'variable_less_than_or_equal',
            'variable_name': 'count',
            'value_template': '10'
        }
        flow_context = {'count': '5'}  # String representation
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertTrue(result)

    def test_numeric_comparison_with_invalid_value(self):
        """Test that numeric comparisons handle invalid values gracefully."""
        self.transition.condition_config = {
            'type': 'variable_less_than_or_equal',
            'variable_name': 'count',
            'value_template': '10'
        }
        flow_context = {'count': 'not_a_number'}
        
        result = _evaluate_transition_condition(
            self.transition, self.contact, self.message_data, flow_context, self.message_obj
        )
        self.assertFalse(result)  # Should return False when conversion fails
