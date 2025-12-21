# Deployment Checklist - Kali Safaris Booking System Updates

## Pre-Deployment

### 1. Review Changes
- ✅ All code changes reviewed and approved
- ✅ All tests passing
- ✅ No breaking changes to existing functionality
- ✅ Migrations created and tested

### 2. Backup Current System
```bash
# Backup database
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

# Backup current code (if not using git)
tar -czf backup_code_$(date +%Y%m%d_%H%M%S).tar.gz whatsappcrm_backend/
```

## Deployment Steps

### 1. Pull Latest Code
```bash
cd /path/to/Kali-Safaris
git pull origin main  # or your branch name
```

### 2. Install Dependencies (if any new ones)
```bash
cd whatsappcrm_backend
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
python manage.py migrate omari_integration
python manage.py migrate products_and_services
python manage.py migrate customer_data
```

Expected output:
```
Running migrations:
  Applying omari_integration.0001_initial... OK
  Applying products_and_services.0003_tour_duration_unit_tour_duration_value_and_more... OK
  Applying products_and_services.0004_alter_tour_duration_unit... OK
  Applying customer_data.0006_alter_booking_booking_reference... OK
```

### 4. Configure Omari Credentials
1. Access Django Admin: `https://your-domain.com/admin/`
2. Navigate to **Omari Integration → Omari Configurations**
3. Click **Add Omari Configuration**
4. Fill in:
   - **Name**: "Production" (or descriptive name)
   - **Base URL**: Your Omari API endpoint
   - **Merchant Key**: Your production API key
   - **Is Active**: ✅ Check this
   - **Is Production**: ✅ Check this
5. Click **Save**

### 5. Update Existing Tours (Optional)
If you want to set specific durations for existing tours:
1. Go to **Products And Services → Tour Packages**
2. Edit each tour
3. Set **Duration Value** and **Duration Unit**
4. Click **Save** (duration_days will auto-update)

### 6. Restart Application
```bash
# For production server (example using gunicorn)
sudo systemctl restart gunicorn

# Or if using Docker
docker-compose restart web

# Or if using PM2
pm2 restart kali-safaris
```

## Post-Deployment Verification

### 1. Test Omari Configuration
```bash
# From Django shell
python manage.py shell

>>> from omari_integration.models import OmariConfig
>>> config = OmariConfig.get_active_config()
>>> print(f"Active config: {config}")
>>> print(f"Base URL: {config.base_url}")
>>> print(f"Is Production: {config.is_production}")
```

### 2. Test Tour Duration
```bash
# From Django shell
python manage.py shell

>>> from products_and_services.models import Tour
>>> tour = Tour.objects.first()
>>> print(f"Duration: {tour.get_duration_display_text()}")
>>> print(f"Days equivalent: {tour.get_duration_in_days()}")
```

### 3. Test Booking Reference Generation
```bash
# From Django shell
python manage.py shell

>>> from datetime import date
>>> from customer_data.reference_generator import generate_shared_booking_reference
>>> ref = generate_shared_booking_reference(1, date(2025, 12, 25))
>>> print(f"Reference: {ref}")
# Should output: BK-T001-20251225
```

### 4. Test WhatsApp Booking Flow
1. Send a WhatsApp message to your business number
2. Start a booking flow
3. Select "Pay with Omari" option
4. Verify:
   - Booking is created
   - Travelers are saved
   - Shared booking reference is generated
   - Flow switches to Omari payment seamlessly

### 5. Test Admin Exports
1. Go to **Customer Data → Bookings**
2. Select multiple bookings
3. Choose **Export travelers to PDF** from actions
4. Verify PDF downloads correctly

## Rollback Plan (If Needed)

### If Issues Occur:

#### 1. Rollback Migrations
```bash
# Rollback to previous migration state
python manage.py migrate omari_integration zero
python manage.py migrate products_and_services 0002_seasonaltourprice
python manage.py migrate customer_data 0005_add_inquiry_reference_and_update_booking_reference
```

#### 2. Restore Code
```bash
git checkout <previous-commit-hash>
```

#### 3. Restore Database (if needed)
```bash
python manage.py loaddata backup_YYYYMMDD_HHMMSS.json
```

#### 4. Restart Application
```bash
sudo systemctl restart gunicorn
# or your restart command
```

## Monitoring

### First 24 Hours
- ✅ Monitor error logs: `tail -f /var/log/gunicorn/error.log`
- ✅ Check booking creation rates
- ✅ Verify Omari payment success rates
- ✅ Monitor database performance

### Week 1
- ✅ Review booking reference patterns
- ✅ Check traveler data completeness
- ✅ Verify export functionality usage
- ✅ Gather user feedback

## Support Contacts

### Technical Issues
- Check implementation summary: `IMPLEMENTATION_SUMMARY.md`
- Run test suite: `python test_booking_traveler_flow.py`
- Review migration status: `python manage.py showmigrations`

### Configuration Help
- Omari API documentation: Check your Omari merchant portal
- Duration configuration: See Tour model documentation
- Booking references: See reference_generator.py

## Success Criteria

✅ **Migrations Applied**: All 4 migrations run successfully  
✅ **Omari Config Active**: One active configuration exists  
✅ **Tours Updated**: Duration values set appropriately  
✅ **Bookings Working**: New bookings create with shared references  
✅ **Travelers Saving**: All traveler details captured correctly  
✅ **Flows Functioning**: Booking to Omari payment flow seamless  
✅ **Exports Working**: PDF and CSV exports generate correctly  

## Post-Deployment Tasks

### Within 1 Week
- [ ] Train staff on new Omari configuration interface
- [ ] Update user documentation
- [ ] Set up monitoring alerts for Omari payment failures
- [ ] Review and optimize shared booking reference queries

### Within 1 Month
- [ ] Analyze booking reference patterns
- [ ] Review duration usage (minutes vs hours vs days)
- [ ] Optimize export performance if needed
- [ ] Collect user feedback on flow improvements

## Notes

- **Zero Downtime**: These changes can be deployed without downtime
- **Backward Compatible**: Existing bookings continue to work
- **Data Safe**: All migrations are non-destructive
- **Tested**: Comprehensive test suite ensures functionality

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Version**: See git commit hash in PR  
**Status**: _______________
