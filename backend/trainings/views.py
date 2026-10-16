from urllib.parse import quote

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from .models import Training

# Galeria: każde zdjęcie wrzucone do tego folderu pojawia się na stronie, kolejność według nazwy pliku
GALLERY_DIR = settings.PUBLIC_DIR / 'images' / 'szkolenia'
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


def gallery_photos():
    if not GALLERY_DIR.is_dir():
        return []
    files = sorted(f.name for f in GALLERY_DIR.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS)
    return [
        {'src': f'/images/szkolenia/{quote(name)}', 'alt': 'Zdjęcie ze szkoleń i campów Training Culture'}
        for name in files
    ]


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
