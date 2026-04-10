# ID Document Capture via WhatsApp - Technical Documentation

## Overview

The system automatically captures ID/Passport images from travelers through the WhatsApp Flow, stores them securely, and displays their status in operational reports.

## How It Works

### 1. User Experience (WhatsApp Flow)

When collecting traveler details during booking:

**Step 1: Basic Information**
- Traveler enters: name, age, nationality, gender, ID number, medical needs
- Click "Continue" button

**Step 2: ID Document Upload**
- Screen prompts: "Upload ID/Passport"
- Shows PhotoPicker component
- User can:
  - Take a photo with camera
  - Upload from photo gallery
- User must upload exactly 1 photo (required)
- Click "Submit Details" button

**What Happens Behind the Scenes:**
```
User takes/selects photo
    ↓
WhatsApp uploads to Meta servers
    ↓
Meta returns Media ID (e.g., "MEDIA_ID_12345")
    ↓
WhatsApp Flow completes with payload:
{
  "traveler_name": "John Doe",
  "traveler_age": "35",
  ...
  "id_document_photo": "MEDIA_ID_12345"  ← Key field
}
```

---

## Technical Implementation

### 1. WhatsApp Flow Definition

**File:** `flows/definitions/traveler_details_whatsapp_flow.py`

**Screen 2: ID_DOCUMENT_UPLOAD**
```python
{
    "id": "ID_DOCUMENT_UPLOAD",
    "title": "Upload ID Document",
    "layout": {
        "type": "SingleColumnLayout",
        "children": [
            {
                "type": "PhotoPicker",
                "name": "id_document_photo",  # ← Field name
                "label": "ID/Passport Photo",
                "description": "Take or upload a photo of the ID/Passport",
                "photo-source": "camera_gallery",
                "min-uploaded-photos": 1,  # Required
                "max-uploaded-photos": 1   # Only 1 allowed
            },
            {
                "type": "Footer",
                "label": "Submit Details",
                "on-click-action": {
                    "name": "complete",
                    "payload": {
                        "traveler_name": "${data.traveler_name}",
                        # ... other fields ...
                        "id_document_photo": "${form.id_document_photo}"  # ← Returns Media ID
                    }
                }
            }
        ]
    }
}
```

### 2. Response Processing

**File:** `flows/whatsapp_flow_response_processor.py`

```python
def process_response(whatsapp_flow, contact, response_data):
    """Processes WhatsApp Flow response and merges into flow context"""
    
    # Extract data from response
    wa_data = response_data.get('data', response_data)
    # wa_data now contains: {'id_document_photo': 'MEDIA_ID_12345', ...}
    
    # Merge into flow context
    context.update(wa_data)
    
    # Now context has 'id_document_photo' available
```

### 3. Booking Flow Processing

**File:** `flows/definitions/booking_flow.py`

**Step: process_traveler_details_response**
```python
{
    "action_type": "set_context_variable",
    "variable_name": "current_traveler_id_document",
    "value_template": "{{ (traveler_details_response or {}).get('id_document_photo', '') }}"
}
```

**Step: add_traveler_to_list**
```python
{
    "action_type": "set_context_variable",
    "variable_name": "travelers_details",
    "value_template": "{{ travelers_details + [{
        'name': current_traveler_name,
        'age': current_traveler_age,
        'nationality': current_traveler_nationality,
        'medical': current_traveler_medical,
        'gender': current_traveler_gender,
        'id_number': current_traveler_id_number,
        'id_document': current_traveler_id_document,  # ← Media ID stored here
        'type': ('adult' if (traveler_index|int) <= (num_adults|int) else 'child')
    }] }}"
}
```

### 4. Save Travelers Action

**File:** `flows/actions.py` - Function: `save_travelers_to_booking()`

