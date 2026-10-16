from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import AVATARS, User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'display_name', 'gender')
        help_texts = {
            'display_name': 'Tak będziesz widoczny w rankingu.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gender'].required = True


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='E-mail', widget=forms.EmailInput(attrs={'autofocus': True}))

    def clean(self):
        try:
            return super().clean()
        except forms.ValidationError:
            # Django nie odróżnia nieaktywnego konta od złego hasła — podpowiadamy, gdy brakuje tylko aktywacji
            email, password = self.cleaned_data.get('username'), self.cleaned_data.get('password')
            user = User.objects.filter(email__iexact=email, is_active=False, last_login__isnull=True).first() if email else None
            if user and password and user.check_password(password):
                raise forms.ValidationError(
                    'Konto nie jest jeszcze aktywne — kliknij link z maila, który wysłaliśmy po rejestracji.',
                    code='inactive',
                )
            raise


class ResendActivationForm(forms.Form):
    email = forms.EmailField(label='E-mail', widget=forms.EmailInput(attrs={'autofocus': True}))


class ProfileForm(forms.ModelForm):
    avatar = forms.ChoiceField(label='Avatar', choices=[(emoji, emoji) for emoji in AVATARS], widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ('avatar', 'display_name', 'gender')
