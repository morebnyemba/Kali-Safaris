from rest_framework import serializers

from .models import GalleryImage


class GalleryImageSerializer(serializers.ModelSerializer):
    """Gallery photos as the CRM dashboard manages them. `image` is upload-only; `image_url` is for display."""
    image = serializers.ImageField(write_only=True, required=False)
    image_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    # Uploads are multipart, where DRF reads a missing boolean as False; new photos should be visible.
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = GalleryImage
        fields = [
            'id', 'image', 'image_url', 'category', 'category_display', 'caption', 'year',
            'sort_order', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ('id', 'image_url', 'category_display', 'created_at', 'updated_at')

    def get_image_url(self, obj):
        if not obj.image:
            return None
        # The dashboard is on another domain, so it needs an absolute URL; the
        # trailing slash skips Django's APPEND_SLASH redirect.
        url = obj.file_path() + '/'
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url

    def validate_year(self, value):
        if value is not None and not 1900 <= value <= 2100:
            raise serializers.ValidationError('Enter a four-digit year.')
        return value

    def validate(self, attrs):
        if self.instance is None and not attrs.get('image'):
            raise serializers.ValidationError({'image': 'Choose a photo to upload.'})
        return attrs
