"""
Public, read-only views for tour packages.

The WhatsApp bot reads live tour data straight from the Tour and
SeasonalTourPrice models (see
flows/definitions/view_available_tours_flow.py). This module exposes the
same source of truth over HTTP so the marketing website's trip listing and
booking form always match what customers see on WhatsApp, instead of a
hardcoded list that can drift out of sync.
"""
from datetime import date

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from .models import SeasonalTourPrice, Tour


def _resolve_display_price(tour: Tour, today: date):
    """Mirrors the seasonal price resolution used by the WhatsApp tour flow."""
    seasonal = (
        SeasonalTourPrice.objects.filter(
            tour=tour,
            start_date__lte=today,
            end_date__gte=today,
            is_active=True,
        )
        .order_by('-start_date')
        .first()
    )
    if seasonal and seasonal.price_per_adult is not None:
        return seasonal.price_per_adult, seasonal.price_per_child
    return tour.base_price, None


def _serialize_tour(tour: Tour, today: date, request: HttpRequest) -> dict:
    price_per_adult, price_per_child = _resolve_display_price(tour, today)
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
