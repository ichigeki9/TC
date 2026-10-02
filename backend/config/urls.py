from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Training Culture — panel'
admin.site.site_title = 'Training Culture'

# Statyczną stronę (/, /szkolenia.html, /css/…) serwuje WhiteNoise z katalogu public/
urlpatterns = [
    path('admin/', admin.site.urls),
    path('konto/', include('accounts.urls')),
    path('ranking/', include('ranking.urls')),
    path('sklep/', include('shop.urls')),
]
