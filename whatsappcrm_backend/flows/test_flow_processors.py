"""
Tests for WhatsApp Flow Response Processors.
Validates that backend handlers correctly process flow submissions.
"""

from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from flows.models import WhatsAppFlow, WhatsAppFlowResponse
from flows.whatsapp_flow_response_processor import WhatsAppFlowResponseProcessor
from conversations.models import Contact
from customer_data.models import (
    CustomerProfile, Booking, TourInquiry
)
from meta_integration.models import MetaAppConfig


