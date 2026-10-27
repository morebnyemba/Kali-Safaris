from pathlib import Path

from django.core.files import File
from django.db import migrations

# The photos that used to be hardcoded on the website's gallery page. Seeding
# them as GalleryImage rows lets staff edit or delete them in the admin like
# any photo they upload. Only runs on an empty gallery, so it never brings
# back photos staff have already removed.
SEED_DIR = Path(__file__).resolve().parent.parent / 'gallery_seed'
SEED_IMAGES = [
    ('kalai_intro.jpeg', 'Kalai Safari Enigma Boat', 'boat'),
    ('sunrise.jpeg', 'Sunrise on the Zambezi', 'sunrise'),
    ('sunset.jpeg', 'Sunset Cruise', 'sunset'),
    ('Kalai Sunset background shot.jpeg', 'Golden Sunset on the Zambezi', 'sunset'),
    ('work_no_play.jpeg', 'Lunch Cruise Experience', 'boat'),
    ('jetty_venue.jpg', 'Jetty Venue', 'jetty'),
    ('Kalai Safaris interior chairs.jpeg', 'Boat Interior Setup', 'boat'),
    ('Kalai Safaris jetty site.jpeg', 'Jetty Site View', 'jetty'),
    ('cruise boat.jpg', 'Cruise Boat on Water', 'boat'),
    ('Boats .jpg', 'Safari Boats Docked', 'boat'),
    ('jetty site 2.jpg', 'Riverside Jetty', 'jetty'),
    ('jetty 3.jpg', 'Jetty Evening View', 'jetty'),
    ('Kalai Safaris Rendezvous.jpeg', 'Rendezvous Vessel', 'boat'),
    ('Kalai Safaris On the River.jpeg', 'Cruising on the Zambezi', 'boat'),
    ('cruise with palms.jpg', 'Cruise with Palm Trees', 'boat'),
    ('boat entry.jpg', 'Boarding the Boat', 'boat'),
]


def seed_gallery(apps, schema_editor):
    GalleryImage = apps.get_model('products_and_services', 'GalleryImage')
    if GalleryImage.objects.exists():
        return
    for order, (filename, caption, category) in enumerate(SEED_IMAGES):
        path = SEED_DIR / filename
        if not path.exists():
            continue
        entry = GalleryImage(caption=caption, category=category, sort_order=order * 10)
        with path.open('rb') as fh:
            entry.image.save(filename.replace(' ', '_'), File(fh), save=True)


def unseed_gallery(apps, schema_editor):
    GalleryImage = apps.get_model('products_and_services', 'GalleryImage')
    for entry in GalleryImage.objects.filter(caption__in=[caption for _, caption, _ in SEED_IMAGES]):
        entry.image.delete(save=False)
        entry.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products_and_services', '0007_galleryimage'),
    ]

    operations = [
        migrations.RunPython(seed_gallery, unseed_gallery),
    ]
