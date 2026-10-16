from django.contrib.auth.tokens import PasswordResetTokenGenerator


class ActivationTokenGenerator(PasswordResetTokenGenerator):
    """Link aktywacyjny z maila. Przestaje działać po aktywacji i pierwszym logowaniu."""

    key_salt = 'accounts.tokens.ActivationTokenGenerator'

    def _make_hash_value(self, user, timestamp):
        return f'{user.pk}{user.is_active}{user.last_login}{timestamp}'


activation_token = ActivationTokenGenerator()
