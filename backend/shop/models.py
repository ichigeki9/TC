import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    name = models.CharField('nazwa', max_length=60)
    slug = models.SlugField('adres', unique=True)
    order = models.PositiveIntegerField('kolejność', default=0)

    class Meta:
        ordering = ('order', 'name')
        verbose_name = 'kategoria'
        verbose_name_plural = 'kategorie'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Produkt w sklepie. Kupowany przez koszyk (cart.py) i zamówienie (Order)."""

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='kategoria')
    name = models.CharField('nazwa', max_length=120)
    slug = models.SlugField('adres', unique=True)
    description = models.TextField('opis', blank=True)
    price = models.DecimalField('cena (zł)', max_digits=8, decimal_places=2)
    sale_price = models.DecimalField('cena promocyjna (zł)', max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.ImageField(
        'zdjęcie', upload_to='sklep/', max_length=255, blank=True,
        help_text='Najlepiej kwadratowe, min. 800 × 800 px.',
    )
    sizes = models.CharField('rozmiary', max_length=200, blank=True, help_text='Po przecinku, np. S, M, L, XL albo 40, 41, 42.')
    badge = models.CharField('etykieta', max_length=20, blank=True, help_text='Np. Nowość, Bestseller.')
    is_active = models.BooleanField(
        'widoczny', default=True,
        help_text='Odznacz, żeby ukryć produkt przed klientami. Ukryty produkt możesz obejrzeć przyciskiem „Pokaż na stronie”.',
    )
    order = models.PositiveIntegerField('kolejność', default=0)

    class Meta:
        ordering = ('order', 'name')
        verbose_name = 'produkt'
        verbose_name_plural = 'produkty'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:detail', args=[self.slug])

    @property
    def size_list(self):
        return [size.strip() for size in self.sizes.split(',') if size.strip()]

    @property
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def current_price(self):
        return self.sale_price if self.is_on_sale else self.price


class ShippingMethod(models.Model):
    name = models.CharField('nazwa', max_length=80)
    price = models.DecimalField('cena (zł)', max_digits=8, decimal_places=2)
    is_active = models.BooleanField('aktywna', default=True)
    order = models.PositiveIntegerField('kolejność', default=0)

    class Meta:
        ordering = ('order', 'name')
        verbose_name = 'sposób dostawy'
        verbose_name_plural = 'sposoby dostawy'

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Czeka na płatność'
        PAID = 'paid', 'Opłacone'
        SHIPPED = 'shipped', 'Wysłane'
        CANCELLED = 'cancelled', 'Anulowane'

    # Losowy identyfikator w adresach, żeby nie dało się zgadywać cudzych zamówień
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # Puste = zakup bez konta (jako gość)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name='orders', verbose_name='konto klienta',
    )
    status = models.CharField('status', max_length=10, choices=Status.choices, default=Status.NEW)

    full_name = models.CharField('imię i nazwisko', max_length=120)
    email = models.EmailField('e-mail')
    phone = models.CharField('telefon', max_length=20)
    street = models.CharField('ulica i numer', max_length=160)
    postal_code = models.CharField('kod pocztowy', max_length=6)
    city = models.CharField('miejscowość', max_length=80)
    note = models.CharField('uwagi do zamówienia', max_length=300, blank=True)

    shipping_name = models.CharField('dostawa', max_length=80)
    shipping_price = models.DecimalField('koszt dostawy (zł)', max_digits=8, decimal_places=2)
    total = models.DecimalField('suma (zł)', max_digits=10, decimal_places=2)

    payment_provider = models.CharField('bramka płatności', max_length=20, blank=True)
    payment_id = models.CharField('identyfikator płatności', max_length=100, blank=True)
    created_at = models.DateTimeField('złożono', auto_now_add=True)
    paid_at = models.DateTimeField('opłacono', null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'zamówienie'
        verbose_name_plural = 'zamówienia'

    def __str__(self):
        return self.number

    def get_absolute_url(self):
        return reverse('shop:order_detail', args=[self.token])

    @property
    def number(self):
        return f'TC-{self.pk:05d}'

    @property
    def items_total(self):
        return self.total - self.shipping_price

    @property
    def is_awaiting_payment(self):
        return self.status == self.Status.NEW

    def mark_paid(self, payment_id=''):
        self.status = self.Status.PAID
        self.payment_id = payment_id
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'payment_id', 'paid_at'])

    def cancel(self):
        self.status = self.Status.CANCELLED
        self.save(update_fields=['status'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='zamówienie')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='+', verbose_name='produkt')
    # Kopie z chwili zakupu — późniejsza zmiana produktu nie zmienia zamówienia
    name = models.CharField('nazwa', max_length=120)
    size = models.CharField('rozmiar', max_length=20, blank=True)
    unit_price = models.DecimalField('cena (zł)', max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField('ilość')

    class Meta:
        verbose_name = 'pozycja'
        verbose_name_plural = 'pozycje'

    def __str__(self):
        return f'{self.quantity} × {self.name}'

    @property
    def total(self):
        return self.unit_price * Decimal(self.quantity)
