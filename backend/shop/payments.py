"""
Bramki płatności.

Każda bramka ma metodę start(order), która zwraca adres, pod który wysyłamy klienta,
żeby zapłacił. Po udanej płatności bramka woła order.mark_paid(identyfikator).

Na razie jest tylko DummyProvider — ekran „Płatność testowa” bez prawdziwych pieniędzy.
Prawdziwą bramkę (Przelewy24, PayU, Stripe…) dodaje się jako kolejną klasę w PROVIDERS
i wybiera zmienną środowiskową PAYMENT_PROVIDER.
"""
from django.conf import settings
from django.urls import reverse


class DummyProvider:
    name = 'dummy'
    is_test = True

    def start(self, order):
        return reverse('shop:payment_dummy', args=[order.token])


PROVIDERS = {provider.name: provider for provider in (DummyProvider,)}


def get_provider():
    return PROVIDERS[settings.PAYMENT_PROVIDER]()
