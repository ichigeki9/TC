import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.utils import timezone

from .models import DailyWorkout, PartResult, Result, ScoreType, WorkoutPart

TIME_RE = re.compile(r'^(?:(\d+):)?(\d{1,2}):(\d{2})$')


def parse_score(score_type, raw):
    """Zamienia wpisany tekst na liczbę: sekundy, powtórzenia albo kg."""
    raw = raw.strip().replace(',', '.')

    if score_type == ScoreType.TIME:
        match = TIME_RE.match(raw)
        if not match:
            raise forms.ValidationError('Podaj czas w formacie mm:ss lub h:mm:ss, np. 12:34.')
        hours, minutes, seconds = (int(part or 0) for part in match.groups())
        if seconds >= 60 or (hours and minutes >= 60):
            raise forms.ValidationError('Nieprawidłowy czas.')
        value = Decimal(hours * 3600 + minutes * 60 + seconds)
    else:
        try:
            value = Decimal(raw)
        except InvalidOperation:
            raise forms.ValidationError('Podaj liczbę.')
        if not value.is_finite():
            raise forms.ValidationError('Podaj liczbę.')
        if score_type == ScoreType.REPS and value != value.to_integral_value():
            raise forms.ValidationError('Liczba powtórzeń musi być całkowita.')

    if value <= 0 or value >= Decimal('10000000'):
        raise forms.ValidationError('Wynik poza zakresem.')
    return value


def score_widget_attrs(field, scored):
    field.widget.attrs['placeholder'] = scored.unit_hint
    if scored.score_type != ScoreType.TIME:
        field.widget.attrs['inputmode'] = 'decimal'


class ResultForm(forms.ModelForm):
    score = forms.CharField(label='Wynik', max_length=20)

    class Meta:
        model = Result
        fields = ('performed_on', 'note')
        widgets = {
            'performed_on': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, workout, **kwargs):
        super().__init__(*args, **kwargs)
        self.workout = workout
        score_widget_attrs(self.fields['score'], workout)

    def clean_score(self):
        return parse_score(self.workout.score_type, self.cleaned_data['score'])

    def clean_performed_on(self):
        performed_on = self.cleaned_data['performed_on']
        if performed_on > timezone.localdate():
            raise forms.ValidationError('Data nie może być z przyszłości.')
        return performed_on

    def save(self, commit=True):
        self.instance.value = self.cleaned_data['score']
        self.instance.workout = self.workout
        return super().save(commit)


class PartResultForm(forms.ModelForm):
    """Wynik w części treningu dnia. Ponowne wysłanie poprawia poprzedni wynik."""

    score = forms.CharField(label='Wynik', max_length=20)

    class Meta:
        model = PartResult
        fields = ('note',)

    def __init__(self, *args, part, **kwargs):
        super().__init__(*args, **kwargs)
        self.part = part
        score_widget_attrs(self.fields['score'], part)
        if self.instance.pk and not self.is_bound:
            self.initial['score'] = self.instance.display_value.removesuffix(' kg')

    def clean_score(self):
        return parse_score(self.part.score_type, self.cleaned_data['score'])

    def save(self, commit=True):
        self.instance.value = self.cleaned_data['score']
        self.instance.part = self.part
        return super().save(commit)


# ===== Dodawanie treningów dnia na stronie (konto admina) =====

DEFAULT_PART_COUNT = 5


class DailyWorkoutForm(forms.ModelForm):
    class Meta:
        model = DailyWorkout
        fields = ('date', 'title', 'description', 'is_published')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class WorkoutPartForm(forms.ModelForm):
    class Meta:
        model = WorkoutPart
        fields = ('name', 'score_type', 'description')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_results = bool(self.instance.pk) and self.instance.results.exists()
        if self.has_results:
            # Zmiana typu przekręciłaby wpisane już wyniki (np. kg czytane jako sekundy)
            self.fields['score_type'].disabled = True
            self.fields['score_type'].help_text = 'Nie można zmienić — są już wyniki.'


class BaseWorkoutPartFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        kept = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get('DELETE')]
        if not kept:
            raise forms.ValidationError('Dodaj przynajmniej jedną część treningu.')

    def save(self, commit=True):
        # Nowe części trafiają na koniec, istniejące zachowują kolejność
        start = max((form.instance.order for form in self.initial_forms), default=-1) + 1
        for index, form in enumerate(self.extra_forms):
            form.instance.order = start + index
        return super().save(commit)


def part_formset(data=None, instance=None):
    existing = instance.parts.count() if instance and instance.pk else 0
    FormSet = forms.inlineformset_factory(
        DailyWorkout, WorkoutPart,
        form=WorkoutPartForm, formset=BaseWorkoutPartFormSet,
        extra=max(DEFAULT_PART_COUNT - existing, 1), can_delete=True,
    )
    return FormSet(data, instance=instance, prefix='czesci')
