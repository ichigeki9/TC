import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.utils import timezone

from .models import Result, Workout

TIME_RE = re.compile(r'^(?:(\d+):)?(\d{1,2}):(\d{2})$')


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
        self.fields['score'].widget.attrs['placeholder'] = workout.unit_hint
        if workout.score_type != Workout.ScoreType.TIME:
            self.fields['score'].widget.attrs['inputmode'] = 'decimal'

    def clean_score(self):
        raw = self.cleaned_data['score'].strip().replace(',', '.')

        if self.workout.score_type == Workout.ScoreType.TIME:
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
            if self.workout.score_type == Workout.ScoreType.REPS and value != value.to_integral_value():
                raise forms.ValidationError('Liczba powtórzeń musi być całkowita.')

        if value <= 0 or value >= Decimal('10000000'):
            raise forms.ValidationError('Wynik poza zakresem.')
        return value

    def clean_performed_on(self):
        performed_on = self.cleaned_data['performed_on']
        if performed_on > timezone.localdate():
            raise forms.ValidationError('Data nie może być z przyszłości.')
        return performed_on

    def save(self, commit=True):
        self.instance.value = self.cleaned_data['score']
        self.instance.workout = self.workout
        return super().save(commit)
