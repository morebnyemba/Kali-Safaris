# whatsappcrm_backend/pdfs/services.py

import os
from decimal import Decimal
from io import BytesIO
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from datetime import datetime

import logging
logger = logging.getLogger(__name__)
from customer_data.models import Payment, Booking

def _draw_pdf_footer(canvas, doc):
    """Draws a standard footer on each PDF page with company details."""
    canvas.saveState()
    
    # Get details from settings, with fallbacks
    details = getattr(settings, 'COMPANY_DETAILS', {})
    name = details.get('NAME', 'Kalai Safaris')
    address_line_1 = details.get('ADDRESS_LINE_1', '')
    address_line_2 = details.get('ADDRESS_LINE_2', '')
    phone = details.get('CONTACT_PHONE', '')
    email = details.get('CONTACT_EMAIL', '')
    website = details.get('WEBSITE', '')

    # Combine address parts that exist
    address_parts = [part for part in [address_line_1, address_line_2] if part]
    full_address = ", ".join(address_parts)

    # Combine contact parts that exist
    contact_parts = []
    if phone: contact_parts.append(f"Phone: {phone}")
    if email: contact_parts.append(f"Email: {email}")
    if website: contact_parts.append(f"Website: {website}")
    contact_line = " | ".join(contact_parts)

    canvas.setFont('Helvetica', 8)
    
    line1_text = f"{name} - {full_address}" if full_address else name
    y_position = doc.bottomMargin - 12
    canvas.drawCentredString(doc.width / 2 + doc.leftMargin, y_position, line1_text)
    canvas.drawCentredString(doc.width / 2 + doc.leftMargin, y_position - 12, contact_line)

    canvas.restoreState()

