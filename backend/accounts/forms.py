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


class ProfileForm(forms.ModelForm):
    avatar = forms.ChoiceField(label='Avatar', choices=[(emoji, emoji) for emoji in AVATARS], widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ('avatar', 'display_name', 'gender')
