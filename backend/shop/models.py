from django.db import models
from django.urls import reverse


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
    """Produkt w katalogu. Sam zakup odbywa się w sklepie Shoper (buy_url)."""

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='kategoria')
    name = models.CharField('nazwa', max_length=120)
    slug = models.SlugField('adres', unique=True)
    description = models.TextField('opis', blank=True)
    price = models.DecimalField('cena (zł)', max_digits=8, decimal_places=2)
    sale_price = models.DecimalField('cena promocyjna (zł)', max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.CharField(
        'zdjęcie', max_length=500, blank=True,
        help_text='Adres zdjęcia (np. skopiowany z produktu w Shoperze) albo plik z public/images/sklep/, '
                  'np. /images/sklep/buty.jpg',
    )
    sizes = models.CharField('rozmiary', max_length=200, blank=True, help_text='Po przecinku, np. S, M, L, XL albo 40, 41, 42.')
    badge = models.CharField('etykieta', max_length=20, blank=True, help_text='Np. Nowość, Bestseller.')
    buy_url = models.URLField('link do zakupu', blank=True, help_text='Adres tego produktu w sklepie Shoper.')
    is_active = models.BooleanField('widoczny', default=True)
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
