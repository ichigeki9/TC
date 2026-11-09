from collections import defaultdict
from datetime import date, timedelta
from functools import wraps
from itertools import groupby

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Max, Min
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateformat import format as format_date
from django.views.decorators.http import require_POST

from accounts.models import User

from .forms import DailyWorkoutForm, PartResultForm, ResultForm, part_formset
from .models import DailyWorkout, PartResult, Result, Workout

GENDER_FILTERS = {'kobiety': User.Gender.FEMALE, 'mezczyzni': User.Gender.MALE}


# Ile starszych tygodni doczytuje jedno kliknięcie „Pokaż wcześniejsze”
WEEKS_PER_PAGE = 4
# Ile miejsc rankingu części widać w rozwijanej liście (pełny ranking na stronie dnia)
BOARD_PREVIEW = 10


def workout_list(request):
    today = timezone.localdate()
    monday = week_start(today)
    days = load_days(DailyWorkout.objects.visible().filter(date__gte=monday), request.user, preview=BOARD_PREVIEW)
    has_earlier = DailyWorkout.objects.visible().filter(date__lt=monday).exists()

    workouts = Workout.objects.filter(is_active=True).annotate(athletes=Count('results__user', distinct=True))
    programs = [(program, list(items)) for program, items in groupby(workouts, key=lambda w: w.program)]
    # Admin widzi też treningi z przyszłości i ukryte, żeby móc je sprawdzić i poprawić
    planned = []
    if request.user.is_staff:
        planned = DailyWorkout.objects.exclude(pk__in=DailyWorkout.objects.visible()).order_by('date')

    return render(request, 'ranking/list.html', {
        'programs': programs,
        'days': days,
        'week_label': week_label(monday),
        'earlier_url': earlier_weeks_url(monday) if has_earlier else None,
        'planned': planned,
    })


# ===== Trening dnia =====

def week_start(day):
    return day - timedelta(days=day.weekday())


def week_label(monday):
    sunday = monday + timedelta(days=6)
    if monday.month == sunday.month:
        return f'{monday.day}–{format_date(sunday, "j E Y")}'
    if monday.year == sunday.year:
        return f'{format_date(monday, "j E")} – {format_date(sunday, "j E Y")}'
    return f'{format_date(monday, "j E Y")} – {format_date(sunday, "j E Y")}'


def plural(count, one, few, many):
    if count == 1:
        return one
    if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return few
    return many


def earlier_weeks_url(before):
    return f"{reverse('ranking:weeks')}?przed={before.isoformat()}"


def parse_day(raw):
    try:
        return date.fromisoformat(raw)
    except (TypeError, ValueError):
        raise Http404('Nieprawidłowa data.')


def part_board(part, results, gender=None):
    """Ranking jednej części: każdy ma jeden wynik, remisy dzielą miejsce."""
    if gender:
        results = [r for r in results if r.user.gender == gender]
    sign = 1 if part.lower_is_better else -1
    results = sorted(results, key=lambda r: (sign * r.value, r.created_at))

    board = []
    for index, result in enumerate(results):
        place = board[-1]['place'] if board and board[-1]['value'] == result.value else index + 1
        board.append({
            'place': place,
            'value': result.value,
            'user_id': result.user_id,
            'name': result.user.display_name,
            'avatar': result.user.avatar,
            'display': result.display_value,
            'note': result.note,
        })
    return board


def load_days(dailies, user, gender=None, preview=None):
    """Treningi dnia z częściami i rankingami — wszystkie wyniki jednym zapytaniem."""
    days = list(dailies.order_by('-date').prefetch_related('parts'))
    parts = [part for day in days for part in day.parts.all()]

    by_part = defaultdict(list)
    for result in PartResult.objects.filter(part__in=parts).select_related('user', 'part'):
        by_part[result.part_id].append(result)

    user_id = user.id if user.is_authenticated else None
    for day in days:
        day.part_list = list(day.parts.all())
        for index, part in enumerate(day.part_list):
            part.letter = chr(ord('A') + index) if index < 26 else str(index + 1)
            part.board = part_board(part, by_part[part.pk], gender)
            part.my_result = next((r for r in by_part[part.pk] if r.user_id == user_id), None)
            if preview:
                part.preview = part.board[:preview]
                part.hidden_count = max(len(part.board) - preview, 0)
                # Własny wynik spoza czołówki pokazujemy pod nią
                part.my_row = next((row for row in part.board[preview:] if row['user_id'] == user_id), None)
    return days