```python
for traveler_data in travelers_details:
    # Extract fields
    name = traveler_data.get('name', '')
    age = traveler_data.get('age', 0)
    # ... other fields ...
    id_document_media_id = traveler_data.get('id_document', '')  # ← Get Media ID
    
    # Create Traveler record
    traveler = Traveler.objects.create(
        booking=booking,
        name=name,
        age=age_int,
        nationality=nationality,
        gender=gender,
        id_number=id_number,
        medical_dietary_requirements=medical_requirements,
        traveler_type=traveler_type
    )
    
    # Handle ID document if provided
    if id_document_media_id:
        try:
            # Download media from WhatsApp
            download_result = download_whatsapp_media(
                id_document_media_id,
                contact.associated_app_config
            )
            
            if download_result:
                media_content, media_mime_type = download_result
                
                # Determine file extension from mime type
                file_extension = mimetypes.guess_extension(media_mime_type) or '.jpg'
                
                # Save to Traveler model
                file_name = f"id_document_{traveler.id}{file_extension}"
                traveler.id_document.save(
                    file_name, 
                    ContentFile(media_content), 
                    save=True
                )
                
                logger.info(f"Successfully saved ID document for traveler {name}")
        except Exception as e:
            logger.error(f"Error saving ID document for traveler {name}: {e}")
```

### 5. Media Download Utility

**File:** `meta_integration/utils.py` - Function: `download_whatsapp_media()`

```python
def download_whatsapp_media(media_id: str, config: MetaAppConfig):
    """
    Downloads media from WhatsApp using Media ID.
    
    Args:
        media_id: The Media ID from the flow response
        config: Meta API configuration with access token
    
    Returns:
        Tuple of (content_bytes, mime_type) or None on failure
    """
    # Step 1: Get media URL from Meta API
    get_url_endpoint = f"https://graph.facebook.com/{config.api_version}/{media_id}/"
    headers = {"Authorization": f"Bearer {config.access_token}"}
    
    response = requests.get(get_url_endpoint, headers=headers, timeout=10)
    response.raise_for_status()
    
    media_info = response.json()
    media_url = media_info.get("url")
    mime_type = media_info.get("mime_type")
    
    # Step 2: Download actual media content
    media_response = requests.get(
        media_url,
        headers={"Authorization": f"Bearer {config.access_token}"},
        timeout=20
    )
    media_response.raise_for_status()
    
    logger.info(f"Successfully downloaded media for Media ID {media_id} ({mime_type})")
    return media_response.content, mime_type
```

---

## Data Model

### Traveler Model

**File:** `customer_data/models.py`

```python
class Traveler(models.Model):
    """Represents an individual traveler on a booking"""
    
    booking = models.ForeignKey(Booking, related_name='travelers', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    nationality = models.CharField(max_length=100)
    gender = models.CharField(max_length=20)
    id_number = models.CharField(max_length=100)
    medical_dietary_requirements = models.TextField(blank=True)
    traveler_type = models.CharField(max_length=20)  # 'adult' or 'child'
    
    # ID Document field - stores uploaded image
    id_document = models.FileField(
        upload_to='traveler_documents/',
        null=True,
        blank=True,
        help_text="ID or Passport document image"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Migration:** `customer_data/migrations/0007_add_id_document_to_traveler.py`

**File Storage:**
- Location: `media/traveler_documents/`
- Filename format: `id_document_{traveler_id}.{extension}`
- Examples:
  - `id_document_123.jpg`
  - `id_document_124.png`
  - `id_document_125.pdf`

---

## Report Integration

### Full Passenger Manifest

**Shows ID document status per traveler:**

```
┌─────────────┬────────────┬─────────────┬─────┬────────┐
│ Full Name   │ ID Number  │ Nationality │ Age │ ID Doc │
├─────────────┼────────────┼─────────────┼─────┼────────┤
│ John Doe    │ 12345678   │ Zimbabwean  │ 35  │   ✓    │
│ Jane Doe    │ 87654321   │ Zimbabwean  │ 32  │   ✓    │
│ Junior Doe  │ 11111111   │ Zimbabwean  │  8  │   ✗    │
└─────────────┴────────────┴─────────────┴─────┴────────┘

