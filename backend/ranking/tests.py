from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .forms import ResultForm
from .models import DailyWorkout, Exercise, PartResult, Result, ScoreType, Workout, WorkoutPart
from .views import earlier_weeks_url, leaderboard, load_days, week_label, week_start


class RankingTestCase(TestCase):
    def setUp(self):
        self.anna = User.objects.create_user('anna@example.com', 'haslo-testowe-123', display_name='Anna', gender='F')
        self.bartek = User.objects.create_user('bartek@example.com', 'haslo-testowe-123', display_name='Bartek', gender='M')
        self.celina = User.objects.create_user('celina@example.com', 'haslo-testowe-123', display_name='Celina', gender='F')
        self.run = Workout.objects.create(program='Hyrox', name='Hyrox Sim', slug='hyrox-sim', score_type=Workout.ScoreType.TIME)
        self.deadlift = Workout.objects.create(program='Siła', name='Max Deadlift', slug='max-deadlift', score_type=Workout.ScoreType.WEIGHT)

    def add(self, user, workout, value):
        return Result.objects.create(user=user, workout=workout, value=Decimal(value))


class LeaderboardTests(RankingTestCase):
    def test_time_lower_is_better_and_best_result_per_user(self):
        self.add(self.anna, self.run, 700)
        self.add(self.anna, self.run, 650)
        self.add(self.bartek, self.run, 600)

        board = leaderboard(self.run)

        self.assertEqual([row['name'] for row in board], ['Bartek', 'Anna'])
        self.assertEqual(board[1]['display'], '10:50')

    def test_weight_higher_is_better_with_ties(self):
        self.add(self.anna, self.deadlift, 120)
        self.add(self.bartek, self.deadlift, 200)
        self.add(self.celina, self.deadlift, 120)

        board = leaderboard(self.deadlift)

        self.assertEqual([row['place'] for row in board], [1, 2, 2])
        self.assertEqual(board[0]['display'], '200 kg')

    def test_gender_filter(self):
        self.add(self.anna, self.deadlift, 120)
        self.add(self.bartek, self.deadlift, 200)

        board = leaderboard(self.deadlift, User.Gender.FEMALE)

        self.assertEqual([row['name'] for row in board], ['Anna'])


class ResultFormTests(RankingTestCase):
    def form(self, workout, score, performed_on=None):
        return ResultForm(
            {'score': score, 'performed_on': performed_on or timezone.localdate(), 'note': ''},
            workout=workout,
        )

    def test_parses_time_formats(self):
        for raw, seconds in [('12:34', 754), ('1:02:03', 3723)]:
            form = self.form(self.run, raw)
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data['score'], seconds)

    def test_rejects_invalid_time(self):
        for raw in ['12', '12:75', 'abc', '0:00']:
            self.assertFalse(self.form(self.run, raw).is_valid(), raw)

    def test_weight_accepts_comma_decimal(self):
        form = self.form(self.deadlift, '102,5')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['score'], Decimal('102.5'))

    def test_rejects_future_date(self):
        form = self.form(self.deadlift, '100', timezone.localdate() + timedelta(days=1))
        self.assertFalse(form.is_valid())


