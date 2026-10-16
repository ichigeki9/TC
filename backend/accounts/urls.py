from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import LoginForm

app_name = 'accounts'

urlpatterns = [
    path('', views.profile, name='profile'),
    path('rejestracja/', views.register, name='register'),
    path('aktywacja/wyslij-ponownie/', views.resend_activation, name='resend_activation'),
    path('aktywacja/<uidb64>/<token>/', views.activate, name='activate'),
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
    # Reset hasła — wbudowane widoki Django, link przychodzi mailem
    path(
        'haslo/reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            email_template_name='emails/password_reset.txt',
            subject_template_name='emails/password_reset_subject.txt',
            success_url=reverse_lazy('accounts:password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'haslo/reset/wyslano/',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'haslo/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'haslo/reset/gotowe/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete',
    ),
]