ID Doc: ✓ = ID/Passport image uploaded via WhatsApp | ✗ = Not uploaded
```

### Passenger Summary Report

**Shows ID document count per booking:**

```
Confirmed Passenger Summary:
Chakanya(3), Nyemba(2) total: 5
ID Documents Uploaded: 4 of 5

Breakdown by Booking Group:
┌────────────┬──────────┬───────────┬────────────┬─────────┐
│ Booking    │ Customer │ Tour      │ Passengers │ ID Docs │
├────────────┼──────────┼───────────┼────────────┼─────────┤
│ BK-T005... │ Chakanya │ Safari... │     3      │   3/3   │
│ BK-T006... │ Nyemba   │ Safari... │     2      │   1/2   │
│ TOTAL      │          │           │     5      │   4/5   │
└────────────┴──────────┴───────────┴────────────┴─────────┘
```

---

## Verification & Debugging

### Check if ID Documents are Being Saved

**1. Database Query:**
```sql
SELECT 
    t.name,
    t.id_number,
    t.id_document,
    LENGTH(t.id_document) > 0 AS has_document
FROM customer_data_traveler t
WHERE t.booking_id = <booking_id>
ORDER BY t.created_at;
```

**2. Django Shell:**
```python
from customer_data.models import Traveler

# Get travelers with ID documents
travelers_with_docs = Traveler.objects.exclude(id_document='')
print(f"Travelers with ID docs: {travelers_with_docs.count()}")

# Check specific traveler
traveler = Traveler.objects.get(id=123)
print(f"Has ID doc: {bool(traveler.id_document)}")
print(f"Document path: {traveler.id_document.path if traveler.id_document else 'None'}")
```

**3. File System:**
```bash
# Check if files exist
ls -lah media/traveler_documents/

# Count files
ls media/traveler_documents/ | wc -l

