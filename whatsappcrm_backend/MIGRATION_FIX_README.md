# Database Migration Fixes

## Issue 1: Omari Integration Migration Conflict (Fixed)

### Problem
The error `CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph: (0002_omariuser, 0002_omariuser_alter_omaritransaction_status in omari_integration)` occurs when Django detects two different migrations with the same number (0002) in the `omari_integration` app.

### Root Cause
This typically happens when:
- Two different branches created different migrations numbered 0002
- One was applied to the database (0002_omariuser)
- The codebase now has a different 0002 migration (0002_omariuser_alter_omaritransaction_status)
- Django sees these as conflicting parallel migration paths

### Solution Applied
Created a merge migration file `0003_merge_20260205_1936.py` that:
- Depends on both conflicting migrations
- Contains no operations (just reconciles the migration graph)
- Tells Django that both migration paths have been merged

### How to Apply (using Docker)
Run the following command to apply the merge migration:

```bash
docker compose exec backend python manage.py migrate omari_integration
```

### Verification
After running migrations, verify they were applied successfully:

```bash
docker compose exec backend python manage.py showmigrations omari_integration
```

You should see [X] marks next to all three migrations:
- [X] 0001_initial
- [X] 0002_omariuser
- [X] 0002_omariuser_alter_omaritransaction_status
- [X] 0003_merge_20260205_1936

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
