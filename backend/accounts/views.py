from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ranking.models import Result

from .forms import ProfileForm, RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect('ranking:list')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Konto założone. Wpisz swój pierwszy wynik!')
        return redirect('ranking:list')

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Zapisano zmiany.')
        return redirect('accounts:profile')

    results = Result.objects.filter(user=request.user).select_related('workout')
    return render(request, 'accounts/profile.html', {'form': form, 'results': results})
