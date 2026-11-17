from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ranking.views import staff_required

from .forms import CampCoverForm, GalleryUploadForm, TrainingForm
from .models import Photo, Training

# Galeria: każde zdjęcie wrzucone do tego folderu pojawia się na stronie, kolejność według nazwy pliku
GALLERY_DIR = settings.PUBLIC_DIR / 'images' / 'szkolenia'
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


GALLERY_ALT = 'Zdjęcie ze szkoleń i campów Training Culture'


def gallery_photos():
    """Najpierw zdjęcia z folderu, potem wgrane na stronie (w kolejności dodania)."""
    files = sorted(f.name for f in GALLERY_DIR.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS) if GALLERY_DIR.is_dir() else []
    photos = [{'src': f'/images/szkolenia/{quote(name)}', 'alt': GALLERY_ALT} for name in files]
    photos += [{'src': photo.image.url, 'alt': GALLERY_ALT} for photo in Photo.objects.filter(place=Photo.Place.GALLERY)]
    return photos


# Duży kafelek „Campy Training Culture”: pierwsze zdjęcie z tego folderu (dowolna nazwa pliku)
CAMP_PHOTO_DIR = settings.PUBLIC_DIR / 'images' / 'campy'


def camp_photo():
    # Zdjęcie wgrane na stronie ma pierwszeństwo przed plikiem z folderu
    cover = Photo.objects.filter(place=Photo.Place.CAMP_COVER).last()
    if cover:
        return cover.image.url
    if not CAMP_PHOTO_DIR.is_dir():
        return ''
    files = sorted(f.name for f in CAMP_PHOTO_DIR.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS)
    return f'/images/campy/{quote(files[0])}' if files else ''


def visible_trainings(request):
    # Obsługa widzi też ukryte wpisy — to podgląd przed publikacją
    trainings = Training.objects.all()
    if not request.user.is_staff:
        trainings = trainings.filter(is_active=True)
    return trainings


def training_list(request):
    trainings = list(visible_trainings(request))
    return render(request, 'trainings/list.html', {
        'courses': [t for t in trainings if t.kind == Training.Kind.COURSE],
        'camps': [t for t in trainings if t.kind == Training.Kind.CAMP],
        'gallery': gallery_photos(),
        'camp_photo': camp_photo(),
        'uploaded_photos': Photo.objects.filter(place=Photo.Place.GALLERY) if request.user.is_staff else [],
        'camp_cover': Photo.objects.filter(place=Photo.Place.CAMP_COVER).last() if request.user.is_staff else None,
        'gallery_form': GalleryUploadForm(),
        'cover_form': CampCoverForm(),
    })


def training_list_json(request):
    """Lista dla statycznej strony głównej (public/js/main.js)."""
    trainings = Training.objects.filter(is_active=True)
    return JsonResponse({'items': [
        {
            'kind': training.kind,
            'title': training.title,
            'icon': training.icon,
            'meta': training.meta,
            'badge': training.badge,
            'url': training.get_absolute_url(),
        }
        for training in trainings
    ]})


# ===== Dodawanie szkoleń i campów na stronie (konto admina) =====

@staff_required
def training_edit(request, pk=None):
    training = get_object_or_404(Training, pk=pk) if pk else None
    initial = {}
    if training is None and request.GET.get('rodzaj') == Training.Kind.CAMP:
        initial['kind'] = Training.Kind.CAMP

    if request.method == 'POST':
        form = TrainingForm(request.POST, request.FILES, instance=training)
        if form.is_valid():
            training = form.save()
            messages.success(request, f'Zapisano: {training.title}.')
            return redirect(training)
    else:
        form = TrainingForm(instance=training, initial=initial)

    return render(request, 'trainings/form.html', {'form': form, 'training': training})


@staff_required
@require_POST
def training_delete(request, pk):
    training = get_object_or_404(Training, pk=pk)
    image = training.image
    training.delete()
    if image:
        image.delete(save=False)
    messages.success(request, f'Usunięto: {training.title}.')
    return redirect('trainings:list')


# ===== Galeria i kafelek campów — wgrywanie na stronie (konto admina) =====

def upload_errors(request, form):
    for errors in form.errors.values():
        for error in errors:
            messages.error(request, error)


@staff_required
@require_POST
def gallery_upload(request):
    form = GalleryUploadForm(request.POST, request.FILES)
    if form.is_valid():
        added = form.save()
        messages.success(request, f'Dodano zdjęcia do galerii: {len(added)}.')
    else:
        upload_errors(request, form)
    return redirect(reverse('trainings:list') + '#galeria')


@staff_required
@require_POST
def camp_cover_upload(request):
    form = CampCoverForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, 'Zmieniono zdjęcie kafelka campów.')
    else:
        upload_errors(request, form)
    return redirect(reverse('trainings:list') + '#campy')


@staff_required
@require_POST
def photo_delete(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    anchor = '#campy' if photo.place == Photo.Place.CAMP_COVER else '#galeria'
    photo.delete()
    messages.success(request, 'Usunięto zdjęcie.')
    return redirect(reverse('trainings:list') + anchor)
