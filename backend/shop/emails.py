from django.conf import settings
from django.urls import reverse

from config.emails import send_email


def send_order_email(request, order, kind):
    """Mail do klienta: kind to 'placed', 'paid' albo 'shipped' (szablony emails/order_<kind>.txt)."""
    # Gość widzi zamówienie tylko w przeglądarce, w której je złożył — link dostaje tylko klient z kontem
    url = request.build_absolute_uri(order.get_absolute_url()) if order.user_id else ''
    send_email(f'order_{kind}', {'order': order, 'url': url}, [order.email])

    if kind == 'paid' and settings.SHOP_NOTIFY_EMAIL:
        admin_url = request.build_absolute_uri(reverse('admin:shop_order_change', args=[order.pk]))
        send_email('order_notify', {'order': order, 'url': admin_url}, [settings.SHOP_NOTIFY_EMAIL])
