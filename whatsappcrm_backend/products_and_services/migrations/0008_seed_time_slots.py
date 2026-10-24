from datetime import time

from django.db import migrations

# The cruise times already published on the website (footer "Cruise times":
# sunrise 06:00–08:00, lunch 12:00–14:00, sunset 16:00 – after sunset).
# A tour only gets these if it has no slots yet, so admin-made slots are never
# touched. Other tours (day trips, dinner, venue hire, learners) get none and
# keep booking by date only until the owner adds slots in the admin.
SLOTS = {
    'Sunrise Cruise': [(time(6), time(8), 'Sunrise')],
    'Lunch Cruise': [(time(12), time(14), 'Lunch')],
    'Sunset Cruise': [(time(16), None, 'Sunset')],
    'Premium River Cruise (Breakfast, Lunch or Sunset)': [
        (time(6), time(8), 'Breakfast'),
        (time(12), time(14), 'Lunch'),
        (time(16), None, 'Sunset'),
    ],
}


def seed(apps, schema_editor):
    Tour = apps.get_model('products_and_services', 'Tour')
    TourTimeSlot = apps.get_model('products_and_services', 'TourTimeSlot')
    for name, slots in SLOTS.items():
        tour = Tour.objects.filter(name=name).first()
        if tour is None or TourTimeSlot.objects.filter(tour=tour).exists():
            continue
        TourTimeSlot.objects.bulk_create(
            TourTimeSlot(tour=tour, start_time=start, end_time=end, label=label) for start, end, label in slots
        )


def unseed(apps, schema_editor):
    TourTimeSlot = apps.get_model('products_and_services', 'TourTimeSlot')
    for name, slots in SLOTS.items():
        for start, end, label in slots:
            TourTimeSlot.objects.filter(tour__name=name, start_time=start, end_time=end, label=label).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products_and_services', '0007_tourtimeslot'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
