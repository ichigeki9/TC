from django.urls import path

from . import views

app_name = 'trainings'

urlpatterns = [
    path('', views.training_list, name='list'),
    path('lista.json', views.training_list_json, name='list_json'),
]
