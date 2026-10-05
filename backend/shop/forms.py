from django import forms
from django.core.validators import RegexValidator

from .models import Order, ShippingMethod


class CheckoutForm(forms.ModelForm):
    shipping = forms.ModelChoiceField(
        label='Dostawa',
        queryset=ShippingMethod.objects.filter(is_active=True),
        widget=forms.RadioSelect,
        empty_label=None,
        error_messages={'required': 'Wybierz sposób dostawy.'},
    )
    postal_code = forms.CharField(
        label='Kod pocztowy', max_length=6,
        validators=[RegexValidator(r'^\d{2}-\d{3}$', 'Podaj kod w formacie 00-000.')],
        widget=forms.TextInput(attrs={'placeholder': '00-000', 'autocomplete': 'postal-code'}),
    )

    class Meta:
        model = Order
        fields = ('full_name', 'email', 'phone', 'street', 'postal_code', 'city', 'note')
        widgets = {
            'full_name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'autocomplete': 'tel', 'inputmode': 'tel'}),
            'street': forms.TextInput(attrs={'autocomplete': 'street-address'}),
            'city': forms.TextInput(attrs={'autocomplete': 'address-level2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        methods = list(self.fields['shipping'].queryset)
        if len(methods) == 1:
            self.fields['shipping'].initial = methods[0]