def generate_quote_pdf(quote_context: dict) -> str | None:
    """
    Generates a PDF quote from the given context and saves it to media storage.
    Returns the public URL of the generated PDF.
    """
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=36)
        
        styles = getSampleStyleSheet()
        story = []

        # Logo (optional, assuming a logo path is in settings)
        logo_path = os.path.join(settings.STATIC_ROOT, 'admin/img/kalai_safaris_logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=1*inch)
            logo.hAlign = 'LEFT'
            story.append(logo)
            story.append(Spacer(1, 0.25*inch))

        # Title and Date
        story.append(Paragraph("Safari Tour Quotation", styles['h1']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.25*inch))

        # Quote Details
        quote_id = quote_context.get('created_inquiry', {}).get('id', 'N/A')
        
        # Handle contact object properly
        contact = quote_context.get('contact', {})
        if hasattr(contact, 'name'):
            customer_name = contact.name or 'Valued Customer'
        else:
            customer_name = contact.get('name', 'Valued Customer') if isinstance(contact, dict) else 'Valued Customer'
        
        tour_name = quote_context.get('tour_name', 'N/A')
        
        # Calculate total travelers from context
        num_adults = quote_context.get('num_adults', 0)
        num_children = quote_context.get('num_children', 0)
        num_travelers = quote_context.get('num_travelers')
        if num_travelers is None:
            num_travelers = int(num_adults) + int(num_children) if num_adults or num_children else 'N/A'
        
        total_cost = quote_context.get('total_cost', 0.0)
        
        # Get dates from context
        start_date = quote_context.get('start_date', '')
        end_date = quote_context.get('end_date', '')
        inquiry_dates = quote_context.get('inquiry_dates')
        if not inquiry_dates and start_date and end_date:
            inquiry_dates = f"{start_date} to {end_date}"
        elif not inquiry_dates:
            inquiry_dates = 'N/A'
        
        story.append(Paragraph(f"<b>Quote For:</b> {customer_name}", styles['Normal']))
        story.append(Paragraph(f"<b>Quote ID:</b> Q-{quote_id}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"<b>Tour:</b> {tour_name}", styles['Normal']))
        story.append(Paragraph(f"<b>Number of Travelers:</b> {num_travelers}", styles['Normal']))
        story.append(Paragraph(f"<b>Preferred Dates:</b> {inquiry_dates}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Format total cost properly
        try:
            cost_float = float(total_cost) if total_cost else 0.0
            story.append(Paragraph(f"<b>Estimated Cost:</b> ${cost_float:,.2f}", styles['h3']))
        except (ValueError, TypeError):
            story.append(Paragraph(f"<b>Estimated Cost:</b> ${total_cost}", styles['h3']))
        
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("<i>This is a preliminary quote. A travel specialist will provide a final detailed itinerary and invoice. Prices are subject to change based on availability and final arrangements.</i>", styles['Italic']))

        doc.build(story)
        
        buffer.seek(0)
        # Save the file to the default storage (media folder)
        file_name = f"quotes/Quote_{quote_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        file_path = default_storage.save(file_name, ContentFile(buffer.read()))
        
        # Get the public URL for the saved file
        file_url = default_storage.url(file_path)
        logger.info(f"Generated PDF quote and saved to: {file_url}")
        return file_url

    except Exception as e:
        logger.error(f"Failed to generate PDF quote: {e}", exc_info=True)
        return None

def generate_receipt_pdf(payment: Payment) -> str | None:
    """
    Generates a PDF receipt for a given Payment object and saves it to media storage.
    Returns the public URL of the generated PDF.
    """
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        story = []

        # Logo
        logo_path = os.path.join(settings.STATIC_ROOT, 'admin/img/kalai_safaris_logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=1*inch)
            logo.hAlign = 'LEFT'
            story.append(logo)
            story.append(Spacer(1, 0.25*inch))

        # Title and Date
        story.append(Paragraph("Payment Receipt", styles['h1']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.25*inch))

        # Receipt Details
        booking: Booking = payment.booking
        customer_name = booking.customer.get_full_name() if booking and booking.customer else "Valued Customer"
        
        story.append(Paragraph(f"<b>Receipt For:</b> {customer_name}", styles['Normal']))
        story.append(Paragraph(f"<b>Booking Ref:</b> {booking.booking_reference if booking else 'N/A'}", styles['Normal']))
        story.append(Paragraph(f"<b>Payment Ref:</b> {payment.transaction_reference or payment.id}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        story.append(Paragraph(f"<b>Tour:</b> {booking.tour_name if booking else 'N/A'}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        # Payment Summary
        amount_paid = payment.amount or Decimal('0.00')
        total_amount = booking.total_amount or Decimal('0.00')
        balance_due = max(total_amount - (booking.get_total_paid() or Decimal('0.00')), Decimal('0.00'))

        story.append(Paragraph(f"<b>Amount Paid:</b> ${amount_paid:,.2f}", styles['h3']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"<b>Total Booking Cost:</b> ${total_amount:,.2f}", styles['Normal']))
        story.append(Paragraph(f"<b>Balance Due:</b> ${balance_due:,.2f}", styles['Normal']))
        story.append(Spacer(1, 0.5*inch))

        # Thank you Note
        story.append(Paragraph("<i>Thank you for your payment! We look forward to hosting you on your adventure. If you have any questions, please contact us.</i>", styles['Italic']))

        doc.build(story, onFirstPage=_draw_pdf_footer, onLaterPages=_draw_pdf_footer)
        
        buffer.seek(0)
        # Save the file to the default storage (media folder)
        file_name = f"receipts/Receipt_{booking.booking_reference if booking else payment.id}.pdf"
        file_path = default_storage.save(file_name, ContentFile(buffer.read()))
        
        # Get the public URL for the saved file
        file_url = default_storage.url(file_path)
        logger.info(f"Generated PDF receipt and saved to: {file_url}")
        return file_url

    except Exception as e:
        logger.error(f"Failed to generate PDF receipt for payment {payment.id}: {e}", exc_info=True)
        return None
