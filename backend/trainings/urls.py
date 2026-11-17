from django.urls import path

from . import views

app_name = 'trainings'

urlpatterns = [
    path('', views.training_list, name='list'),
    path('lista.json', views.training_list_json, name='list_json'),
    path('nowy/', views.training_edit, name='add'),
    path('<int:pk>/edytuj/', views.training_edit, name='edit'),
    path('<int:pk>/usun/', views.training_delete, name='delete'),
    path('galeria/dodaj/', views.gallery_upload, name='gallery_upload'),
    path('campy/zdjecie/', views.camp_cover_upload, name='camp_cover_upload'),
    path('zdjecie/<int:pk>/usun/', views.photo_delete, name='photo_delete'),
]
