from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from ranking.models import Result
from shop.models import Order

from .forms import ProfileForm, RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect('ranking:list')

    # Dokąd wrócić po rejestracji (np. do zamówienia w sklepie)
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = ''

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        if next_url:
            messages.success(request, 'Konto założone.')
            return redirect(next_url)
        messages.success(request, 'Konto założone. Wpisz swój pierwszy wynik!')
        return redirect('ranking:list')

    return render(request, 'accounts/register.html', {'form': form, 'next': next_url})


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
