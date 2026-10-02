from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = 'accounts'

urlpatterns = [
    path('', views.profile, name='profile'),
    path('rejestracja/', views.register, name='register'),
    path(
        'logowanie/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('wyloguj/', auth_views.LogoutView.as_view(), name='logout'),
]
