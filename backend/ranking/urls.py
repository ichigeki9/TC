from django.urls import path

from . import views

app_name = 'ranking'

urlpatterns = [
    path('', views.workout_list, name='list'),
    path('wynik/<int:pk>/usun/', views.delete_result, name='delete_result'),
    path('tygodnie/', views.earlier_weeks, name='weeks'),
    path('tydzien/<str:start>/', views.week_days, name='week'),
    path('dzien/<str:day>/', views.day_detail, name='day'),
    path('trening/nowy/', views.daily_edit, name='daily_add'),
    path('trening/<str:day>/edytuj/', views.daily_edit, name='daily_edit'),
    path('trening/<str:day>/usun/', views.daily_delete, name='daily_delete'),
    path('dzien/wynik/<int:pk>/usun/', views.delete_part_result, name='delete_part_result'),
    path('<slug:slug>/', views.workout_detail, name='detail'),
]
