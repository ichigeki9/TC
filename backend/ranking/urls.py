from django.urls import path

from . import views

app_name = 'ranking'

urlpatterns = [
    path('', views.workout_list, name='list'),
    path('wynik/<int:pk>/usun/', views.delete_result, name='delete_result'),
    path('<slug:slug>/', views.workout_detail, name='detail'),
]
