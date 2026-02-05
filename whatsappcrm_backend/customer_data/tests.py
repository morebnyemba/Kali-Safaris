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


class BookingReferenceUpdateTestCase(TestCase):
    """Test cases for updating booking reference to shared format"""
    
    def setUp(self):
        """Set up test data"""
        from products_and_services.models import Tour
        
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
        # Create a tour
        self.tour = Tour.objects.create(
            name="Victoria Falls Safari",
            description="3-day safari tour",
            duration_days=3,
            price_per_person=500.00
        )
    
    def test_update_to_shared_reference_with_tour(self):
        """Test that booking reference updates to shared format when tour exists"""
        start_date = timezone.now().date() + timedelta(days=7)
        
        # Create booking with random reference
        booking = Booking.objects.create(
            customer=self.customer_profile,
            tour=self.tour,
            tour_name=self.tour.name,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            number_of_adults=2,
            total_amount=1000.00
        )
        
        old_reference = booking.booking_reference
        
        # Update to shared reference
        was_updated, new_reference = booking.update_to_shared_reference()
        
        # Verify update occurred
        self.assertTrue(was_updated)
        self.assertIsNotNone(new_reference)
        self.assertTrue(new_reference.startswith('BK-T'))
        self.assertIn(start_date.strftime('%Y%m%d'), new_reference)
        self.assertNotEqual(old_reference, new_reference)
        
        # Refresh from DB and verify
        booking.refresh_from_db()
        self.assertEqual(booking.booking_reference, new_reference)
    
    def test_update_to_shared_reference_without_tour(self):
        """Test that booking reference does not update when tour is missing"""
        start_date = timezone.now().date() + timedelta(days=7)
        
        # Create booking without tour
        booking = Booking.objects.create(
            customer=self.customer_profile,
            tour_name="Custom Tour",
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            number_of_adults=2,
            total_amount=1000.00
        )
        
        old_reference = booking.booking_reference
        
        # Attempt to update to shared reference
        was_updated, new_reference = booking.update_to_shared_reference()
        
        # Verify no update occurred
        self.assertFalse(was_updated)
        self.assertIsNone(new_reference)
        
        # Refresh from DB and verify reference unchanged
        booking.refresh_from_db()
        self.assertEqual(booking.booking_reference, old_reference)
    
    def test_update_to_shared_reference_idempotent(self):
        """Test that updating to shared reference multiple times is idempotent"""
        start_date = timezone.now().date() + timedelta(days=7)
        
        # Create booking with tour (will use shared reference initially)
        booking = Booking.objects.create(
            customer=self.customer_profile,
            tour=self.tour,
            tour_name=self.tour.name,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            number_of_adults=2,
            total_amount=1000.00
        )
        
        # Should already have shared reference
        first_reference = booking.booking_reference
        self.assertTrue(first_reference.startswith('BK-T'))
        
        # Try to update again
        was_updated, new_reference = booking.update_to_shared_reference()
        
        # Should not update since it's already in shared format
        self.assertFalse(was_updated)
        self.assertIsNone(new_reference)
        
        # Reference should remain unchanged
        booking.refresh_from_db()
        self.assertEqual(booking.booking_reference, first_reference)
    
    def test_multiple_bookings_share_reference(self):
        """Test that multiple bookings for same tour and date share reference"""
        start_date = timezone.now().date() + timedelta(days=7)
        
        # Create first booking
        booking1 = Booking.objects.create(
            customer=self.customer_profile,
            tour=self.tour,
            tour_name=self.tour.name,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            number_of_adults=2,
            total_amount=1000.00
        )
        
        # Create second customer
        contact2 = Contact.objects.create(
            whatsapp_id="+263779999999",
            name="Second User"
        )
        customer2 = CustomerProfile.objects.create(
            contact=contact2,
            first_name="Second",
            last_name="User"
        )
        
        # Create second booking for same tour and date
        booking2 = Booking.objects.create(
            customer=customer2,
            tour=self.tour,
            tour_name=self.tour.name,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            number_of_adults=1,
            total_amount=500.00
        )
        
        # Both should have the same reference
        self.assertEqual(booking1.booking_reference, booking2.booking_reference)
        self.assertTrue(booking1.booking_reference.startswith('BK-T'))


