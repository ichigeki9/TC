from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .forms import ResultForm
from .models import Result, Workout
from .views import leaderboard


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
    def test_register_and_login_with_email(self):
        response = self.client.post(reverse('accounts:register'), {
            'email': 'nowy@example.com',
            'display_name': 'Nowy',
            'gender': 'M',
            'password1': 'Trening-Kultura-2026',
            'password2': 'Trening-Kultura-2026',
        })
        self.assertRedirects(response, reverse('ranking:list'))

        self.client.logout()
        response = self.client.post(reverse('accounts:login'), {'username': 'nowy@example.com', 'password': 'Trening-Kultura-2026'})
        self.assertRedirects(response, reverse('ranking:list'))

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:profile')}")