def earlier_weeks(request):
    """Doczytywane przyciskiem: nagłówki starszych tygodni (dni ładują się po rozwinięciu)."""
    before = week_start(parse_day(request.GET.get('przed')))
    dates = DailyWorkout.objects.visible().filter(date__lt=before).values_list('date', flat=True).order_by('-date')

    counts = {}
    has_more = False
    for day in dates:
        monday = week_start(day)
        if monday not in counts and len(counts) == WEEKS_PER_PAGE:
            has_more = True
            break
        counts[monday] = counts.get(monday, 0) + 1

    weeks = [{
        'start': start,
        'label': week_label(start),
        'count': f'{count} {plural(count, "trening", "treningi", "treningów")}',
    } for start, count in counts.items()]
    return render(request, 'ranking/_weeks.html', {
        'weeks': weeks,
        'more_url': earlier_weeks_url(weeks[-1]['start']) if has_more else None,
    })


def week_days(request, start):
    """Doczytywane po rozwinięciu tygodnia: jego dni z rankingami części."""
    monday = week_start(parse_day(start))
    dailies = DailyWorkout.objects.visible().filter(date__range=(monday, monday + timedelta(days=6)))
    days = load_days(dailies, request.user, preview=BOARD_PREVIEW)
    return render(request, 'ranking/_days.html', {'days': days})


def day_detail(request, day):
    dailies = DailyWorkout.objects.all() if request.user.is_staff else DailyWorkout.objects.visible()
    daily = get_object_or_404(dailies, date=parse_day(day))
    gender_key = request.GET.get('plec', '')
    (daily,) = load_days(DailyWorkout.objects.filter(pk=daily.pk), request.user, GENDER_FILTERS.get(gender_key))

    if request.user.is_authenticated:
        posted_part = request.POST.get('part') if request.method == 'POST' else None
        for part in daily.part_list:
            data = request.POST if posted_part == str(part.pk) else None
            part.form = PartResultForm(data, part=part, instance=part.my_result, prefix=f'p{part.pk}')
            if data is not None and part.form.is_valid():
                result = part.form.save(commit=False)
                result.user = request.user
                result.save()
                messages.success(request, f'{part.name}: zapisano wynik {result.display_value}')
                return redirect(f'{daily.get_absolute_url()}#czesc-{part.pk}')

    return render(request, 'ranking/day.html', {
        'daily': daily,
        'gender_key': gender_key,
        'today': timezone.localdate(),
    })


@login_required
@require_POST
def delete_part_result(request, pk):
    result = get_object_or_404(PartResult.objects.select_related('part__daily'), pk=pk, user=request.user)
    daily = result.part.daily
    result.delete()
    messages.success(request, 'Usunięto wynik.')
    return redirect(f'{daily.get_absolute_url()}#czesc-{result.part_id}')


# ===== Dodawanie treningów dnia na stronie (konto admina) =====

def staff_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


@staff_required
def daily_edit(request, day=None):
    daily = get_object_or_404(DailyWorkout, date=parse_day(day)) if day else None
    initial = {}
    if daily is None:
        # Domyślnie najbliższy dzień od dziś, który nie ma jeszcze treningu
        taken = set(DailyWorkout.objects.filter(date__gte=timezone.localdate()).values_list('date', flat=True))
        suggested = timezone.localdate()
        while suggested in taken:
            suggested += timedelta(days=1)
        initial['date'] = suggested

    data = request.POST if request.method == 'POST' else None
    form = DailyWorkoutForm(data, instance=daily, initial=initial)
    parts = part_formset(data, instance=form.instance)

    if data is not None and form.is_valid() and parts.is_valid():
        with transaction.atomic():
            daily = form.save()
            parts.instance = daily
            parts.save()
        messages.success(request, f'Zapisano trening {daily.date:%d.%m.%Y}.')
        return redirect(daily)

    return render(request, 'ranking/day_form.html', {'form': form, 'parts': parts, 'daily': daily})


@staff_required
@require_POST
def daily_delete(request, day):
    daily = get_object_or_404(DailyWorkout, date=parse_day(day))
    daily.delete()
    messages.success(request, f'Usunięto trening {daily.date:%d.%m.%Y}.')
    return redirect('ranking:list')


# ===== Treningi testowe =====


def leaderboard(workout, gender=None):
    """Najlepszy wynik każdego zawodnika, posortowany; remisy dzielą miejsce."""
    results = Result.objects.filter(workout=workout)
    if gender:
        results = results.filter(user__gender=gender)

    best = Min('value') if workout.lower_is_better else Max('value')
    rows = (
        results.values('user_id', 'user__display_name', 'user__gender', 'user__avatar')
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
            'avatar': row['user__avatar'],
            'best': row['best'],
            'display': workout.format_value(row['best']),
        })
    return board


def workout_detail(request, slug):
    workout = get_object_or_404(Workout.objects.prefetch_related('exercises'), slug=slug, is_active=True)
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
