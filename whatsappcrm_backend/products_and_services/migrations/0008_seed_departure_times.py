from django.db import migrations

# The cruise times already published on the website (footer "Cruise times"
# and the homepage cruise cards). Only tours whose departure_times are still
# blank are filled in, so anything the owner has set in the admin is kept.
# Tours not listed here (day trips, dinner, venue hire, learners) stay blank
# and keep booking without a time until the owner sets one.
DEPARTURES = {
    'Sunrise Cruise': '06:00',
    'Lunch Cruise': '12:00',
    'Sunset Cruise': '16:00',
    'Premium River Cruise (Breakfast, Lunch or Sunset)': '06:00, 12:00, 16:00',
}


def seed(apps, schema_editor):
    Tour = apps.get_model('products_and_services', 'Tour')
    for name, times in DEPARTURES.items():
        Tour.objects.filter(name=name, departure_times='').update(departure_times=times)


def unseed(apps, schema_editor):
    Tour = apps.get_model('products_and_services', 'Tour')
    for name, times in DEPARTURES.items():
        Tour.objects.filter(name=name, departure_times=times).update(departure_times='')


class Migration(migrations.Migration):

    dependencies = [
        ('products_and_services', '0007_tour_departure_times'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
