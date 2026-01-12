# Fix Summary for PDF Export Issues

## Issues Resolved

### 1. AttributeError: 'Settings' object has no attribute 'CHURCH_DETAILS'

**Error Location**: `/app/customer_data/exports.py`, line 59

**Root Cause**: 
The code was attempting to access `settings.CHURCH_DETAILS` which doesn't exist in the settings file. The correct setting name is `COMPANY_DETAILS`.

**Changes Made**:
- Updated `customer_data/exports.py`:
  - Line 30: `settings.CHURCH_DETAILS` → `settings.COMPANY_DETAILS`
  - Line 32: Updated warning message
  - Line 59: `settings.CHURCH_DETAILS` → `settings.COMPANY_DETAILS`
  - Updated function docstrings and fallback values

**Files Modified**:
- `whatsappcrm_backend/customer_data/exports.py`

---

### 2. ProgrammingError: column customer_data_traveler.id_document does not exist

**Error Location**: Database query in `/app/customer_data/admin.py`, line 165

**Root Cause**: 
Migration `0007_add_id_document_to_traveler.py` exists but hasn't been applied to the database.

**Solution**:
Run the following command to apply pending migrations:

```bash
cd /home/runner/work/Kali-Safaris/Kali-Safaris/whatsappcrm_backend
python manage.py migrate customer_data
```

Or migrate all apps:
```bash
python manage.py migrate
```

**Files Created**:
- `whatsappcrm_backend/MIGRATION_FIX_README.md` - Detailed migration instructions

---

## Verification Steps

### For Issue 1 (CHURCH_DETAILS):
✅ All code references updated
✅ Code review passed
✅ Security scan passed
✅ No breaking changes introduced

### For Issue 2 (Database Migration):
After running the migration command:

1. Verify migration status:
   ```bash
   python manage.py showmigrations customer_data
   ```
   You should see `[X]` next to `0007_add_id_document_to_traveler`

2. Test the PDF export functionality:
   - Navigate to Django Admin → Bookings
   - Select one or more bookings
   - Choose "Export travelers from selected bookings to PDF" action
   - The export should complete without errors

3. Test the manifest export:
   - Select bookings with the same date
   - Choose "Export Manifest for Booking Date (ZimParks Format)"
   - The manifest PDF should generate successfully

---

## Configuration Validation

The settings file (`whatsappcrm_backend/settings.py`) already has `COMPANY_DETAILS` properly configured:

```python
COMPANY_DETAILS = {
    'NAME': 'Kalai Safaris',
    'ADDRESS_LINE_1': '123 Adventure Lane',
    'ADDRESS_LINE_2': 'Victoria Falls, Zimbabwe',
    'CONTACT_PHONE': '+263 123 456 789',
    'CONTACT_EMAIL': 'bookings@kalaisafaris.com',
    'WEBSITE': 'www.kalaisafaris.com',
}
```

No additional configuration changes are required.

---

## Impact Assessment

**Minimal Changes**: Only the necessary references were updated
**No Breaking Changes**: Existing functionality remains intact
**Security**: No vulnerabilities introduced (verified via CodeQL)
**Database**: Migration adds an optional field (nullable and blank)

---

## Next Steps

1. **Deploy the code changes** to your environment
2. **Run the database migration** using the command provided above
3. **Test the PDF export functionality** to confirm the fix works
4. **Monitor logs** for any additional errors

If you encounter any issues after applying these fixes, please check:
- Django logs for any new error messages
- Database connection is working properly
- All migrations have been applied successfully
