from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import GalleryImage


@receiver(post_delete, sender=GalleryImage)
def delete_gallery_file(sender, instance, **kwargs):
    """Remove the photo from disk when its gallery entry is deleted (including bulk deletes in the admin)."""
    if instance.image:
        instance.image.delete(save=False)


@receiver(pre_save, sender=GalleryImage)
def delete_replaced_gallery_file(sender, instance, **kwargs):
    """Remove the old photo from disk when an entry's image is replaced."""
    if not instance.pk:
        return
    old = GalleryImage.objects.filter(pk=instance.pk).values_list('image', flat=True).first()
    if old and old != instance.image.name:
        instance.image.storage.delete(old)
