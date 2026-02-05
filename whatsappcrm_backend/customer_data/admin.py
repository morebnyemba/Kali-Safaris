from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import csv
import zipfile
import os
from django.conf import settings
from .models import CustomerProfile, Interaction, Booking, Payment, TourInquiry, Traveler

class InteractionInline(admin.TabularInline):
    """
    Inline admin for displaying recent interactions directly on the CustomerProfile page.
    This provides immediate context about recent activities.
    """
    model = Interaction
    extra = 0  # Don't show extra empty forms for new interactions
    fields = ('created_at', 'interaction_type', 'agent', 'notes_preview')
    readonly_fields = ('created_at', 'interaction_type', 'agent', 'notes_preview')
    show_change_link = True  # Allow clicking to the full interaction change form
    ordering = ('-created_at',)
    verbose_name_plural = 'Recent Interactions'

    def notes_preview(self, obj):
        """Provides a truncated preview of the interaction notes."""
        if obj.notes:
            return (obj.notes[:75] + '...') if len(obj.notes) > 75 else obj.notes
        return "No notes."
    notes_preview.short_description = "Notes Preview"

    def has_add_permission(self, request, obj=None):
        # Interactions should be added via the API or main Interaction admin, not inline.
        return False

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the CustomerProfile model.
    """
    list_display = ('__str__', 'lead_status', 'company', 'assigned_agent', 'last_interaction_date')
    list_filter = ('lead_status', 'assigned_agent', 'country', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'company', 'contact__whatsapp_id', 'contact__name')
    readonly_fields = ('contact', 'created_at', 'updated_at', 'last_interaction_date')
    inlines = [InteractionInline]
    list_per_page = 25
    list_select_related = ('contact', 'assigned_agent') # Performance optimization

    fieldsets = (
        ('Primary Info', {
            'fields': ('contact', ('first_name', 'last_name'), 'email')
        }),
        ('Company & Role', {
            'fields': ('company', 'role')
        }),
        ('Sales Pipeline', {
            'fields': ('lead_status', 'potential_value', 'acquisition_source', 'assigned_agent')
        }),
        ('Location', {
            'fields': (('city', 'state_province'), ('postal_code', 'country')),
            'classes': ('collapse',) # Collapsible section
        }),
        ('Segmentation & Notes', {
            'fields': ('tags', 'notes', 'custom_attributes')
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_interaction_date'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    """
    Admin interface for the Interaction model.
    """
    list_display = ('__str__', 'customer', 'agent', 'interaction_type', 'created_at')
    list_filter = ('interaction_type', 'agent', 'created_at')
    search_fields = ('notes', 'customer__first_name', 'customer__last_name', 'customer__contact__whatsapp_id')
    readonly_fields = ('created_at',)
    list_per_page = 30
    list_select_related = ('customer', 'agent', 'customer__contact') # Performance optimization
    autocomplete_fields = ['customer', 'agent'] # Use a search-friendly widget for foreign keys

    fieldsets = (
        (None, {
            'fields': ('customer', 'agent', 'interaction_type')
        }),
        ('Details', {
            'fields': ('notes', 'created_at')
        }),
    )

class TravelerInline(admin.TabularInline):
    """
    Inline admin for displaying travelers associated with a booking.
    """
    model = Traveler
    extra = 0
    fields = ('name', 'age', 'nationality', 'gender', 'id_number', 'id_document', 'traveler_type', 'medical_dietary_requirements')
    readonly_fields = ('created_at',)
    show_change_link = True

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin interface for the Booking model.
    """
    list_display = ('booking_reference', 'customer', 'tour_name', 'start_date', 'payment_status', 'total_amount', 'assigned_agent', 'get_traveler_count')
    list_filter = ('payment_status', 'source', 'start_date', 'assigned_agent')
    search_fields = ('booking_reference', 'tour_name', 'customer__first_name', 'customer__last_name', 'customer__contact__whatsapp_id')
    autocomplete_fields = ['customer', 'tour', 'assigned_agent']
    list_editable = ('payment_status',)
    date_hierarchy = 'start_date'
    inlines = [TravelerInline]
    actions = ['export_booking_travelers_pdf', 'export_booking_travelers_excel', 'export_manifest_for_date', 'export_passenger_summary_for_date', 'download_all_id_documents']
    fieldsets = (
        ('Booking Core Info', {
            'fields': ('booking_reference', 'customer', 'tour', 'tour_name', 'assigned_agent')
        }),
        ('Dates & Guests', {
            'fields': (('start_date', 'end_date'), ('number_of_adults', 'number_of_children'))
        }),
        ('Financials & Source', {
            'fields': (('total_amount', 'amount_paid'), 'payment_status', 'source')
        }),
        ('Additional Details', {
            'fields': ('notes', 'booking_details_payload'),
            'classes': ('collapse',)
        }),
    )
    list_select_related = ('customer', 'tour', 'assigned_agent')
    
    def get_traveler_count(self, obj):
        """Display the number of travelers for this booking."""
        return obj.travelers.count()
    get_traveler_count.short_description = 'Travelers'
    
    def export_booking_travelers_pdf(self, request, queryset):
        """Export travelers from selected bookings to PDF."""
        # Get all travelers from selected bookings
        travelers = Traveler.objects.filter(booking__in=queryset).select_related('booking')
        
        # Create the HttpResponse object with PDF headers
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="booking_travelers_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        # Create the PDF object using ReportLab
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>Traveler Manifest</b><br/>Generated: {timezone.now().strftime('%B %d, %Y at %H:%M')}<br/>Total Bookings: {queryset.count()} | Total Travelers: {travelers.count()}", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Prepare data for table
        data = [['Name', 'Booking Ref', 'Tour', 'Tour Date', 'Type', 'Age', 'Nationality', 'Gender', 'ID Number']]
        
        for traveler in travelers:
            start_date = traveler.booking.start_date.strftime('%Y-%m-%d') if traveler.booking and traveler.booking.start_date else 'N/A'
            
            data.append([
                traveler.name,
                traveler.booking.booking_reference if traveler.booking else 'N/A',
                traveler.booking.tour_name if traveler.booking else 'N/A',
                start_date,
                traveler.get_traveler_type_display(),
                str(traveler.age),
                traveler.nationality,
                traveler.gender,
                traveler.id_number
            ])
        
        # Create table
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF from buffer and write to response
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        self.message_user(request, f"Successfully exported {travelers.count()} traveler(s) from {queryset.count()} booking(s) to PDF.")
        return response
    
    export_booking_travelers_pdf.short_description = "Export travelers from selected bookings to PDF"
    
    def export_booking_travelers_excel(self, request, queryset):
        """Export travelers from selected bookings to CSV (Excel-compatible)."""
        # Get all travelers from selected bookings
        travelers = Traveler.objects.filter(booking__in=queryset).select_related('booking', 'booking__customer')
        
        # Create the HttpResponse object with CSV headers
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="booking_travelers_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow([
            'Name', 'Booking Reference', 'Tour Name', 'Tour Start Date', 'Tour End Date',
            'Traveler Type', 'Age', 'Nationality', 'Gender', 'ID/Passport Number',
            'Medical/Dietary Requirements', 'Booking Status', 'Total Amount', 'Customer Name', 'Customer Email'
        ])
        
        # Write data rows
        for traveler in travelers:
            # Safely access booking and customer data
            if traveler.booking:
                customer_name = traveler.booking.customer.get_full_name() if traveler.booking.customer else 'N/A'
                customer_email = traveler.booking.customer.email if traveler.booking.customer else 'N/A'
                start_date = traveler.booking.start_date.strftime('%Y-%m-%d') if traveler.booking.start_date else 'N/A'
                end_date = traveler.booking.end_date.strftime('%Y-%m-%d') if traveler.booking.end_date else 'N/A'
                booking_ref = traveler.booking.booking_reference
                tour_name = traveler.booking.tour_name
                payment_status = traveler.booking.get_payment_status_display()
                total_amount = traveler.booking.total_amount
            else:
                customer_name = 'N/A'
                customer_email = 'N/A'
                start_date = 'N/A'
                end_date = 'N/A'
                booking_ref = 'N/A'
                tour_name = 'N/A'
                payment_status = 'N/A'
                total_amount = 'N/A'
            
            writer.writerow([
                traveler.name,
                booking_ref,
                tour_name,
                start_date,
                end_date,
                traveler.get_traveler_type_display(),
                traveler.age,
                traveler.nationality,
                traveler.gender,
                traveler.id_number,
                traveler.medical_dietary_requirements or 'None',
                payment_status,
                total_amount,
                customer_name,
                customer_email
            ])
        
        self.message_user(request, f"Successfully exported {travelers.count()} traveler(s) from {queryset.count()} booking(s) to CSV/Excel.")
        return response
    
    export_booking_travelers_excel.short_description = "Export travelers from selected bookings to CSV/Excel"
    
    def export_manifest_for_date(self, request, queryset):
        """
        Export a ZimParks-compliant manifest for bookings on a specific date.
        Uses the first booking's start_date from the selected queryset.
        """
        from .exports import export_booking_manifest_pdf
        
        if not queryset.exists():
            self.message_user(request, "No bookings selected.", level='warning')
            return
        
        # Use the start_date from the first booking in the queryset
        booking_date = queryset.first().start_date
        
        # Filter all bookings for that date (not just selected ones)
        self.message_user(
            request, 
            f"Generating manifest for {booking_date.strftime('%B %d, %Y')} (all bookings on that date)...",
            level='info'
        )
        
        return export_booking_manifest_pdf(booking_date)
    
    export_manifest_for_date.short_description = "Export Manifest for Booking Date (ZimParks Format)"
    
    def export_passenger_summary_for_date(self, request, queryset):
        """
        Export an operational passenger summary for bookings on a specific date.
        Shows headcount per booking group for crew planning and park fees.
        """
        from .exports import export_passenger_manifest_summary_pdf
        
        if not queryset.exists():
            self.message_user(request, "No bookings selected.", level='warning')
            return
        
        # Use the start_date from the first booking in the queryset
        booking_date = queryset.first().start_date
        
        # Filter to confirmed bookings for that date
        confirmed_count = Booking.objects.filter(
            start_date=booking_date,
            payment_status__in=[Booking.PaymentStatus.PAID, Booking.PaymentStatus.DEPOSIT_PAID]
        ).count()
        
        self.message_user(
            request,
            f"Generating passenger summary for {booking_date.strftime('%B %d, %Y')} ({confirmed_count} confirmed booking(s))...",
            level='info'
        )
        
        return export_passenger_manifest_summary_pdf(booking_date)
    
    export_passenger_summary_for_date.short_description = "Export Passenger Summary (Operational - Headcount)"
    
    def download_all_id_documents(self, request, queryset):
        """
        Download all ID documents for travelers in selected bookings as a ZIP file.
        Organizes documents by booking reference for easy submission to ZimParks.
        """
        # Get all travelers with ID documents from selected bookings
        travelers = Traveler.objects.filter(
            booking__in=queryset
        ).exclude(
            id_document=''
        ).select_related('booking')
        
        if not travelers.exists():
            self.message_user(request, "No travelers with ID documents found in selected bookings.", level='warning')
            return
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Group travelers by booking for organization
            bookings_dict = {}
            for traveler in travelers:
                booking_ref = traveler.booking.booking_reference
                if booking_ref not in bookings_dict:
                    bookings_dict[booking_ref] = []
                bookings_dict[booking_ref].append(traveler)
            
            # Add each ID document to ZIP
            for booking_ref, booking_travelers in bookings_dict.items():
                for idx, traveler in enumerate(booking_travelers, 1):
                    try:
                        # Read the file content
                        id_doc_path = traveler.id_document.path
                        if os.path.exists(id_doc_path):
                            # Get file extension
                            file_ext = os.path.splitext(id_doc_path)[1]
                            # Create a clean filename: BookingRef/TravelerName_ID.ext
                            safe_name = traveler.name.replace(' ', '_').replace('/', '_')
                            filename = f"{booking_ref}/{idx}_{safe_name}{file_ext}"
                            
                            # Add to ZIP
                            with open(id_doc_path, 'rb') as f:
                                zip_file.writestr(filename, f.read())
                    except Exception as e:
                        # Log error but continue with other documents
                        self.message_user(
                            request, 
                            f"Could not add ID document for {traveler.name}: {str(e)}", 
                            level='warning'
                        )
        
        # Prepare HTTP response
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="id_documents_{timezone.now().strftime("%Y%m%d_%H%M%S")}.zip"'
        
        # Count documents
        total_travelers = travelers.count()
        booking_count = queryset.count()
        
        self.message_user(
            request,
            f"✅ Successfully downloaded {total_travelers} ID document(s) from {booking_count} booking(s).",
            level='success'
        )
        
        return response
    
    download_all_id_documents.short_description = "📥 Download All ID Documents (ZIP)"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('id', 'booking__booking_reference', 'transaction_reference')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['booking']
    actions = ['approve_payments', 'reject_payments']
    
    def approve_payments(self, request, queryset):
        """
        Approve selected payments, update booking references, and notify customers.
        """
        from django.db import transaction
        from meta_integration.utils import send_whatsapp_message
        
        approved_count = 0
        error_count = 0
        
        for payment in queryset.filter(status=Payment.PaymentStatus.PENDING):
            try:
                with transaction.atomic():
                    # Update payment status
                    payment.status = Payment.PaymentStatus.SUCCESSFUL
                    payment.notes = (payment.notes or '') + f"\n[Approved by {request.user.username} on {timezone.now().strftime('%Y-%m-%d %H:%M')}]"
                    payment.save()
                    
                    # Update booking reference to shared format if applicable
                    if payment.booking:
                        booking = payment.booking
                        
                        # Lock the booking for update
                        booking = Booking.objects.select_for_update().get(pk=booking.pk)
                        
                        # Update booking reference to shared format
                        old_reference = booking.booking_reference
                        was_updated, new_reference = booking.update_to_shared_reference(commit=False)
                        
                        # Update payment status based on amount paid
                        if booking.amount_paid >= booking.total_amount:
                            booking.payment_status = Booking.PaymentStatus.PAID
                        elif booking.amount_paid > 0:
                            booking.payment_status = Booking.PaymentStatus.DEPOSIT_PAID
                        
                        # Save booking with all updates
                        if was_updated:
                            booking.save(update_fields=['payment_status', 'booking_reference', 'updated_at'])
                            self.message_user(
                                request,
                                f"Updated booking reference: {old_reference} → {new_reference}",
                                level='info'
                            )
                        else:
                            booking.save(update_fields=['payment_status', 'updated_at'])
                        
                        # Send confirmation to customer via WhatsApp
                        if booking.customer and booking.customer.contact:
                            try:
                                message_body = (
                                    f"✅ *Payment Approved!*\n\n"
                                    f"Your payment of ${payment.amount:.2f} for booking *{booking.booking_reference}* has been approved.\n\n"
                                    f"Tour: {booking.tour_name}\n"
                                    f"Date: {booking.start_date.strftime('%B %d, %Y')}\n"
                                    f"Amount Paid: ${booking.amount_paid:.2f}\n"
                                    f"Total: ${booking.total_amount:.2f}\n"
                                )
                                
                                if booking.payment_status == Booking.PaymentStatus.PAID:
                                    message_body += "\n✅ Your booking is now fully paid!\n"
                                else:
                                    balance = booking.total_amount - booking.amount_paid
                                    message_body += f"\nBalance Due: ${balance:.2f}\n"
                                
                                # Check if travelers are recorded
                                traveler_count = booking.travelers.count()
                                if traveler_count == 0:
                                    message_body += (
                                        "\n📋 *Next Step:* Please provide traveler details for all passengers.\n"
                                        "Reply with *traveler details* to get started."
                                    )
                                
                                send_whatsapp_message(
                                    booking.customer.contact.whatsapp_id,
                                    'text',
                                    {'body': message_body},
                                    booking.customer.contact.associated_app_config
                                )
                            except Exception as e:
                                self.message_user(
                                    request,
                                    f"Payment approved but failed to send WhatsApp notification: {e}",
                                    level='warning'
                                )
                    
                    approved_count += 1
                    
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error approving payment {payment.id}: {e}",
                    level='error'
                )
        
        if approved_count > 0:
            self.message_user(
                request,
                f"Successfully approved {approved_count} payment(s).",
                level='success'
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to approve {error_count} payment(s). Check error messages above.",
                level='error'
            )
    
    approve_payments.short_description = "Approve selected payments"
    
    def reject_payments(self, request, queryset):
        """
        Reject selected payments and notify customers.
        """
        from meta_integration.utils import send_whatsapp_message
        
        rejected_count = 0
        error_count = 0
        
        for payment in queryset.filter(status=Payment.PaymentStatus.PENDING):
            try:
                # Update payment status
                payment.status = Payment.PaymentStatus.FAILED
                payment.notes = (payment.notes or '') + f"\n[Rejected by {request.user.username} on {timezone.now().strftime('%Y-%m-%d %H:%M')}]"
                payment.save()
                
                # Send notification to customer via WhatsApp
                if payment.booking and payment.booking.customer and payment.booking.customer.contact:
                    try:
                        booking = payment.booking
                        message_body = (
                            f"❌ *Payment Not Approved*\n\n"
                            f"Unfortunately, we couldn't verify your payment of ${payment.amount:.2f} for booking *{booking.booking_reference}*.\n\n"
                            f"Please contact our finance team or try submitting the payment again with a clear proof of payment.\n\n"
                            f"You can record a new payment by typing *manual payment*."
                        )
                        
                        send_whatsapp_message(
                            booking.customer.contact.whatsapp_id,
                            'text',
                            {'body': message_body},
                            booking.customer.contact.associated_app_config
                        )
                    except Exception as e:
                        self.message_user(
                            request,
                            f"Payment rejected but failed to send WhatsApp notification: {e}",
                            level='warning'
                        )
                
                rejected_count += 1
                
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error rejecting payment {payment.id}: {e}",
                    level='error'
                )
        
        if rejected_count > 0:
            self.message_user(
                request,
                f"Successfully rejected {rejected_count} payment(s).",
                level='success'
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to reject {error_count} payment(s). Check error messages above.",
                level='error'
            )
    
    reject_payments.short_description = "Reject selected payments"

