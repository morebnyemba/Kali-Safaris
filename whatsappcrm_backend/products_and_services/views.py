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
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models import GalleryImage, Tour, resolve_tour_price


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


def gallery_image_url(image: GalleryImage) -> str:
    """
    Site-relative URL that streams the photo through this backend. The website
    proxies /crm-api/ to us, so photos load without separate media hosting. The
    version segment changes whenever the entry is saved, so the URL can be
    cached for a long time and still pick up a replaced photo. No trailing
    slash: the website redirects those away, and its proxy adds it back.
    """
    return reverse('gallery_api:gallery_image_file', args=[image.pk, int(image.updated_at.timestamp())]).rstrip('/')


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
            'url': gallery_image_url(image),
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
    image = get_object_or_404(GalleryImage, pk=pk)
    # Hidden photos stay viewable to staff so the admin can still preview them.
    if not image.image or not (image.is_active or request.user.is_staff):
        raise Http404
    try:
        file = image.image.open('rb')
    except FileNotFoundError:
        raise Http404
    response = FileResponse(file, content_type=mimetypes.guess_type(image.image.name)[0] or 'application/octet-stream')
    response['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response
