from urllib.parse import quote

from django.db import models
from django.urls import reverse

CONTACT_EMAIL = 'info@trainingculture.pl'


class Training(models.Model):
    """Szkolenie albo camp pokazywany na /szkolenia/ i na stronie głównej."""

    class Kind(models.TextChoices):
        COURSE = 'course', 'Szkolenie'
        CAMP = 'camp', 'Camp'

    kind = models.CharField('rodzaj', max_length=10, choices=Kind.choices, default=Kind.COURSE)
    title = models.CharField('tytuł', max_length=120)
    slug = models.SlugField('adres', unique=True, help_text='Kotwica na stronie, np. trener-personalny.')
    icon = models.CharField('ikona', max_length=8, blank=True, help_text='Jedna emotka, np. 🏋️‍♂️.')
    meta = models.CharField(
        'krótka informacja', max_length=160, blank=True,
        help_text='Jedna linia pod tytułem, np. „12 tygodni · Online + Praktyki”.',
    )
    badge = models.CharField('etykieta', max_length=20, blank=True, help_text='Np. Nowość, Bestseller.')
    description = models.TextField('opis', blank=True)
    points = models.TextField('punkty', blank=True, help_text='Lista „co dostajesz” — każdy punkt w osobnej linii.')
    date_text = models.CharField('termin', max_length=80, blank=True, help_text='Np. 12–14 czerwca 2026.')
    place = models.CharField('miejsce', max_length=120, blank=True)
    price = models.DecimalField('cena (zł)', max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.ImageField('zdjęcie', upload_to='szkolenia/', max_length=255, blank=True)
    is_active = models.BooleanField(
        'widoczne', default=True,
        help_text='Odznacz, żeby ukryć wpis. Ukryty wpis widzisz na stronie tylko Ty (podgląd).',
    )
    order = models.PositiveIntegerField('kolejność', default=0)

    class Meta:
        ordering = ('order', 'title')
        verbose_name = 'szkolenie / camp'
        verbose_name_plural = 'szkolenia i campy'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"{reverse('trainings:list')}#{self.slug}"

    @property
    def point_list(self):
        return [line.strip() for line in self.points.splitlines() if line.strip()]

    @property
    def details(self):
        """Termin, miejsce i cena jako gotowe pary do wyświetlenia."""
        price = f'{self.price.normalize():f} zł' if self.price is not None else ''
        return [(label, value) for label, value in (('Termin', self.date_text), ('Miejsce', self.place), ('Cena', price)) if value]

    @property
    def contact_url(self):
        return f'mailto:{CONTACT_EMAIL}?subject={quote(f"{self.get_kind_display()}: {self.title}")}'
