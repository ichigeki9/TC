from decimal import Decimal

from .models import Product

SESSION_KEY = 'cart'
MAX_QUANTITY = 20


class Cart:
    """Koszyk w sesji: {'<id produktu>:<rozmiar>': ilość}. Działa też bez logowania."""

    def __init__(self, request):
        self.session = request.session
        self.data = dict(self.session.get(SESSION_KEY, {}))

    @staticmethod
    def make_key(product, size=''):
        return f'{product.pk}:{size}'

    def _save(self):
        self.session[SESSION_KEY] = self.data

    def add(self, product, size='', quantity=1):
        key = self.make_key(product, size)
        self.data[key] = min(self.data.get(key, 0) + quantity, MAX_QUANTITY)
        self._save()

    def set_quantity(self, key, quantity):
        if key not in self.data:
            return
        if quantity <= 0:
            del self.data[key]
        else:
            self.data[key] = min(quantity, MAX_QUANTITY)
        self._save()

    def clear(self):
        self.data = {}
        self.session.pop(SESSION_KEY, None)

    @property
    def count(self):
        return sum(self.data.values())

    def lines(self):
        """Pozycje koszyka z aktualnymi cenami; produkty usunięte lub ukryte wypadają."""
        ids = {key.split(':', 1)[0] for key in self.data}
        products = {str(p.pk): p for p in Product.objects.filter(pk__in=ids, is_active=True).select_related('category')}

        lines = []
        for key, quantity in self.data.items():
            product_id, size = key.split(':', 1)
            product = products.get(product_id)
            if not product:
                continue
            lines.append({
                'key': key,
                'product': product,
                'size': size,
                'quantity': quantity,
                'unit_price': product.current_price,
                'total': product.current_price * Decimal(quantity),
            })
        return lines

    @staticmethod
    def total(lines):
        return sum((line['total'] for line in lines), Decimal('0'))
