from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

admin.site.site_header = 'Training Culture — panel'
admin.site.site_title = 'Training Culture'

# Statyczną stronę (/, /css/…, /js/…) serwuje WhiteNoise z katalogu public/
urlpatterns = [
    path('admin/', admin.site.urls),
    path('konto/', include('accounts.urls')),
    path('ranking/', include('ranking.urls')),
    path('sklep/', include('shop.urls')),
    path('szkolenia/', include('trainings.urls')),
    # Stary adres statycznej strony szkoleń
    path('szkolenia.html', RedirectView.as_view(pattern_name='trainings:list', permanent=True)),
    # Zdjęcia wgrane w panelu — WhiteNoise nie widzi plików dodanych po starcie serwera
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
