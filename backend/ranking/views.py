from itertools import groupby

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Min
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User

from .forms import ResultForm
from .models import Result, Workout

GENDER_FILTERS = {'kobiety': User.Gender.FEMALE, 'mezczyzni': User.Gender.MALE}


def workout_list(request):
    workouts = Workout.objects.filter(is_active=True).annotate(athletes=Count('results__user', distinct=True))
    programs = [(program, list(items)) for program, items in groupby(workouts, key=lambda w: w.program)]
    return render(request, 'ranking/list.html', {'programs': programs})


def leaderboard(workout, gender=None):
    """Najlepszy wynik każdego zawodnika, posortowany; remisy dzielą miejsce."""
    results = Result.objects.filter(workout=workout)
    if gender:
        results = results.filter(user__gender=gender)

    best = Min('value') if workout.lower_is_better else Max('value')
    rows = (
        results.values('user_id', 'user__display_name', 'user__gender')
        .annotate(best=best)
        .order_by('best' if workout.lower_is_better else '-best', 'user__display_name')
    )

    board = []
    for index, row in enumerate(rows):
        place = board[-1]['place'] if board and board[-1]['best'] == row['best'] else index + 1
        board.append({
            'place': place,
            'user_id': row['user_id'],
            'name': row['user__display_name'],
            'best': row['best'],
            'display': workout.format_value(row['best']),
        })
    return board


def workout_detail(request, slug):
    workout = get_object_or_404(Workout, slug=slug, is_active=True)
    gender_key = request.GET.get('plec', '')
    board = leaderboard(workout, GENDER_FILTERS.get(gender_key))

    form = None
    my_results = []
    if request.user.is_authenticated:
        form = ResultForm(request.POST or None, workout=workout)
        if request.method == 'POST' and form.is_valid():
            result = form.save(commit=False)
            result.user = request.user
            result.save()
            messages.success(request, f'Dodano wynik: {result.display_value}')
            return redirect(workout)
        my_results = Result.objects.filter(workout=workout, user=request.user)

    return render(request, 'ranking/detail.html', {
        'workout': workout,
        'board': board,
        'gender_key': gender_key,
        'form': form,
        'my_results': my_results,
    })


@login_required
@require_POST
def delete_result(request, pk):
    result = get_object_or_404(Result, pk=pk, user=request.user)
    workout = result.workout
    result.delete()
    messages.success(request, 'Usunięto wynik.')
    next_url = request.POST.get('next')
    return redirect('accounts:profile' if next_url == 'profile' else workout)
