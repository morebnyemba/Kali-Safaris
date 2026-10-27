"""
Public, read-only views for tour packages.

The WhatsApp bot reads live tour data straight from the Tour and
SeasonalTourPrice models (see
flows/definitions/view_available_tours_flow.py). This module exposes the
same source of truth over HTTP so the marketing website's trip listing and
booking form always match what customers see on WhatsApp, instead of a
hardcoded list that can drift out of sync.
"""
import mimetypes
from datetime import date

from django.http import FileResponse, Http404, HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from rest_framework import permissions, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from .models import GalleryImage, Tour, resolve_tour_price
from .serializers import GalleryImageSerializer


def _serialize_tour(tour: Tour, today: date, request: HttpRequest) -> dict:
    price_per_adult, price_per_child = resolve_tour_price(tour, today)
    image_url = request.build_absolute_uri(tour.image.url) if tour.image else None

    return {
        'id': tour.id,
        'name': tour.name,
        'description': tour.description,
        'category': tour.category,
        'category_display': tour.get_category_display(),
        'location': tour.location,
        'base_price': str(tour.base_price),
        'price_per_adult': str(price_per_adult),
        'price_per_child': str(price_per_child) if price_per_child is not None else None,
        'duration_value': tour.duration_value,
        'duration_unit': tour.duration_unit,
        'duration_days': tour.duration_days,
        'duration_display': tour.get_duration_display_text(),
        'image_url': image_url,
    }


@require_http_methods(["GET"])
def public_tours_list_view(request: HttpRequest) -> JsonResponse:
    """
    GET /crm-api/tours/

    Public list of active tour packages, with the same seasonal pricing
    resolution the WhatsApp "View Available Tours" flow uses. No
    authentication required — this is marketing/booking data, not customer
    data.
    """
    today = date.today()
    tours = Tour.objects.filter(is_active=True).order_by('name')
    data = [_serialize_tour(tour, today, request) for tour in tours]

    return JsonResponse({'success': True, 'count': len(data), 'tours': data})


@require_http_methods(["GET"])
def public_gallery_list_view(request: HttpRequest) -> JsonResponse:
    """
    GET /crm-api/gallery/

    Public list of the photos shown on the website gallery, in display order.
    """
    images = GalleryImage.objects.filter(is_active=True).exclude(image='')
    data = [
        {
            'id': image.id,
            'url': image.file_path(),
            'category': image.category,
            'category_display': image.get_category_display(),
            'caption': image.caption,
            'year': image.year,
        }
        for image in images
    ]
    return JsonResponse({'success': True, 'count': len(data), 'images': data})


@require_http_methods(["GET", "HEAD"])
def public_gallery_image_view(request: HttpRequest, pk: int, version: int) -> FileResponse:
    """GET /crm-api/gallery/<pk>/<version>/ — the photo file itself."""
    # Hidden photos are unpublished, not private: they still load here so the
    # admin and the CRM dashboard (which can't send its login with an <img>)
    # can preview them. Only the list above decides what the website shows.
    image = get_object_or_404(GalleryImage, pk=pk)
    if not image.image:
        raise Http404
    try:
        file = image.image.open('rb')
    except FileNotFoundError:
        raise Http404
    response = FileResponse(file, content_type=mimetypes.guess_type(image.image.name)[0] or 'application/octet-stream')
    response['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response


class GalleryImageViewSet(viewsets.ModelViewSet):
    """
    /crm-api/gallery/manage/ — the CRM dashboard's gallery manager: list,
    upload, edit (caption, year, category, order, visibility, replace photo)
    and delete. Deleting also removes the file (see signals.py).
    """
    serializer_class = GalleryImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = None  # A gallery is a few dozen photos; the page shows them all.

    def get_queryset(self):
        queryset = GalleryImage.objects.all()
        category = self.request.query_params.get('category')
        if category in GalleryImage.Category.values:
            queryset = queryset.filter(category=category)
        return queryset
