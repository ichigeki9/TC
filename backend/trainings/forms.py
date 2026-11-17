from django import forms
from django.utils.text import slugify

from .models import Photo, Training

# slugify gubi litery, które nie mają wersji bez ogonka (ł → ''), więc zamieniamy je ręcznie
POLISH = str.maketrans('łŁ', 'lL')


def unique_slug(title, instance=None):
    base = slugify(title.translate(POLISH))[:40].strip('-') or 'wpis'
    others = Training.objects.exclude(pk=instance.pk) if instance and instance.pk else Training.objects.all()
    slug, number = base, 2
    while others.filter(slug=slug).exists():
        slug, number = f'{base}-{number}', number + 1
    return slug


class TrainingForm(forms.ModelForm):
    """Dodawanie i edycja szkolenia / campu na stronie (konto admina)."""

    remove_image = forms.BooleanField(label='Usuń obecne zdjęcie', required=False)

    class Meta:
        model = Training
        fields = (
            'kind', 'title', 'description', 'image',
            'date_text', 'place', 'price', 'meta', 'badge', 'icon', 'points',
            'is_active', 'order',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'points': forms.Textarea(attrs={'rows': 4}),
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.image:
            self.fields['image'].label = 'Nowe zdjęcie'
            self.fields['image'].help_text = 'Zostaw puste, żeby zachować obecne.'

    def save(self, commit=True):
        old_image = self.initial.get('image')
        new_upload = 'image' in self.files
        if self.cleaned_data.get('remove_image') and not new_upload:
            self.instance.image = None
        # Adres (kotwicę) tworzymy z tytułu tylko przy dodawaniu — zmiana psułaby stare linki
        if not self.instance.slug:
            self.instance.slug = unique_slug(self.instance.title, self.instance)
        training = super().save(commit)
        # Stary plik kasujemy dopiero po zapisie — zastąpiony albo usunięty nie wisi w media/
        if commit and old_image and old_image != training.image:
            old_image.storage.delete(old_image.name)
        return training


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """Kilka zdjęć z jednego pola — każde sprawdzane jak zwykłe ImageField."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput(attrs={'accept': 'image/*'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        files = [f for f in files if f]
        if not files:
            raise forms.ValidationError('Wybierz przynajmniej jedno zdjęcie.')
        return [super(MultipleImageField, self).clean(f, initial) for f in files]


class GalleryUploadForm(forms.Form):
    images = MultipleImageField(label='Zdjęcia do galerii')

    def save(self):
        return [Photo.objects.create(place=Photo.Place.GALLERY, image=f) for f in self.cleaned_data['images']]


class CampCoverForm(forms.Form):
    image = forms.ImageField(label='Zdjęcie kafelka campów', widget=forms.FileInput(attrs={'accept': 'image/*'}))

    def save(self):
        # Jedno zdjęcie kafelka — poprzednie (i jego plik) usuwamy
        for old in Photo.objects.filter(place=Photo.Place.CAMP_COVER):
            old.delete()
        return Photo.objects.create(place=Photo.Place.CAMP_COVER, image=self.cleaned_data['image'])
