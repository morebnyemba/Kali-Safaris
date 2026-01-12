"""
Unit tests for WhatsApp Flow JSON validation.
Ensures all flow definitions meet WhatsApp Flow API v7.3 requirements.
"""
from django.test import TestCase
from flows.definitions.traveler_details_whatsapp_flow import (
    TRAVELER_DETAILS_WHATSAPP_FLOW,
    TRAVELER_DETAILS_WHATSAPP_FLOW_METADATA
)
from flows.definitions.tour_inquiry_whatsapp_flow import (
    TOUR_INQUIRY_WHATSAPP_FLOW,
    TOUR_INQUIRY_WHATSAPP_FLOW_METADATA
)
from flows.definitions.date_picker_whatsapp_flow import (
    DATE_PICKER_WHATSAPP_FLOW,
    DATE_PICKER_WHATSAPP_FLOW_METADATA
)
import json


class WhatsAppFlowJSONValidationTest(TestCase):
    """Test WhatsApp Flow JSON definitions for API compliance"""
    
    def validate_photopicker(self, component, screen_id, flow_name):
        """Validate PhotoPicker component against WhatsApp Flow API v7.3 requirements."""
        # Check required properties exist
        self.assertIn(
            'min-uploaded-photos', 
            component,
            f"PhotoPicker in {flow_name}/{screen_id} missing 'min-uploaded-photos'"
        )
        self.assertIn(
            'max-uploaded-photos', 
            component,
            f"PhotoPicker in {flow_name}/{screen_id} missing 'max-uploaded-photos'"
        )
        
        # Validate value types and ranges
        min_photos = component['min-uploaded-photos']
        max_photos = component['max-uploaded-photos']
        
        self.assertIsInstance(
            min_photos, 
            int,
            f"PhotoPicker in {flow_name}/{screen_id}: 'min-uploaded-photos' must be an integer"
        )
        self.assertIsInstance(
            max_photos, 
            int,
            f"PhotoPicker in {flow_name}/{screen_id}: 'max-uploaded-photos' must be an integer"
        )
        
        # Check range constraints (0-30 for min, 1-30 for max)
        self.assertGreaterEqual(
            min_photos, 
            0,
            f"PhotoPicker in {flow_name}/{screen_id}: 'min-uploaded-photos' must be >= 0"
        )
        self.assertLessEqual(
            min_photos, 
            30,
            f"PhotoPicker in {flow_name}/{screen_id}: 'min-uploaded-photos' must be <= 30"
        )
        self.assertGreaterEqual(
            max_photos, 
            1,
            f"PhotoPicker in {flow_name}/{screen_id}: 'max-uploaded-photos' must be >= 1"
        )
        self.assertLessEqual(
            max_photos, 
            30,
            f"PhotoPicker in {flow_name}/{screen_id}: 'max-uploaded-photos' must be <= 30"
        )
        
        # Check logical constraint: min <= max
        self.assertLessEqual(
            min_photos,
            max_photos,
            f"PhotoPicker in {flow_name}/{screen_id}: 'min-uploaded-photos' "
            f"({min_photos}) must be <= 'max-uploaded-photos' ({max_photos})"
        )
    
    def validate_flow_json(self, flow_json, flow_name):
        """Validate a WhatsApp Flow JSON definition."""
        # Check version exists
        self.assertIn('version', flow_json, f"{flow_name} missing 'version'")
        
        # Check screens exist
        self.assertIn('screens', flow_json, f"{flow_name} missing 'screens'")
        screens = flow_json['screens']
        self.assertGreater(len(screens), 0, f"{flow_name} has no screens")
        
        # Validate each screen
        for screen in screens:
            screen_id = screen.get('id', 'UNKNOWN')
            layout = screen.get('layout', {})
            children = layout.get('children', [])
            
            # Check for PhotoPicker components
            for child in children:
                if child.get('type') == 'PhotoPicker':
                    self.validate_photopicker(child, screen_id, flow_name)
        
        # Ensure JSON is serializable
        try:
            json.dumps(flow_json)
        except Exception as e:
            self.fail(f"{flow_name} JSON serialization failed: {e}")
    
    def test_traveler_details_flow_json(self):
        """Test Traveler Details WhatsApp Flow JSON validation"""
        self.validate_flow_json(
            TRAVELER_DETAILS_WHATSAPP_FLOW,
            "Traveler Details WhatsApp Flow"
        )
    
    def test_tour_inquiry_flow_json(self):
        """Test Tour Inquiry WhatsApp Flow JSON validation"""
        self.validate_flow_json(
            TOUR_INQUIRY_WHATSAPP_FLOW,
            "Tour Inquiry WhatsApp Flow"
        )
    
    def test_date_picker_flow_json(self):
        """Test Date Picker WhatsApp Flow JSON validation"""
        self.validate_flow_json(
            DATE_PICKER_WHATSAPP_FLOW,
            "Date Picker WhatsApp Flow"
        )
    
    def test_traveler_details_photopicker_properties(self):
        """Test that Traveler Details PhotoPicker has required properties"""
        # Find the PhotoPicker in the ID_DOCUMENT_UPLOAD screen
        flow_json = TRAVELER_DETAILS_WHATSAPP_FLOW
        photopicker_found = False
        
        for screen in flow_json['screens']:
            if screen['id'] == 'ID_DOCUMENT_UPLOAD':
                for child in screen['layout']['children']:
                    if child.get('type') == 'PhotoPicker':
                        photopicker_found = True
                        # Verify specific properties
                        self.assertEqual(
                            child['name'], 
                            'id_document_photo',
                            "PhotoPicker name should be 'id_document_photo'"
                        )
                        self.assertEqual(
                            child['min-uploaded-photos'],
                            1,
                            "PhotoPicker should require at least 1 photo"
                        )
                        self.assertEqual(
                            child['max-uploaded-photos'],
                            1,
                            "PhotoPicker should allow maximum 1 photo"
                        )
                        self.assertTrue(
                            child.get('required', False),
                            "PhotoPicker should be required"
                        )
        
        self.assertTrue(
            photopicker_found,
            "PhotoPicker not found in ID_DOCUMENT_UPLOAD screen"
        )