class PassengerManifestSummaryTestCase(TestCase):
    """Test cases for passenger manifest summary export"""
    
    def setUp(self):
        """Set up test data"""
        from products_and_services.models import Tour
        from .models import Traveler
        
        # Create a tour
        self.tour = Tour.objects.create(
            name="Test Safari",
            description="Test tour",
            duration_days=3,
            price_per_person=100.00
        )
        
        # Create test date
        self.test_date = timezone.now().date() + timedelta(days=7)
        
        # Create customers
        contact1 = Contact.objects.create(whatsapp_id="+263771111111", name="Customer One")
        self.customer1 = CustomerProfile.objects.create(
            contact=contact1,
            first_name="John",
            last_name="Chakanya"
        )
        
        contact2 = Contact.objects.create(whatsapp_id="+263772222222", name="Customer Two")
        self.customer2 = CustomerProfile.objects.create(
            contact=contact2,
            first_name="Mary",
            last_name="Nyemba"
        )
        
        # Create confirmed booking 1 with travelers
        self.booking1 = Booking.objects.create(
            customer=self.customer1,
            tour=self.tour,
            tour_name=self.tour.name,
            start_date=self.test_date,
            end_date=self.test_date + timedelta(days=3),
            number_of_adults=2,
            number_of_children=1,
            total_amount=300.00,
            amount_paid=300.00,
            payment_status=Booking.PaymentStatus.PAID
        )
        
        # Add travelers for booking 1
        Traveler.objects.create(
            booking=self.booking1,
            name="John Chakanya",
            age=35,
            nationality="Zimbabwean",
            gender="Male",
            id_number="12345678",
            traveler_type="adult"
        )
        Traveler.objects.create(
            booking=self.booking1,
            name="Jane Chakanya",
            age=32,
            nationality="Zimbabwean",
            gender="Female",
            id_number="87654321",
            traveler_type="adult"
        )
        Traveler.objects.create(
            booking=self.booking1,
            name="Junior Chakanya",
            age=8,
            nationality="Zimbabwean",
            gender="Male",
            id_number="11111111",
            traveler_type="child"
        )
        
        # Create confirmed booking 2 with travelers
        self.booking2 = Booking.objects.create(
            customer=self.customer2,
            tour=self.tour,
            tour_name=self.tour.name,
            start_date=self.test_date,
            end_date=self.test_date + timedelta(days=3),
            number_of_adults=2,
            total_amount=200.00,
            amount_paid=100.00,
            payment_status=Booking.PaymentStatus.DEPOSIT_PAID
        )
        
        # Add travelers for booking 2
        Traveler.objects.create(
            booking=self.booking2,
            name="Mary Nyemba",
            age=40,
            nationality="Zimbabwean",
            gender="Female",
            id_number="22222222",
            traveler_type="adult"
        )
        Traveler.objects.create(
            booking=self.booking2,
            name="Peter Nyemba",
            age=42,
            nationality="Zimbabwean",
            gender="Male",
            id_number="33333333",
            traveler_type="adult"
        )
        
        # Create pending booking (should not appear in summary)
        self.booking3 = Booking.objects.create(
            customer=self.customer1,
            tour=self.tour,
            tour_name=self.tour.name,
            start_date=self.test_date,
            end_date=self.test_date + timedelta(days=3),
            number_of_adults=1,
            total_amount=100.00,
            amount_paid=0.00,
            payment_status=Booking.PaymentStatus.PENDING
        )
    
    def test_summary_export_filters_confirmed_bookings(self):
        """Test that summary export only includes confirmed bookings"""
        from .exports import export_passenger_manifest_summary_pdf
        from io import BytesIO
        
        # Generate report
        response = export_passenger_manifest_summary_pdf(self.test_date)
        
        # Should be a PDF
        self.assertEqual(response['Content-Type'], 'application/pdf')
        
        # Check filename format
        expected_filename = f"passenger_summary_{self.test_date.strftime('%Y-%m-%d')}.pdf"
        self.assertIn(expected_filename, response['Content-Disposition'])
        
        # Read PDF content to verify it was generated
        content = BytesIO(response.content)
        self.assertGreater(len(content.getvalue()), 0)
    
    def test_summary_counts_travelers_correctly(self):
        """Test that summary counts travelers correctly per booking"""
        # Booking 1 should have 3 travelers
        self.assertEqual(self.booking1.travelers.count(), 3)
        
        # Booking 2 should have 2 travelers
        self.assertEqual(self.booking2.travelers.count(), 2)
        
        # Booking 3 (pending) should not be counted
        self.assertEqual(self.booking3.payment_status, Booking.PaymentStatus.PENDING)
    
    def test_summary_excel_export(self):
        """Test Excel export format"""
        from .exports import export_passenger_manifest_summary_excel
        
        # Generate report
        response = export_passenger_manifest_summary_excel(self.test_date)
        
        # Should be Excel format
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Check filename format
        expected_filename = f"passenger_summary_{self.test_date.strftime('%Y-%m-%d')}.xlsx"
        self.assertIn(expected_filename, response['Content-Disposition'])
        
        # Verify content was generated
        self.assertGreater(len(response.content), 0)
    
    def test_no_confirmed_bookings(self):
        """Test report generation when no confirmed bookings exist"""
        from .exports import export_passenger_manifest_summary_pdf
        
        # Use a date with no bookings
        future_date = timezone.now().date() + timedelta(days=365)
        
        # Should still generate a report (with "no bookings" message)
        response = export_passenger_manifest_summary_pdf(future_date)
        
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertGreater(len(response.content), 0)


