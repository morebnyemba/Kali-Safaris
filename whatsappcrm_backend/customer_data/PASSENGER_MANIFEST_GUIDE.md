# Passenger Manifest Summary Report - User Guide

## Overview

The Passenger Manifest Summary Report provides operational headcounts for confirmed bookings, helping crew plan seating arrangements and calculate park fees.

## Report Format

### Summary Line
```
Chakanya(14), Nyemba(10) total: 24
```

### Detailed Breakdown Table
| Booking Reference | Customer/Group | Tour | Passenger Count |
|-------------------|----------------|------|-----------------|
| BK-T005-20260210 | Chakanya | Victoria Falls Safari | 14 |
| BK-T006-20260210 | Nyemba | Hwange Wildlife Tour | 10 |
| **TOTAL** | | | **24** |

## Usage

### For Crew Members
- **Individual counts** show passengers per group
- Helps set up seating arrangements
- Assists with logistics planning
- Useful for group coordination

### For Park Fees
- **Total count** determines park fees due
- Quick verification of vehicle capacity
- Useful for regulatory compliance

## Accessing the Report

### Method 1: Django Admin (Recommended)

1. Navigate to **Admin** → **Customer Data** → **Bookings**
2. Filter bookings by date using the date hierarchy
3. Select one or more bookings for the target date
4. From the **Actions** dropdown, select:
   - **"Export Passenger Summary (Operational - Headcount)"**
5. Click **"Go"**
6. PDF report downloads automatically

### Method 2: API Endpoint

**Endpoint:** `/api/customer-data/export/passenger-summary/`

**Query Parameters:**
- `date` (required): Tour date in YYYY-MM-DD format
- `format` (optional): 'pdf' or 'excel' (default: 'pdf')

**Examples:**

PDF format:
```bash
GET /api/customer-data/export/passenger-summary/?date=2026-02-10
```

Excel format:
```bash
GET /api/customer-data/export/passenger-summary/?date=2026-02-10&format=excel
```

**Authentication Required:** Yes (Bearer token or session)

**Response:** Binary file download (PDF or Excel)

## Report Features

### Filtering Logic
✅ **Only Confirmed Bookings** - Includes bookings with status:
- PAID (fully paid)
- DEPOSIT_PAID (partially paid)

❌ **Excludes:**
- PENDING bookings
- CANCELLED bookings
- REFUNDED bookings

### Passenger Count Logic
1. **Primary:** Counts actual traveler records in database
2. **Fallback:** If no travelers recorded, uses `number_of_adults + number_of_children` from booking

### Grouping
- Groups passengers by booking reference
- Shared booking references (same tour/date) appear together
- Customer name shown for each booking group

## Export Formats

### PDF Format
- **Use Case:** Print for crew, send to partners
- **Features:**
  - Professional layout with company branding
  - Date information clearly displayed
  - Breakdown table with alternating row colors
  - Usage notes included
  - Company footer on each page

### Excel Format
- **Use Case:** Further analysis, sharing via email
- **Features:**
  - Editable spreadsheet format
  - Same data as PDF
  - Auto-adjusted column widths
  - Easy to copy/paste
  - Compatible with Microsoft Excel, Google Sheets

## Example Scenarios

### Scenario 1: Day Trip Planning
**Situation:** Planning a day trip to Victoria Falls on Feb 10, 2026

**Steps:**
1. Generate report for Feb 10, 2026
2. Review summary: "Chakanya(14), Nyemba(10) total: 24"
3. Crew knows:
   - 2 groups to coordinate
   - 24 total passengers
   - Need seating for 24
   - Park fees for 24 people

### Scenario 2: Multi-Tour Day
**Situation:** Multiple tours departing on same day

**Report Shows:**
```
Safari Group A(12), Safari Group B(8), Hwange Tour(15) total: 35
```

**Crew can:**
- Separate groups by tour
- Calculate fees per tour
- Plan vehicle allocation
- Coordinate departure times

### Scenario 3: Last-Minute Changes
**Situation:** Booking status changes from PENDING to PAID

**Impact:**
- Report automatically includes the newly confirmed booking
- Real-time accuracy
- No manual tracking needed

## Tips & Best Practices

### 1. Generate Early
- Generate report 1-2 days before tour date
- Allows time for crew preparation
- Catches any last-minute confirmations

### 2. Verify Traveler Details
- Ensure all bookings have traveler records
- Check that traveler counts match booking's adult/children counts
- Update any missing information

### 3. Cross-Reference with Full Manifest
- Use this summary for headcounts
- Use the full manifest (with IDs) for ZimParks submission
- Both reports complement each other

### 4. Share with Team
- Email PDF to crew leaders
- Print copies for tour guides
- Share Excel version with operations team

## Troubleshooting

### Report Shows "No Confirmed Bookings"
**Cause:** No bookings with PAID or DEPOSIT_PAID status for that date

**Solutions:**
- Check booking payment status
- Verify correct date is selected
- Update payment status if needed

### Passenger Count Seems Wrong
**Cause:** Missing traveler records or incorrect booking counts

**Solutions:**
1. Check booking's traveler records
2. Verify `number_of_adults` and `number_of_children` fields
3. Add missing traveler details
4. Regenerate report

### Cannot Access Report
**Cause:** Missing permissions

**Solutions:**
- Ensure you're logged in as staff user
- Check API authentication (Bearer token)
- Contact system administrator

## API Response Examples

### Success Response (PDF)
```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="passenger_summary_2026-02-10.pdf"

[Binary PDF content]
```

### Success Response (Excel)
```http
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="passenger_summary_2026-02-10.xlsx"

[Binary Excel content]
```

### Error Response (Missing Date)
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Date parameter is required (format: YYYY-MM-DD)"
}
```

### Error Response (Invalid Date)
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Invalid date format. Use YYYY-MM-DD"
}
```

## Related Reports

### Full Passenger Manifest
- **Purpose:** Detailed traveler information for ZimParks
- **Includes:** Names, ID numbers, nationalities, ages
- **Use Case:** Regulatory compliance, park entry
- **Access:** Admin action or `/api/customer-data/export/manifest/`

### Booking Travelers Export
- **Purpose:** Complete traveler list across multiple bookings
- **Includes:** All traveler details plus booking info
- **Formats:** PDF, CSV/Excel
- **Use Case:** Comprehensive records, data analysis

## Support

For issues or questions:
- Contact system administrator
- Check Django admin logs
- Review booking payment statuses
- Verify tour date accuracy

---

**Document Version:** 1.0  
**Last Updated:** February 2026  
**Maintained By:** Slyker Tech Web Services
