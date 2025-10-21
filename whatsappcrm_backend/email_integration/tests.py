from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock

from .models import EmailAttachment
from .tasks import _create_order_from_invoice_data
from customer_data.models import CustomerProfile, Order, OrderItem, Contact
from products_and_services.models import Product

class CreateOrderFromInvoiceDataTests(TestCase):

    def setUp(self):
        """Set up common objects for tests."""
        # Create a dummy file and an EmailAttachment instance
        dummy_file = SimpleUploadedFile("invoice.pdf", b"file_content", content_type="application/pdf")
        self.attachment = EmailAttachment.objects.create(
            file=dummy_file,
            filename="invoice.pdf",
            sender="testsender@example.com"
        )

        # A standard set of extracted data for a new customer and order
        self.invoice_data = {
            "invoice_number": "INV-123",
            "invoice_date": "2023-10-26",
            "total_amount": 150.00,
            "recipient": {
                "name": "John Doe",
                "phone": "+15551234567",
                "address": "123 Main St"
            },
            "line_items": [
                {
                    "product_code": "SKU-001",
                    "description": "Solar Panel 300W",
                    "quantity": 1,
                    "unit_price": 100.00,
                    "total_amount": 100.00
                },
                {
                    "product_code": "SKU-002",
                    "description": "Inverter 5kW",
                    "quantity": 1,
                    "unit_price": 50.00,
                    "total_amount": 50.00
                }
            ]
        }

    @patch('email_integration.tasks.queue_notifications_to_users')
    def test_create_order_for_new_customer(self, mock_queue_notifications):
        """Test creating a new order, customer, products, and items from scratch."""
        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")

        # 1. Verify Contact and CustomerProfile were created
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(CustomerProfile.objects.count(), 1)
        customer = CustomerProfile.objects.first()
        self.assertEqual(customer.first_name, "John")
        self.assertEqual(customer.contact.whatsapp_id, "15551234567")

        # 2. Verify Order was created
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.order_number, "INV-123")
        self.assertEqual(order.customer, customer)
        self.assertEqual(order.amount, 150.00)

        # 3. Verify Products and OrderItems were created
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(OrderItem.objects.count(), 2)
        self.assertEqual(order.items.count(), 2)
        self.assertTrue(Product.objects.filter(sku="SKU-001").exists())

        # 4. Verify notification was queued
        mock_queue_notifications.assert_called_once()

    @patch('email_integration.tasks.queue_notifications_to_users')
    def test_update_existing_order(self, mock_queue_notifications):
        """Test that an existing order is updated and its items are replaced."""
        # Pre-create an order with the same invoice number
        existing_order = Order.objects.create(order_number="INV-123", amount=99.99)
        product = Product.objects.create(name="Old Product", price=99.99)
        OrderItem.objects.create(order=existing_order, product=product, quantity=1, unit_price=99.99)

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")

        # Verify order was updated, not created
        self.assertEqual(Order.objects.count(), 1)
        updated_order = Order.objects.get(order_number="INV-123")
        self.assertEqual(updated_order.amount, 150.00)

        # Verify old items were deleted and new ones were created
        self.assertEqual(updated_order.items.count(), 2)
        self.assertFalse(updated_order.items.filter(product__name="Old Product").exists())
        self.assertTrue(updated_order.items.filter(product__sku="SKU-001").exists())
        mock_queue_notifications.assert_called_once()

    @patch('email_integration.tasks.queue_notifications_to_users')
    def test_create_order_for_existing_customer(self, mock_queue_notifications):
        """Test that a new order is created for an existing customer without creating a new profile."""
        contact = Contact.objects.create(whatsapp_id="15551234567", name="John Doe")
        CustomerProfile.objects.create(contact=contact, first_name="John", last_name="Doe")

        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(CustomerProfile.objects.count(), 1)

        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")

        # No new contact or profile should be created
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(CustomerProfile.objects.count(), 1)

        # A new order should be created and linked to the existing customer
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.first().customer.contact.whatsapp_id, "15551234567")

    @patch('email_integration.tasks.queue_notifications_to_users')
    def test_use_existing_products(self, mock_queue_notifications):
        """Test that existing products are reused instead of creating duplicates."""
        Product.objects.create(sku="SKU-001", name="Pre-existing Panel", price=99.00)
        self.assertEqual(Product.objects.count(), 1)

        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")

        # Only one new product (SKU-002) should have been created
        self.assertEqual(Product.objects.count(), 2)
        order_item = OrderItem.objects.get(product__sku="SKU-001")
        # The name should not have been updated by get_or_create defaults
        self.assertEqual(order_item.product.name, "Pre-existing Panel")

    def test_no_invoice_number(self):
        """Test that the function exits gracefully if no invoice_number is present."""
        self.invoice_data.pop('invoice_number')
        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Contact.objects.count(), 0)

    @patch('email_integration.tasks.queue_notifications_to_users')
    def test_no_customer_phone(self, mock_queue_notifications):
        """Test that an order is created without a customer if the phone is missing."""
        self.invoice_data['recipient'].pop('phone')
        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")

        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertIsNone(order.customer)

        # Notification should not be sent if there's no customer profile
        mock_queue_notifications.assert_not_called()
