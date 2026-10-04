from django.db import migrations

# 0005 seeded the old homepage pricing tiers alongside the named cruises, which
# left two pairs of tours that are the same product under different names:
#
#   "Dinner Cruise Package (Per Person)"  ==  "Dinner Cruise"            ($75, 3h)
#   "River Cruise with Cash Bar"          ==  Sunrise/Lunch/Sunset Cruise ($25, 2h)
#
# Customers saw both on the website and in the WhatsApp tour list. The
# duplicate is deactivated, never deleted, so bookings that point at it keep
# their history. It's only touched when it still has the same price as the
# tour it duplicates — if the owner has since given it its own price in the
# admin, it's a real product and is left alone.
DUPLICATES = [
    # (duplicate, canonical tours it repeats)
    ('Dinner Cruise Package (Per Person)', ['Dinner Cruise']),
    ('River Cruise with Cash Bar', ['Sunrise Cruise', 'Lunch Cruise', 'Sunset Cruise']),
]


def deactivate_duplicates(apps, schema_editor):
    Tour = apps.get_model('products_and_services', 'Tour')
    for dup_name, canonical_names in DUPLICATES:
        dup = Tour.objects.filter(name=dup_name, is_active=True).first()
        if dup is None:
            continue
        canonical_prices = set(
            Tour.objects.filter(name__in=canonical_names, is_active=True).values_list('base_price', flat=True)
        )
        if dup.base_price in canonical_prices:
            # .update() skips Tour.save()'s full_clean, which historical models don't have anyway.
            Tour.objects.filter(pk=dup.pk).update(is_active=False)


def reactivate_duplicates(apps, schema_editor):
    Tour = apps.get_model('products_and_services', 'Tour')
    Tour.objects.filter(name__in=[name for name, _ in DUPLICATES]).update(is_active=True)


class Migration(migrations.Migration):

    dependencies = [
        ('products_and_services', '0005_seed_default_tours'),
    ]

    operations = [
        migrations.RunPython(deactivate_duplicates, reactivate_duplicates),
    ]