# Check recent uploads
ls -lt media/traveler_documents/ | head -10
```

**4. Admin Interface:**
- Navigate to: Admin → Customer Data → Travelers
- Click on a traveler record
- Check "ID document" field
- If uploaded, link to view/download will appear

### Common Issues & Solutions

#### Issue: ID documents not being saved

**Possible Causes:**
1. **WhatsApp API credentials invalid**
   - Check: MetaAppConfig in admin
   - Verify: Access token is valid
   - Test: Try downloading any media manually

2. **Media download failing**
   - Check logs for: `"Error saving ID document"`
   - Common errors:
     - Network timeout
     - Invalid Media ID
     - Expired media URL (WhatsApp media expires)

3. **File storage permissions**
   - Check: `media/traveler_documents/` directory exists
   - Verify: Write permissions on directory
   - Test: Try creating a file manually

4. **Flow not completing**
   - Check: WhatsApp Flow response is being received
   - Verify: `id_document_photo` is in response data
   - Look for: `"whatsapp_flow_response_received": True` in context

### Log Messages to Look For

**Success:**
```
Successfully downloaded media for Media ID {media_id} (image/jpeg)
Successfully saved ID document for traveler John Doe (mime: image/jpeg)
Created Payment record and updated booking
```

**Failure:**
```
Error saving ID document for traveler Jane Doe: [error details]
Failed to get media URL for Media ID {media_id}
Error during media download for Media ID {media_id}
```

### Testing the Complete Flow

**Manual Test:**
1. Start booking flow via WhatsApp
2. Select tour and dates
3. Enter number of travelers
4. Fill traveler details (include all fields)
5. Upload ID photo when prompted
6. Complete booking
7. Check logs for success messages
8. Query database for traveler record
9. Verify file exists in media directory
10. Generate manifest report
11. Confirm ✓ appears for that traveler

---

## Security & Privacy

### Data Protection

**Storage:**
- Files stored securely in `media/traveler_documents/`
- Not publicly accessible (requires authentication)
- Only viewable by staff/admin users

**Access Control:**
- Admin users can view/download via Django admin
- API endpoints require authentication
- Reports only accessible to authenticated staff

**Retention:**
- Documents stored indefinitely (or per company policy)
- Can be manually deleted from admin interface
- Consider implementing auto-deletion policy after tour completion

### GDPR/Privacy Compliance

**Considerations:**
- ID documents are sensitive personal data
- Obtain consent before collection (mention in T&Cs)
- Allow travelers to request deletion
- Implement data retention policy
- Secure storage and transmission
- Log access to documents

---

## Future Enhancements

### Potential Improvements

1. **Document Validation**
   - Check image quality/readability
   - Verify ID number matches entered data (OCR)
   - Flag suspicious/unclear documents

2. **Bulk Operations**
   - Download all IDs for a tour as ZIP
   - Bulk email IDs to ZimParks
   - Generate compiled PDF with all IDs

3. **Reminder System**
   - Auto-remind travelers with missing IDs
   - Send follow-up WhatsApp messages
   - Deadline notifications (e.g., "Upload ID 48hrs before tour")

4. **Integration**
   - Direct submission to ZimParks portal
   - Sync with government verification systems
   - Integration with booking confirmation emails

5. **Analytics**
   - Track upload completion rates
   - Identify bottlenecks in flow
   - Monitor time-to-upload metrics

---

## API Reference

### Endpoints Using ID Documents

**1. Export Full Manifest**
```
GET /api/customer-data/export/manifest/?date=YYYY-MM-DD
```
Returns: PDF with ID document status (✓/✗)

**2. Export Passenger Summary**
```
GET /api/customer-data/export/passenger-summary/?date=YYYY-MM-DD&format=pdf
```
Returns: PDF/Excel with ID document counts

**3. Admin Actions**
- **"Export Manifest for Booking Date (ZimParks Format)"**
  - Shows ID document status per traveler
  
- **"Export Passenger Summary (Operational - Headcount)"**
  - Shows ID document counts per booking

---

## Troubleshooting Guide

### Problem: Travelers not uploading IDs

**Solutions:**
1. Check WhatsApp Flow is properly configured
2. Verify PhotoPicker component is visible
3. Test with different devices/OS versions
4. Check WhatsApp Business API status

### Problem: Media download fails

**Solutions:**
1. Verify Meta API credentials
2. Check access token hasn't expired
3. Ensure Media ID is valid
4. Check network connectivity
5. Review rate limits (Meta API)

### Problem: Files not appearing in reports

**Solutions:**
1. Refresh traveler record from database
2. Check `id_document` field is populated
3. Verify file path is correct
4. Regenerate report
5. Check report generation code for errors

---

## Support & Maintenance

### Monitoring

**Regular Checks:**
- Review upload success rates
- Monitor error logs
- Check storage space usage
- Verify Meta API quotas

**Alerts to Set Up:**
- Failed media downloads (>5% failure rate)
- Storage approaching capacity
- API credential expiration warnings
- Missing IDs close to tour date

### Maintenance Tasks

**Weekly:**
- Review error logs
- Check upload completion rates
- Verify recent uploads are accessible

**Monthly:**
- Archive old documents (if policy allows)
- Review storage usage
- Update documentation as needed
- Test complete flow end-to-end

---

## Summary

✅ **Fully Implemented** - ID document capture is production-ready  
✅ **Automated** - Downloads and stores images automatically  
✅ **Visible** - Reports show upload status  
✅ **Secure** - Proper access controls and storage  
✅ **Reliable** - Error handling and logging in place

The system successfully captures ID/Passport images through the WhatsApp Flow, stores them securely, and provides operational visibility through reports. This meets ZimParks requirements and improves tour operations.

---

**Document Version:** 1.0  
**Last Updated:** February 2026  
**Maintained By:** Slyker Tech Web Services