class ViewTests(RankingTestCase):
    def test_anonymous_can_view_but_not_post(self):
        url = self.run.get_absolute_url()
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.post(url, {'score': '10:00', 'performed_on': timezone.localdate()})

        self.assertFalse(Result.objects.exists())

    def test_logged_in_user_adds_result(self):
        self.client.force_login(self.anna)

        response = self.client.post(self.run.get_absolute_url(), {'score': '10:00', 'performed_on': timezone.localdate()})

        self.assertRedirects(response, self.run.get_absolute_url())
        result = Result.objects.get()
        self.assertEqual((result.user, result.value), (self.anna, Decimal(600)))

    def test_cannot_delete_someone_elses_result(self):
        result = self.add(self.anna, self.run, 600)
        self.client.force_login(self.bartek)

        response = self.client.post(reverse('ranking:delete_result', args=[result.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Result.objects.filter(pk=result.pk).exists())

    def test_inactive_workout_is_hidden(self):
        self.run.is_active = False
        self.run.save()

        self.assertEqual(self.client.get(self.run.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse('ranking:list')), 'Hyrox Sim')


class AccountTests(TestCase):
    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:profile')}")


class ExerciseTests(RankingTestCase):
    def test_workout_page_lists_exercises_in_order(self):
        Exercise.objects.create(workout=self.run, name='Wall balls', details='50 powtórzeń', order=2)
        Exercise.objects.create(workout=self.run, name='Bieg', details='1 km', order=1)
        Exercise.objects.create(workout=self.deadlift, name='Martwy ciąg', details='1 RM')

        response = self.client.get(self.run.get_absolute_url())

        self.assertEqual([e.name for e in response.context['workout'].exercises.all()], ['Bieg', 'Wall balls'])
        self.assertContains(response, '50 powtórzeń')
        self.assertNotContains(response, 'Martwy ciąg')

    def test_workout_without_exercises_has_no_section(self):
        response = self.client.get(self.run.get_absolute_url())
        self.assertNotContains(response, 'tc-exercises')


class AvatarTests(RankingTestCase):
    def test_new_user_has_default_avatar_shown_on_board(self):
        self.add(self.anna, self.run, 600)

        response = self.client.get(self.run.get_absolute_url())

        self.assertEqual(self.anna.avatar, '💪')
        self.assertEqual(response.context['board'][0]['avatar'], '💪')

    def test_user_can_change_avatar_only_to_listed_emoji(self):
        self.client.force_login(self.anna)
        data = {'display_name': 'Anna', 'gender': 'F'}

        self.client.post(reverse('accounts:profile'), {**data, 'avatar': '🦁'})
        self.anna.refresh_from_db()
        self.assertEqual(self.anna.avatar, '🦁')

        self.client.post(reverse('accounts:profile'), {**data, 'avatar': '<b>x</b>'})
        self.anna.refresh_from_db()
        self.assertEqual(self.anna.avatar, '🦁')


class DailyWorkoutTestCase(RankingTestCase):
    def setUp(self):
        super().setUp()
        self.today = timezone.localdate()
        self.daily = self.make_day(self.today)
        self.squat = WorkoutPart.objects.create(daily=self.daily, name='Back squat', score_type=ScoreType.WEIGHT, order=1)
        self.metcon = WorkoutPart.objects.create(daily=self.daily, name='Metcon', score_type=ScoreType.TIME, order=2)

    def make_day(self, day, **kwargs):
        return DailyWorkout.objects.create(date=day, **kwargs)

    def score(self, user, part, value):
        return PartResult.objects.create(user=user, part=part, value=Decimal(value))


class PartRankingTests(DailyWorkoutTestCase):
    def test_each_part_has_its_own_ranking(self):
        self.score(self.anna, self.squat, 80)
        self.score(self.bartek, self.squat, 140)
        self.score(self.anna, self.metcon, 500)
        self.score(self.bartek, self.metcon, 600)

        (day,) = load_days(DailyWorkout.objects.all(), self.anna)
        squat, metcon = day.part_list

        self.assertEqual([row['name'] for row in squat.board], ['Bartek', 'Anna'])
        self.assertEqual([row['name'] for row in metcon.board], ['Anna', 'Bartek'])
        self.assertEqual(metcon.board[0]['display'], '8:20')
        self.assertEqual((squat.letter, metcon.letter), ('A', 'B'))
        self.assertEqual(squat.my_result.value, 80)

    def test_ties_share_place_and_gender_filter(self):
        self.score(self.anna, self.squat, 100)
        self.score(self.celina, self.squat, 100)
        self.score(self.bartek, self.squat, 90)

        (day,) = load_days(DailyWorkout.objects.all(), self.anna)
        self.assertEqual([row['place'] for row in day.part_list[0].board], [1, 1, 3])

        (day,) = load_days(DailyWorkout.objects.all(), self.anna, User.Gender.MALE)
        self.assertEqual([row['name'] for row in day.part_list[0].board], ['Bartek'])

    def test_preview_shows_my_row_outside_top(self):
        for value in range(1, 13):
            user = User.objects.create_user(f'u{value}@example.com', 'haslo-testowe-123', display_name=f'U{value}')
            self.score(user, self.squat, 200 + value)
        self.score(self.anna, self.squat, 50)

        (day,) = load_days(DailyWorkout.objects.all(), self.anna, preview=10)
        part = day.part_list[0]

        self.assertEqual(len(part.preview), 10)
        self.assertEqual(part.hidden_count, 3)
        self.assertEqual((part.my_row['name'], part.my_row['place']), ('Anna', 13))

    def test_one_result_per_user_and_part(self):
        self.score(self.anna, self.squat, 80)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.score(self.anna, self.squat, 90)


class DailyViewTests(DailyWorkoutTestCase):
    def test_list_shows_current_week_and_hides_future_and_unpublished(self):
        self.score(self.bartek, self.squat, 140)
        self.make_day(self.today + timedelta(days=1), title='Jutrzejszy')
        self.make_day(week_start(self.today) - timedelta(days=3), title='Zeszły tydzień')
        unpublished = self.make_day(self.today - timedelta(days=30), title='Ukryty', is_published=False)

        response = self.client.get(reverse('ranking:list'))

        self.assertContains(response, 'Back squat')
        self.assertContains(response, '140 kg')
        self.assertNotContains(response, 'Jutrzejszy')
        self.assertNotContains(response, 'Zeszły tydzień')  # dopiero po kliknięciu
        self.assertContains(response, 'Pokaż wcześniejsze tygodnie')
        self.assertEqual(self.client.get(unpublished.get_absolute_url()).status_code, 404)

    def test_earlier_weeks_are_paged(self):
        monday = week_start(self.today)
        for weeks_back in range(1, 7):
            self.make_day(monday - timedelta(weeks=weeks_back))

        response = self.client.get(earlier_weeks_url(monday))

        self.assertEqual(len(response.context['weeks']), 4)
        self.assertEqual(response.context['weeks'][0]['start'], monday - timedelta(weeks=1))
        self.assertEqual(response.context['more_url'], earlier_weeks_url(monday - timedelta(weeks=4)))

        response = self.client.get(response.context['more_url'])

        self.assertEqual(len(response.context['weeks']), 2)
        self.assertIsNone(response.context['more_url'])

    def test_week_returns_its_days(self):
        monday = week_start(self.today) - timedelta(weeks=1)
        old = self.make_day(monday + timedelta(days=2), title='Środowy')
        WorkoutPart.objects.create(daily=old, name='Wiosłowanie', score_type=ScoreType.TIME)
        self.make_day(monday - timedelta(days=1), title='Inny tydzień')

        response = self.client.get(reverse('ranking:week', args=[monday.isoformat()]))

        self.assertContains(response, 'Środowy')
        self.assertContains(response, 'Wiosłowanie')
        self.assertNotContains(response, 'Inny tydzień')

    def test_bad_date_is_404(self):
        self.assertEqual(self.client.get(reverse('ranking:day', args=['abc'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('ranking:weeks') + '?przed=x').status_code, 404)

    def post_score(self, part, score):
        return self.client.post(self.daily.get_absolute_url(), {
            'part': part.pk, f'p{part.pk}-score': score, f'p{part.pk}-note': '',
        })

    def test_user_adds_and_then_corrects_result(self):
        self.client.force_login(self.anna)

        response = self.post_score(self.metcon, '10:00')
        self.assertRedirects(response, f'{self.daily.get_absolute_url()}#czesc-{self.metcon.pk}', fetch_redirect_response=False)
        self.post_score(self.metcon, '9:30')

        result = PartResult.objects.get()
        self.assertEqual((result.user, result.part, result.value), (self.anna, self.metcon, Decimal(570)))

    def test_invalid_score_shows_error_only_on_that_part(self):
        self.client.force_login(self.anna)

        response = self.post_score(self.metcon, 'szybko')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(PartResult.objects.exists())
        parts = response.context['daily'].part_list
        self.assertFalse(parts[0].form.is_bound)
        self.assertIn('score', parts[1].form.errors)

    def test_anonymous_cannot_post(self):
        self.post_score(self.squat, '100')
        self.assertFalse(PartResult.objects.exists())

    def test_cannot_delete_someone_elses_part_result(self):
        result = self.score(self.anna, self.squat, 100)
        self.client.force_login(self.bartek)

        response = self.client.post(reverse('ranking:delete_part_result', args=[result.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(PartResult.objects.filter(pk=result.pk).exists())


class WeekLabelTests(TestCase):
    def test_labels(self):
        from datetime import date
        self.assertEqual(week_label(date(2026, 11, 2)), '2–8 listopada 2026')
        self.assertEqual(week_label(date(2026, 10, 26)), '26 października – 1 listopada 2026')
        self.assertEqual(week_label(date(2026, 12, 28)), '28 grudnia 2026 – 3 stycznia 2027')


class StaffDailyEditTests(DailyWorkoutTestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user('admin@example.com', 'haslo-testowe-123', display_name='Trener', is_staff=True)

    def form_data(self, day, parts, existing=()):
        data = {
            'date': day.isoformat(), 'title': 'Siła', 'description': '', 'is_published': 'on',
            'czesci-TOTAL_FORMS': str(len(existing) + len(parts)),
            'czesci-INITIAL_FORMS': str(len(existing)),
            'czesci-MIN_NUM_FORMS': '0', 'czesci-MAX_NUM_FORMS': '1000',
        }
        rows = [(part.pk, part.name, part.score_type, delete) for part, delete in existing]
        rows += [('', name, score_type, False) for name, score_type in parts]
        for index, (pk, name, score_type, delete) in enumerate(rows):
            data.update({
                f'czesci-{index}-id': pk, f'czesci-{index}-name': name,
                f'czesci-{index}-score_type': score_type, f'czesci-{index}-description': '',
            })
            if delete:
                data[f'czesci-{index}-DELETE'] = 'on'
        return data

    def test_regular_user_cannot_add(self):
        self.client.force_login(self.anna)
        self.assertEqual(self.client.get(reverse('ranking:daily_add')).status_code, 403)
        self.assertNotContains(self.client.get(reverse('ranking:list')), 'Dodaj trening dnia')

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(reverse('ranking:daily_add'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('ranking:daily_add')}")

    def test_admin_adds_training_with_parts_and_empty_rows_are_skipped(self):
        self.client.force_login(self.admin)
        tomorrow = self.today + timedelta(days=1)

        response = self.client.post(reverse('ranking:daily_add'), self.form_data(tomorrow, [
            ('Back squat', 'weight'), ('Metcon', 'time'), ('', ''), ('', ''),
        ]))

        daily = DailyWorkout.objects.get(date=tomorrow)
        self.assertRedirects(response, daily.get_absolute_url())
        self.assertEqual([(p.name, p.order) for p in daily.parts.all()], [('Back squat', 0), ('Metcon', 1)])
        # Admin widzi zaplanowany trening, zawodnik jeszcze nie
        self.assertEqual(self.client.get(daily.get_absolute_url()).status_code, 200)
        self.client.force_login(self.anna)
        self.assertEqual(self.client.get(daily.get_absolute_url()).status_code, 404)

    def test_training_needs_at_least_one_part_and_unique_date(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse('ranking:daily_add'), self.form_data(self.today, [('', '')]))

        self.assertEqual(response.status_code, 200)
        self.assertIn('date', response.context['form'].errors)
        self.assertTrue(response.context['parts'].non_form_errors())

    def test_admin_edits_deletes_part_and_cannot_change_scored_type(self):
        self.score(self.anna, self.squat, 100)
        self.client.force_login(self.admin)
        url = reverse('ranking:daily_edit', args=[self.today.isoformat()])
        data = self.form_data(self.today, [('Bieg', 'time')], existing=[(self.squat, False), (self.metcon, True)])
        data['czesci-0-score_type'] = 'time'  # próba zmiany typu części z wynikami

        self.client.post(url, data)

        names = [(p.name, p.score_type) for p in self.daily.parts.all()]
        self.assertEqual(names, [('Back squat', 'weight'), ('Bieg', 'time')])
        self.assertEqual(PartResult.objects.count(), 1)

    def test_admin_deletes_training(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('ranking:daily_delete', args=[self.today.isoformat()]))
        self.assertFalse(DailyWorkout.objects.exists())
