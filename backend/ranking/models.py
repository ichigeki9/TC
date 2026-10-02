from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


def format_seconds(value):
    total = int(value)
    hours, rest = divmod(total, 3600)
    minutes, seconds = divmod(rest, 60)
    if hours:
        return f'{hours}:{minutes:02d}:{seconds:02d}'
    return f'{minutes}:{seconds:02d}'


class Workout(models.Model):
    """Trening testowy z własnym rankingiem, np. „Hyrox Sim” albo „Max Deadlift”."""

    class ScoreType(models.TextChoices):
        TIME = 'time', 'Czas (mniej = lepiej)'
        REPS = 'reps', 'Powtórzenia (więcej = lepiej)'
        WEIGHT = 'weight', 'Ciężar w kg (więcej = lepiej)'

    program = models.CharField('program', max_length=60, help_text='Np. CrossFit, Hyrox, Trening Siłowy.')
    name = models.CharField('nazwa', max_length=120)
    slug = models.SlugField('adres', unique=True, help_text='Część adresu strony, np. hyrox-sim.')
    description = models.TextField('opis', blank=True, help_text='Na czym polega trening, standardy ruchów.')
    score_type = models.CharField('typ wyniku', max_length=10, choices=ScoreType.choices)
    is_active = models.BooleanField('aktywny', default=True, help_text='Nieaktywne treningi są ukryte.')
    order = models.PositiveIntegerField('kolejność', default=0)

    class Meta:
        ordering = ('program', 'order', 'name')
        verbose_name = 'trening'
        verbose_name_plural = 'treningi'

    def __str__(self):
        return f'{self.program}: {self.name}'

    def get_absolute_url(self):
        return reverse('ranking:detail', args=[self.slug])

    @property
    def lower_is_better(self):
        return self.score_type == self.ScoreType.TIME

    @property
    def unit_hint(self):
        return {
            self.ScoreType.TIME: 'mm:ss lub h:mm:ss',
            self.ScoreType.REPS: 'liczba powtórzeń',
            self.ScoreType.WEIGHT: 'kg',
        }[self.score_type]

    def format_value(self, value):
        if self.score_type == self.ScoreType.TIME:
            return format_seconds(value)
        if self.score_type == self.ScoreType.WEIGHT:
            return f'{Decimal(value).normalize():f} kg'
        return f'{int(value)}'


class Result(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='results', verbose_name='trening')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='results', verbose_name='zawodnik')
    # Czas w sekundach, powtórzenia albo kg
    value = models.DecimalField('wynik', max_digits=9, decimal_places=2)
    performed_on = models.DateField('data', default=timezone.localdate)
    note = models.CharField('notatka', max_length=200, blank=True)
    created_at = models.DateTimeField('dodano', auto_now_add=True)

    class Meta:
        ordering = ('-performed_on', '-created_at')
        verbose_name = 'wynik'
        verbose_name_plural = 'wyniki'

    def __str__(self):
        return f'{self.user} — {self.workout.name}: {self.display_value}'

    @property
    def display_value(self):
        return self.workout.format_value(self.value)
