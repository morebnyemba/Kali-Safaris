"""
Tests for new WhatsApp flow definitions.
Validates the structure and data integrity of the converted flows.
"""

from django.test import TestCase
from flows.definitions.site_inspection_whatsapp_flow import (
    SITE_INSPECTION_WHATSAPP_FLOW,
    SITE_INSPECTION_FLOW_METADATA
)
from flows.definitions.loan_application_whatsapp_flow import (
    LOAN_APPLICATION_WHATSAPP_FLOW,
    LOAN_APPLICATION_FLOW_METADATA
)
from flows.definitions.solar_cleaning_whatsapp_flow import (
    SOLAR_CLEANING_WHATSAPP_FLOW,
    SOLAR_CLEANING_FLOW_METADATA
)


class FlowStructureValidationTest(TestCase):
    """Validate the structure of WhatsApp flow definitions"""
    
    def test_site_inspection_flow_structure(self):
        """Test that site inspection flow has correct structure"""
        # Check basic structure
        self.assertIn('version', SITE_INSPECTION_WHATSAPP_FLOW)
        self.assertIn('screens', SITE_INSPECTION_WHATSAPP_FLOW)
        self.assertEqual(SITE_INSPECTION_WHATSAPP_FLOW['version'], '7.3')
        
        # Check screens exist
        screens = SITE_INSPECTION_WHATSAPP_FLOW['screens']
        self.assertGreater(len(screens), 0)
        
        # Check screen IDs
        screen_ids = [screen['id'] for screen in screens]
        expected_screens = ['WELCOME', 'PERSONAL_INFO', 'COMPANY_INFO', 'LOCATION_INFO', 'CONTACT_INFO']
        for expected_id in expected_screens:
            self.assertIn(expected_id, screen_ids, f"Missing screen: {expected_id}")
        
        # Check final screen is terminal
        final_screen = screens[-1]
        self.assertTrue(final_screen.get('terminal', False), "Final screen should be terminal")
        self.assertTrue(final_screen.get('success', False), "Final screen should have success=True")
        
        # Check metadata
        self.assertEqual(SITE_INSPECTION_FLOW_METADATA['name'], 'site_inspection_whatsapp')
        self.assertTrue(SITE_INSPECTION_FLOW_METADATA['is_active'])
    
    def test_loan_application_flow_structure(self):
        """Test that loan application flow has correct structure"""
        # Check basic structure
        self.assertIn('version', LOAN_APPLICATION_WHATSAPP_FLOW)
        self.assertIn('screens', LOAN_APPLICATION_WHATSAPP_FLOW)
        self.assertEqual(LOAN_APPLICATION_WHATSAPP_FLOW['version'], '7.3')
        
        # Check screens exist
        screens = LOAN_APPLICATION_WHATSAPP_FLOW['screens']
        self.assertGreater(len(screens), 0)
        
        # Check screen IDs
        screen_ids = [screen['id'] for screen in screens]
        expected_screens = ['WELCOME', 'LOAN_TYPE', 'PERSONAL_INFO', 'EMPLOYMENT_INFO', 'LOAN_DETAILS']
        for expected_id in expected_screens:
            self.assertIn(expected_id, screen_ids, f"Missing screen: {expected_id}")
        
        # Check final screen is terminal
        final_screen = screens[-1]
        self.assertTrue(final_screen.get('terminal', False), "Final screen should be terminal")
        self.assertTrue(final_screen.get('success', False), "Final screen should have success=True")
        
        # Check metadata
        self.assertEqual(LOAN_APPLICATION_FLOW_METADATA['name'], 'loan_application_whatsapp')
        self.assertTrue(LOAN_APPLICATION_FLOW_METADATA['is_active'])
    
    def test_solar_cleaning_flow_data_persistence(self):
        """Test that solar cleaning flow properly carries forward data"""
        screens = SOLAR_CLEANING_WHATSAPP_FLOW['screens']
        
        # Define expected data fields
        expected_fields = [
            'full_name', 'contact_phone', 'roof_type', 'panel_type',
            'panel_count', 'preferred_date', 'availability', 'address'
        ]
        
        # Check each screen's data section includes all fields
        for screen in screens:
            if screen['id'] == 'WELCOME':
                continue  # Welcome screen can have empty defaults
            
            data_section = screen.get('data', {})
            for field in expected_fields:
                self.assertIn(
                    field, data_section,
                    f"Screen {screen['id']} missing data field: {field}"
                )
        
        # Check that navigation payloads carry forward data
        for screen in screens[:-1]:  # All except terminal screen
            layout = screen.get('layout', {})
            children = layout.get('children', [])
            
            # Find the Footer with on-click-action
            for child in children:
                if child.get('type') == 'Footer':
                    action = child.get('on-click-action', {})
                    if action.get('name') == 'navigate':
                        payload = action.get('payload', {})
                        # Payload should include all fields
                        for field in expected_fields:
                            self.assertIn(
                                field, payload,
                                f"Screen {screen['id']} navigation payload missing field: {field}"
                            )


