# Database Migration Fixes

## Issue 1: Omari Integration Migration Conflict (Fixed)

### Problem
The error `CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph: (0002_omariuser, 0002_omariuser_alter_omaritransaction_status in omari_integration)` occurs when Django detects two different migrations with the same number (0002) in the `omari_integration` app.

### Root Cause
The database has a migration called `0002_omariuser` applied, but the codebase had a file named `0002_omariuser_alter_omaritransaction_status.py` with a different filename, causing Django to see them as separate conflicting migrations.

### Solution Applied
Removed the conflicting migration file `0002_omariuser_alter_omaritransaction_status.py` from the codebase. Users should regenerate it manually using Django's makemigrations command, which will create the migration with the correct name that matches what's in the database.

### How to Apply (using Docker)

1. **Pull the latest code** that has the conflicting migration removed

2. **Generate the migration** based on your current models:
```bash
docker compose exec backend python manage.py makemigrations omari_integration
```

This will create a new migration file (likely `0002_omariuser.py`) that includes:
- CreateModel for OmariUser
- AlterField for OmariTransaction.status (adding 'VOIDED' option)

3. **Apply the migration**:
```bash
docker compose exec backend python manage.py migrate omari_integration
```

### Verification
After running migrations, verify they were applied successfully:

```bash
docker compose exec backend python manage.py showmigrations omari_integration
```

You should see [X] marks next to all migrations:
- [X] 0001_initial
- [X] 0002_omariuser (or whatever name was generated)

---

## Issue 2: Customer Data Traveler ID Document

### Problem
The error `django.db.utils.ProgrammingError: column customer_data_traveler.id_document does not exist` occurs because migration `0007_add_id_document_to_traveler.py` has not been applied to the database.

### Solution
Run the following commands to apply pending migrations:

```bash
# Using Docker
docker compose exec backend python manage.py migrate customer_data

# Or to migrate all apps
docker compose exec backend python manage.py migrate

# Local development (if not using Docker)
cd /home/runner/work/Kali-Safaris/Kali-Safaris/whatsappcrm_backend
python manage.py migrate customer_data
```

### Verification
After running migrations, verify they were applied successfully:

```bash
docker compose exec backend python manage.py showmigrations customer_data
```

You should see an [X] next to migration `0007_add_id_document_to_traveler`.

### Migration Details
- **Migration File**: `customer_data/migrations/0007_add_id_document_to_traveler.py`
- **What it does**: Adds an `id_document` FileField to the Traveler model to store uploaded ID/Passport documents
- **Field Details**: 
  - Type: FileField
  - Null: True (optional)
  - Blank: True (optional)
  - Upload path: `traveler_documents/%Y/%m/`
