from decimal import Decimal

from django.db import migrations

# These mirror the tour packages that used to be hardcoded on the public
# website (booking page cruise picker + homepage pricing tiers) before the
# website started reading its trip catalogue from this Tour table. Seeding
# them here means the live site keeps showing the same packages customers
# already knew, on top of whatever tours have since been added in the admin.
#
# Matched by `name` via get_or_create, so this is safe to run against a
# database that already has some/all of these (no duplicates) or none of
# them (all get created), and never touches unrelated existing tours.
DEFAULT_TOURS = [
    # ── Named cruises from the booking page's cruise picker ──────────────
    {
        'name': 'Sunrise Cruise',
        'description': 'Start your day with the peaceful sounds of the Zambezi as hippos yawn and fish eagles call.',
        'category': 'safari',
        'base_price': Decimal('25.00'),
        'duration_value': 2,
        'duration_unit': 'hours',
        'duration_days': 1,
        'location': 'Zambezi River, Victoria Falls',
    },
    {
        'name': 'Lunch Cruise',
        'description': 'A relaxing midday cruise along the river with stunning views and refreshing breezes.',
        'category': 'safari',
        'base_price': Decimal('25.00'),
        'duration_value': 2,
        'duration_unit': 'hours',
        'duration_days': 1,
        'location': 'Zambezi River, Victoria Falls',
    },
    {
        'name': 'Sunset Cruise',
        'description': 'The most popular cruise — watch the African sun set over the Zambezi in golden splendour.',
        'category': 'safari',
        'base_price': Decimal('25.00'),
        'duration_value': 3,
        'duration_unit': 'hours',
        'duration_days': 1,
        'location': 'Zambezi River, Victoria Falls',
    },
    {
        'name': 'Dinner Cruise',
        'description': 'An exclusive evening on the river, complete with a gourmet dinner under the stars.',
        'category': 'safari',
        'base_price': Decimal('75.00'),
        'duration_value': 3,
        'duration_unit': 'hours',
        'duration_days': 1,
        'location': 'Zambezi River, Victoria Falls',
    },
    {
        'name': 'Jetty Venue Hire',
        'description': 'Host your wedding, conference, or cocktail event at our beautiful riverside jetty.',
        'category': 'custom',
        'base_price': Decimal('70.00'),
        'duration_value': 4,
        'duration_unit': 'hours',
        'duration_days': 1,
        'location': 'Kalai Safaris Jetty, Victoria Falls',
    },
    # ── Per-person pricing tiers from the homepage Pricing section ───────
    {
        'name': 'Learners Special Cruise Package',
        'description': 'Per person. A discounted river cruise package for school children and learners.',
        'category': 'safari',
        'base_price': Decimal('15.00'),
        'duration_value': 2,
        'duration_unit': 'hours',
        'duration_days': 1,
        'location': 'Zambezi River, Victoria Falls',
    },
    {
        'name': 'River Cruise with Cash Bar',
        'description': 'Per person, includes access to the onboard cash bar.',
        'category': 'safari',
        'base_price': Decimal('25.00'),
        'duration_value': 2,
        'duration_unit': 'hours',
        'duration_days': 1,
        'location': 'Zambezi River, Victoria Falls',
    },
    {
        'name': 'Premium River Cruise (Breakfast, Lunch or Sunset)',
        'description': 'Per person, includes beverages and food depending on the Breakfast, Lunch, or Sunset service selected.',
        'category': 'safari',
        'base_price': Decimal('55.00'),
        'duration_value': 2,
        'duration_unit': 'hours',
        'duration_days': 1,
        'location': 'Zambezi River, Victoria Falls',
    },
    {
        'name': 'Dinner Cruise Package (Per Person)',
        'description': 'Per person rate for the dinner cruise package.',
        'category': 'safari',
        'base_price': Decimal('75.00'),
        'duration_value': 3,
        'duration_unit': 'hours',
        'duration_days': 1,
        'location': 'Zambezi River, Victoria Falls',
    },
]


def seed_default_tours(apps, schema_editor):
    Tour = apps.get_model('products_and_services', 'Tour')
    for entry in DEFAULT_TOURS:
        name = entry['name']
        defaults = {key: value for key, value in entry.items() if key != 'name'}
        defaults['is_active'] = True
        Tour.objects.get_or_create(name=name, defaults=defaults)


def unseed_default_tours(apps, schema_editor):
    Tour = apps.get_model('products_and_services', 'Tour')
    names = [entry['name'] for entry in DEFAULT_TOURS]
    Tour.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products_and_services', '0004_alter_tour_duration_unit'),
    ]

    operations = [
        migrations.RunPython(seed_default_tours, unseed_default_tours),
    ]
