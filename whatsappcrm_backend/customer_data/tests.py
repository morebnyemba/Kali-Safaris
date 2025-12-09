from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .reference_generator import generate_booking_reference, generate_inquiry_reference
from .models import Booking, TourInquiry, CustomerProfile
from conversations.models import Contact


class ReferenceGeneratorTestCase(TestCase):
    """Test cases for reference ID generation"""
    
    def test_booking_reference_format(self):
        """Test that booking reference has correct format: BK followed by 8 digits"""
        ref = generate_booking_reference()
        self.assertIsNotNone(ref)
        self.assertTrue(ref.startswith('BK'))
        self.assertEqual(len(ref), 10)  # BK + 8 digits
        # Check that the last 8 characters are all digits
        self.assertTrue(ref[2:].isdigit())
    
    def test_inquiry_reference_format(self):
        """Test that inquiry reference has correct format: TQ followed by 8 digits"""
        ref = generate_inquiry_reference()
        self.assertIsNotNone(ref)
        self.assertTrue(ref.startswith('TQ'))
        self.assertEqual(len(ref), 10)  # TQ + 8 digits
        # Check that the last 8 characters are all digits
        self.assertTrue(ref[2:].isdigit())
    
    def test_booking_reference_uniqueness(self):
        """Test that multiple generated references are different"""
        refs = set()
        for _ in range(100):
            ref = generate_booking_reference()
            refs.add(ref)
        # Should have 100 unique references (though there's a tiny chance of collision)
        self.assertGreater(len(refs), 95)  # Allow for rare collisions
    
    def test_inquiry_reference_uniqueness(self):
        """Test that multiple generated inquiry references are different"""
        refs = set()
        for _ in range(100):
            ref = generate_inquiry_reference()
            refs.add(ref)
        # Should have 100 unique references (though there's a tiny chance of collision)
        self.assertGreater(len(refs), 95)  # Allow for rare collisions


class BookingReferenceAutoGenerationTestCase(TestCase):
    """Test cases for automatic booking reference generation"""
    
    def setUp(self):
        """Set up test data"""
        # Create a contact
        self.contact = Contact.objects.create(
            whatsapp_id="+263771234567",
            name="Test User"
        )
        # Create a customer profile
        self.customer_profile = CustomerProfile.objects.create(
            contact=self.contact,
            first_name="Test",
            last_name="User"
        )
    
    def test_booking_auto_generates_reference(self):
        """Test that booking reference is auto-generated when not provided"""
        booking = Booking.objects.create(
            customer=self.customer_profile,
            tour_name="Test Safari",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=3),
            number_of_adults=2,
            total_amount=1000.00
        )
        
        # Check that booking_reference was auto-generated
        self.assertIsNotNone(booking.booking_reference)
        self.assertTrue(booking.booking_reference.startswith('BK'))
        self.assertEqual(len(booking.booking_reference), 10)
    
    def test_booking_respects_provided_reference(self):
        """Test that provided booking reference is not overwritten"""
        custom_ref = "CUSTOM-REF-123"
        booking = Booking.objects.create(
            customer=self.customer_profile,
            booking_reference=custom_ref,
            tour_name="Test Safari",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=3),
            number_of_adults=2,
            total_amount=1000.00
        )
        
        # Check that the custom reference was preserved
        self.assertEqual(booking.booking_reference, custom_ref)


class TourInquiryReferenceAutoGenerationTestCase(TestCase):
    """Test cases for automatic tour inquiry reference generation"""
    
    def setUp(self):
        """Set up test data"""
        # Create a contact
        self.contact = Contact.objects.create(
            whatsapp_id="+263771234567",
            name="Test User"
        )
        # Create a customer profile
        self.customer_profile = CustomerProfile.objects.create(
            contact=self.contact,
            first_name="Test",
            last_name="User"
        )
    
    def test_inquiry_auto_generates_reference(self):
        """Test that inquiry reference is auto-generated when not provided"""
        inquiry = TourInquiry.objects.create(
            customer=self.customer_profile,
            destinations="Victoria Falls",
            number_of_travelers=4
        )
        
        # Check that inquiry_reference was auto-generated
        self.assertIsNotNone(inquiry.inquiry_reference)
        self.assertTrue(inquiry.inquiry_reference.startswith('TQ'))
        self.assertEqual(len(inquiry.inquiry_reference), 10)
    
    def test_inquiry_respects_provided_reference(self):
        """Test that provided inquiry reference is not overwritten"""
        custom_ref = "CUSTOM-INQ-456"
        inquiry = TourInquiry.objects.create(
            customer=self.customer_profile,
            inquiry_reference=custom_ref,
            destinations="Victoria Falls",
            number_of_travelers=4
        )
        
        # Check that the custom reference was preserved
        self.assertEqual(inquiry.inquiry_reference, custom_ref)