class FlowDataFieldsTest(TestCase):
    """Test that all required data fields are present in flows"""
    
    def test_site_inspection_required_fields(self):
        """Test site inspection flow has all required fields"""
        required_fields = [
            'assessment_full_name',
            'assessment_preferred_day',
            'assessment_company_name',
            'assessment_address',
            'assessment_contact_info'
        ]
        
        screens = SITE_INSPECTION_WHATSAPP_FLOW['screens']
        final_screen = screens[-1]
        
        # Check final screen collects all data
        data_section = final_screen.get('data', {})
        for field in required_fields:
            self.assertIn(field, data_section, f"Missing required field: {field}")
    
    def test_loan_application_required_fields(self):
        """Test loan application flow has all required fields"""
        required_fields = [
            'loan_type',
            'loan_applicant_name',
            'loan_national_id',
            'loan_employment_status',
            'loan_monthly_income',
            'loan_request_amount',
            'loan_product_interest'
        ]
        
        screens = LOAN_APPLICATION_WHATSAPP_FLOW['screens']
        final_screen = screens[-1]
        
        # Check final screen collects all data
        data_section = final_screen.get('data', {})
        for field in required_fields:
            self.assertIn(field, data_section, f"Missing required field: {field}")
    
    def test_solar_cleaning_required_fields(self):
        """Test solar cleaning flow has all required fields"""
        required_fields = [
            'full_name',
            'contact_phone',
            'roof_type',
            'panel_type',
            'panel_count',
            'preferred_date',
            'availability',
            'address'
        ]
        
        screens = SOLAR_CLEANING_WHATSAPP_FLOW['screens']
        final_screen = screens[-1]
        
        # Check final screen collects all data
        data_section = final_screen.get('data', {})
        for field in required_fields:
            self.assertIn(field, data_section, f"Missing required field: {field}")


class FlowCompletionActionTest(TestCase):
    """Test that flows have proper completion actions"""
    
    def test_site_inspection_completion_has_payload(self):
        """Test that site inspection completion action includes all data"""
        screens = SITE_INSPECTION_WHATSAPP_FLOW['screens']
        final_screen = screens[-1]
        
        # Find the completion action
        layout = final_screen.get('layout', {})
        children = layout.get('children', [])
        
        completion_action = None
        for child in children:
            if child.get('type') == 'Footer':
                action = child.get('on-click-action', {})
                if action.get('name') == 'complete':
                    completion_action = action
                    break
        
        self.assertIsNotNone(completion_action, "Completion action not found")
        self.assertIn('payload', completion_action, "Completion action should have payload")
        
        # Check payload has all required fields
        payload = completion_action['payload']
        required_fields = ['assessment_full_name', 'assessment_address', 'assessment_contact_info']
        for field in required_fields:
            self.assertIn(field, payload, f"Completion payload missing field: {field}")
    
    def test_loan_application_completion_has_payload(self):
        """Test that loan application completion action includes all data"""
        screens = LOAN_APPLICATION_WHATSAPP_FLOW['screens']
        final_screen = screens[-1]
        
        # Find the completion action
        layout = final_screen.get('layout', {})
        children = layout.get('children', [])
        
        completion_action = None
        for child in children:
            if child.get('type') == 'Footer':
                action = child.get('on-click-action', {})
                if action.get('name') == 'complete':
                    completion_action = action
                    break
        
        self.assertIsNotNone(completion_action, "Completion action not found")
        self.assertIn('payload', completion_action, "Completion action should have payload")
        
        # Check payload has all required fields
        payload = completion_action['payload']
        required_fields = ['loan_type', 'loan_applicant_name', 'loan_employment_status']
        for field in required_fields:
            self.assertIn(field, payload, f"Completion payload missing field: {field}")
    
    def test_solar_cleaning_completion_has_payload(self):
        """Test that solar cleaning completion action includes all data"""
        screens = SOLAR_CLEANING_WHATSAPP_FLOW['screens']
        final_screen = screens[-1]
        
        # Find the completion action
        layout = final_screen.get('layout', {})
        children = layout.get('children', [])
        
        completion_action = None
        for child in children:
            if child.get('type') == 'Footer':
                action = child.get('on-click-action', {})
                if action.get('name') == 'complete':
                    completion_action = action
                    break
        
        self.assertIsNotNone(completion_action, "Completion action not found")
        self.assertIn('payload', completion_action, "Completion action should have payload")
        
        # Check payload has all required fields
        payload = completion_action['payload']
        required_fields = ['full_name', 'contact_phone', 'address', 'panel_count']
        for field in required_fields:
            self.assertIn(field, payload, f"Completion payload missing field: {field}")
