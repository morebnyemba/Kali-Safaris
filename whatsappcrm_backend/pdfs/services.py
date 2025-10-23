# whatsappcrm_backend/pdfs/services.py

import os
from io import BytesIO
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

def generate_quote_pdf(quote_context: dict) -> str | None:
    """
    Generates a PDF quote from the given context and saves it to media storage.
    Returns the public URL of the generated PDF.
    """
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
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
        customer_name = quote_context.get('contact', {}).name or 'Valued Customer'
        tour_name = quote_context.get('tour_name', 'N/A')
        num_travelers = quote_context.get('num_travelers', 'N/A')
        total_cost = quote_context.get('total_cost', 0.0)
        inquiry_dates = quote_context.get('inquiry_dates', 'N/A')
        
        story.append(Paragraph(f"<b>Quote For:</b> {customer_name}", styles['Normal']))
        story.append(Paragraph(f"<b>Quote ID:</b> Q-{quote_id}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"<b>Tour:</b> {tour_name}", styles['Normal']))
        story.append(Paragraph(f"<b>Number of Travelers:</b> {num_travelers}", styles['Normal']))
        story.append(Paragraph(f"<b>Preferred Dates:</b> {inquiry_dates}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"<b>Estimated Cost:</b> ${total_cost:,.2f}", styles['h3']))
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
