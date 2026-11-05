from django.conf import settings
from django.shortcuts import render

SHOP_PREFIX = '/sklep/'


class ShopClosedMiddleware:
    """Gdy SHOP_OPEN jest wyłączone, cały /sklep/ pokazuje stronę „w trakcie budowy”.
    Obsługa (staff) widzi sklep normalnie, żeby móc go przygotować."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            not settings.SHOP_OPEN
            and request.path.startswith(SHOP_PREFIX)
            and not request.user.is_staff
        ):
            return render(request, 'shop/coming_soon.html')
        return self.get_response(request)
