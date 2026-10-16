import re

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import User

REGISTRATION = {
    'email': 'nowy@example.com', 'display_name': 'Nowy', 'gender': 'M',
    'password1': 'Trening-Kultura-2026', 'password2': 'Trening-Kultura-2026',
}


def activation_link(message):
    return re.search(r'http://testserver(\S+)', message.body).group(1)


class ActivationTests(TestCase):
    def register(self):
        return self.client.post(reverse('accounts:register'), REGISTRATION)

    def login(self):
        return self.client.post(reverse('accounts:login'), {'username': 'nowy@example.com', 'password': 'Trening-Kultura-2026'})

    def test_new_account_is_inactive_until_link_is_clicked(self):
        response = self.register()

        self.assertContains(response, 'nowy@example.com')
        self.assertFalse(User.objects.get().is_active)
        self.assertEqual(mail.outbox[0].to, ['nowy@example.com'])
        self.assertContains(self.login(), 'nie jest jeszcze aktywne')

        response = self.client.get(activation_link(mail.outbox[0]))

        self.assertRedirects(response, reverse('ranking:list'))
        self.assertTrue(User.objects.get().is_active)
        self.client.logout()
        self.assertRedirects(self.login(), reverse('ranking:list'))

    def test_link_works_only_once(self):
        self.register()
        link = activation_link(mail.outbox[0])
        self.client.get(link)
        self.client.logout()

        self.assertRedirects(self.client.get(link), reverse('accounts:login'))

    def test_broken_link_is_rejected(self):
        self.register()
        link = activation_link(mail.outbox[0])

        response = self.client.get(link.rstrip('/')[:-3] + 'xyz/')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.get().is_active)

    def test_wrong_password_does_not_reveal_inactive_account(self):
        self.register()
        response = self.client.post(reverse('accounts:login'), {'username': 'nowy@example.com', 'password': 'zle-haslo'})
        self.assertNotContains(response, 'nie jest jeszcze aktywne')

    def test_resend_sends_new_link_only_to_pending_accounts(self):
        self.register()
        User.objects.create_user('aktywny@example.com', 'haslo-testowe-123', display_name='A')
        mail.outbox.clear()

        self.client.post(reverse('accounts:resend_activation'), {'email': 'nowy@example.com'})
        self.client.post(reverse('accounts:resend_activation'), {'email': 'aktywny@example.com'})
        self.client.post(reverse('accounts:resend_activation'), {'email': 'brak@example.com'})

        self.assertEqual([m.to for m in mail.outbox], [['nowy@example.com']])
        self.assertRedirects(self.client.get(activation_link(mail.outbox[0])), reverse('ranking:list'))

    def test_blocked_account_cannot_reactivate_itself(self):
        user = User.objects.create_user('nowy@example.com', 'Trening-Kultura-2026', display_name='Nowy')
        self.client.force_login(user)  # ustawia last_login
        self.client.logout()
        user.refresh_from_db()
        user.is_active = False
        user.save()

        self.client.post(reverse('accounts:resend_activation'), {'email': 'nowy@example.com'})

        self.assertEqual(mail.outbox, [])
        self.assertNotContains(self.login(), 'nie jest jeszcze aktywne')


class PasswordResetTests(TestCase):
    def test_reset_password_by_email(self):
        User.objects.create_user('anna@example.com', 'stare-haslo-123', display_name='Anna')

        response = self.client.post(reverse('accounts:password_reset'), {'email': 'anna@example.com'})
        self.assertRedirects(response, reverse('accounts:password_reset_done'))

        # Django przekierowuje z linku z tokenem na adres z „set-password”
        response = self.client.get(activation_link(mail.outbox[0]), follow=True)
        response = self.client.post(response.redirect_chain[-1][0], {
            'new_password1': 'Nowe-Haslo-2026', 'new_password2': 'Nowe-Haslo-2026',
        })

        self.assertRedirects(response, reverse('accounts:password_reset_complete'))
        self.assertTrue(self.client.login(username='anna@example.com', password='Nowe-Haslo-2026'))
