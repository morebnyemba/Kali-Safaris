# Database Migration Fix

## Issue
The error `django.db.utils.ProgrammingError: column customer_data_traveler.id_document does not exist` occurs because migration `0007_add_id_document_to_traveler.py` has not been applied to the database.

## Solution
Run the following commands to apply pending migrations:

```bash
cd /home/runner/work/Kali-Safaris/Kali-Safaris/whatsappcrm_backend
python manage.py migrate customer_data
```

Or to migrate all apps:

```bash
python manage.py migrate
```

## Verification
After running migrations, verify they were applied successfully:

```bash
python manage.py showmigrations customer_data
```

You should see an [X] next to migration `0007_add_id_document_to_traveler`.

## Migration Details
- **Migration File**: `customer_data/migrations/0007_add_id_document_to_traveler.py`
- **What it does**: Adds an `id_document` FileField to the Traveler model to store uploaded ID/Passport documents
- **Field Details**: 
  - Type: FileField
  - Null: True (optional)
  - Blank: True (optional)
  - Upload path: `traveler_documents/%Y/%m/`
