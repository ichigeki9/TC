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


class ScoreType(models.TextChoices):
    TIME = 'time', 'Czas (mniej = lepiej)'
    REPS = 'reps', 'Powtórzenia (więcej = lepiej)'
    WEIGHT = 'weight', 'Ciężar w kg (więcej = lepiej)'


SCORE_HINTS = {
    ScoreType.TIME: 'mm:ss lub h:mm:ss',
    ScoreType.REPS: 'liczba powtórzeń',
    ScoreType.WEIGHT: 'kg',
}


def format_score(score_type, value):
    if score_type == ScoreType.TIME:
        return format_seconds(value)
    if score_type == ScoreType.WEIGHT:
        return f'{Decimal(value).normalize():f} kg'
    return f'{int(value)}'


class ScoredMixin:
    """Wspólne dla wszystkiego, co ma pole score_type."""

    @property
    def lower_is_better(self):
        return self.score_type == ScoreType.TIME

    @property
    def unit_hint(self):
        return SCORE_HINTS[self.score_type]

    def format_value(self, value):
        return format_score(self.score_type, value)


class Workout(ScoredMixin, models.Model):
    """Trening testowy z własnym rankingiem, np. „Hyrox Sim” albo „Max Deadlift”."""

    ScoreType = ScoreType

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


class Exercise(models.Model):
    """Jedno ćwiczenie w treningu, np. „Wall balls — 50 powtórzeń, 9 kg”."""

    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='exercises', verbose_name='trening')
    name = models.CharField('ćwiczenie', max_length=120)
    details = models.CharField(
        'ile / jak', max_length=160, blank=True,
        help_text='Np. 50 powtórzeń, 1 km, 5 × 100 kg, 2 min przerwy.',
    )
    order = models.PositiveIntegerField('kolejność', default=0)

    class Meta:
        ordering = ('order', 'pk')
        verbose_name = 'ćwiczenie'
        verbose_name_plural = 'ćwiczenia'

    def __str__(self):
        return f'{self.name} — {self.details}' if self.details else self.name


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


class DailyWorkoutQuerySet(models.QuerySet):
    def visible(self):
        """Opublikowane i nie z przyszłości — admin może dodawać treningi z wyprzedzeniem."""
        return self.filter(is_published=True, date__lte=timezone.localdate())


class DailyWorkout(models.Model):
    """Trening dnia złożony z kilku części; każda część ma osobny ranking."""

    date = models.DateField('dzień', unique=True)
    title = models.CharField('tytuł', max_length=120, blank=True, help_text='Opcjonalnie, np. „Siła + kondycja”.')
    description = models.TextField('opis', blank=True, help_text='Rozgrzewka, uwagi do całego treningu.')
    is_published = models.BooleanField('opublikowany', default=True, help_text='Nieopublikowane są ukryte.')

    objects = DailyWorkoutQuerySet.as_manager()

    class Meta:
        ordering = ('-date',)
        verbose_name = 'trening dnia'
        verbose_name_plural = 'treningi dnia'

    def __str__(self):
        return f'{self.date:%d.%m.%Y}' + (f' — {self.title}' if self.title else '')

    def get_absolute_url(self):
        return reverse('ranking:day', args=[self.date.isoformat()])


class WorkoutPart(ScoredMixin, models.Model):
    """Część treningu dnia, np. „A. Back squat 5×5” z wynikiem w kg."""

    daily = models.ForeignKey(DailyWorkout, on_delete=models.CASCADE, related_name='parts', verbose_name='trening dnia')
    name = models.CharField('nazwa', max_length=120, help_text='Np. Back squat, Metcon, Bieg 5 km.')
    description = models.TextField('opis', blank=True, help_text='Co dokładnie zrobić, np. „5 rund: 10 burpees, 15 KB swings”.')
    score_type = models.CharField('typ wyniku', max_length=10, choices=ScoreType.choices)
    order = models.PositiveIntegerField('kolejność', default=0)

    class Meta:
        ordering = ('order', 'pk')
        verbose_name = 'część treningu'
        verbose_name_plural = 'części treningu'

    def __str__(self):
        return f'{self.daily.date:%d.%m.%Y}: {self.name}'


class PartResult(models.Model):
    """Wynik zawodnika w jednej części — jeden na osobę, można go poprawić."""

    part = models.ForeignKey(WorkoutPart, on_delete=models.CASCADE, related_name='results', verbose_name='część')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='part_results', verbose_name='zawodnik')
    # Czas w sekundach, powtórzenia albo kg
    value = models.DecimalField('wynik', max_digits=9, decimal_places=2)
    note = models.CharField('notatka', max_length=200, blank=True)
    created_at = models.DateTimeField('dodano', auto_now_add=True)
    updated_at = models.DateTimeField('zmieniono', auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        constraints = [models.UniqueConstraint(fields=('part', 'user'), name='one_result_per_part')]
        verbose_name = 'wynik części'
        verbose_name_plural = 'wyniki części'

    def __str__(self):
        return f'{self.user} — {self.part}: {self.display_value}'

    @property
    def display_value(self):
        return self.part.format_value(self.value)
