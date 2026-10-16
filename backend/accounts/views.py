from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode, urlsafe_base64_encode

from config.emails import send_email
from ranking.models import Result
from shop.models import Order

from .forms import ProfileForm, RegisterForm, ResendActivationForm
from .models import User
from .tokens import activation_token


def get_next_url(request):
    """Dokąd wrócić po rejestracji (np. do zamówienia w sklepie) — tylko adresy z naszej domeny."""
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return ''
    return next_url


def send_activation_email(request, user, next_url=''):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    url = reverse('accounts:activate', args=[uid, activation_token.make_token(user)])
    if next_url:
        url += '?' + urlencode({'next': next_url})
    return send_email('activation', {'user': user, 'url': request.build_absolute_uri(url)}, [user.email])


def register(request):
    if request.user.is_authenticated:
        return redirect('ranking:list')

    next_url = get_next_url(request)
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Konto działa dopiero po kliknięciu linku z maila
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        sent = send_activation_email(request, user, next_url)
        return render(request, 'accounts/activation_sent.html', {'email': user.email, 'sent': sent})

    return render(request, 'accounts/register.html', {'form': form, 'next': next_url})


def activate(request, uidb64, token):
    try:
        user = User.objects.get(pk=urlsafe_base64_decode(uidb64).decode())
    except (ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and user.is_active:
        messages.info(request, 'Konto jest już aktywne — zaloguj się.')
        return redirect('accounts:login')
    if user is None or not activation_token.check_token(user, token):
        return render(request, 'accounts/activation_invalid.html', status=400)

    user.is_active = True
    user.save(update_fields=['is_active'])
    login(request, user)
    next_url = get_next_url(request)
    if next_url:
        messages.success(request, 'Konto aktywne.')
        return redirect(next_url)
    messages.success(request, 'Konto aktywne. Wpisz swój pierwszy wynik!')
    return redirect('ranking:list')


def resend_activation(request):
    form = ResendActivationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Tylko konta, które nigdy nie były aktywne — nie odblokowujemy kont zablokowanych w panelu
        user = User.objects.filter(
            email__iexact=form.cleaned_data['email'], is_active=False, last_login__isnull=True,
        ).first()
        if user:
            send_activation_email(request, user)
        # Ta sama odpowiedź niezależnie od tego, czy konto istnieje
        messages.success(request, 'Jeśli konto czeka na aktywację, wysłaliśmy nowy link. Sprawdź też folder spam.')
        return redirect('accounts:login')

    return render(request, 'accounts/resend_activation.html', {'form': form})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Zapisano zmiany.')
        return redirect('accounts:profile')

    results = Result.objects.filter(user=request.user).select_related('workout')
    orders = Order.objects.filter(user=request.user)
    return render(request, 'accounts/profile.html', {'form': form, 'results': results, 'orders': orders})