@admin.register(Traveler)
class TravelerAdmin(admin.ModelAdmin):
    """
    Admin interface for the Traveler model.
    """
    list_display = ('name', 'booking', 'traveler_type', 'age', 'nationality', 'gender', 'get_tour_date')
    list_filter = ('traveler_type', 'nationality', 'gender', 'booking__start_date')
    search_fields = ('name', 'id_number', 'booking__booking_reference', 'booking__tour_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['booking']
    actions = ['export_travelers_pdf', 'export_travelers_excel']
    fieldsets = (
        ('Traveler Info', {
            'fields': ('booking', 'name', 'age', 'traveler_type')
        }),
        ('Identity & Nationality', {
            'fields': ('nationality', 'gender', 'id_number', 'id_document')
        }),
        ('Special Requirements', {
            'fields': ('medical_dietary_requirements',)
        }),
        ('System Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_tour_date(self, obj):
        """Display the tour start date from the booking."""
        return obj.booking.start_date if obj.booking else None
    get_tour_date.short_description = 'Tour Date'
    get_tour_date.admin_order_field = 'booking__start_date'
    
    def export_travelers_pdf(self, request, queryset):
        """Export selected travelers to PDF."""
        # Create the HttpResponse object with PDF headers
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="travelers_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        # Create the PDF object using ReportLab
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>Traveler List Export</b><br/>Generated: {timezone.now().strftime('%B %d, %Y at %H:%M')}", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Prepare data for table
        data = [['Name', 'Booking Ref', 'Tour', 'Tour Date', 'Type', 'Age', 'Nationality', 'Gender', 'ID Number']]
        
        for traveler in queryset.select_related('booking'):
            start_date = traveler.booking.start_date.strftime('%Y-%m-%d') if traveler.booking and traveler.booking.start_date else 'N/A'
            
            data.append([
                traveler.name,
                traveler.booking.booking_reference if traveler.booking else 'N/A',
                traveler.booking.tour_name if traveler.booking else 'N/A',
                start_date,
                traveler.get_traveler_type_display(),
                str(traveler.age),
                traveler.nationality,
                traveler.gender,
                traveler.id_number
            ])
        
        # Create table
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF from buffer and write to response
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        self.message_user(request, f"Successfully exported {queryset.count()} traveler(s) to PDF.")
        return response
    
    export_travelers_pdf.short_description = "Export selected travelers to PDF"
    
    def export_travelers_excel(self, request, queryset):
        """Export selected travelers to CSV (Excel-compatible)."""
        # Create the HttpResponse object with CSV headers
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="travelers_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow([
            'Name', 'Booking Reference', 'Tour Name', 'Tour Start Date', 'Tour End Date',
            'Traveler Type', 'Age', 'Nationality', 'Gender', 'ID/Passport Number',
            'Medical/Dietary Requirements', 'Booking Status', 'Total Amount', 'Customer Name', 'Customer Email'
        ])
        
        # Write data rows
        for traveler in queryset.select_related('booking', 'booking__customer'):
            # Safely access booking and customer data
            if traveler.booking:
                customer_name = traveler.booking.customer.get_full_name() if traveler.booking.customer else 'N/A'
                customer_email = traveler.booking.customer.email if traveler.booking.customer else 'N/A'
                start_date = traveler.booking.start_date.strftime('%Y-%m-%d') if traveler.booking.start_date else 'N/A'
                end_date = traveler.booking.end_date.strftime('%Y-%m-%d') if traveler.booking.end_date else 'N/A'
                booking_ref = traveler.booking.booking_reference
                tour_name = traveler.booking.tour_name
                payment_status = traveler.booking.get_payment_status_display()
                total_amount = traveler.booking.total_amount
            else:
                customer_name = 'N/A'
                customer_email = 'N/A'
                start_date = 'N/A'
                end_date = 'N/A'
                booking_ref = 'N/A'
                tour_name = 'N/A'
                payment_status = 'N/A'
                total_amount = 'N/A'
            
            writer.writerow([
                traveler.name,
                booking_ref,
                tour_name,
                start_date,
                end_date,
                traveler.get_traveler_type_display(),
                traveler.age,
                traveler.nationality,
                traveler.gender,
                traveler.id_number,
                traveler.medical_dietary_requirements or 'None',
                payment_status,
                total_amount,
                customer_name,
                customer_email
            ])
        
        self.message_user(request, f"Successfully exported {queryset.count()} traveler(s) to CSV/Excel.")
        return response
    
    export_travelers_excel.short_description = "Export selected travelers to CSV/Excel"

@admin.register(TourInquiry)
class TourInquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'destinations', 'status', 'assigned_agent', 'created_at')
    list_filter = ('status', 'assigned_agent', 'created_at')
    search_fields = ('destinations', 'notes', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['customer', 'assigned_agent']