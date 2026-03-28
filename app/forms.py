from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.forms import inlineformset_factory
from django_select2.forms import Select2Widget

from app.models import Client, Invoice, InvoiceItem, UserCompany, UserProfile

TAILWIND_INPUT_CLASS = (
    'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900'
    ' placeholder-gray-400 focus:border-red-500 focus:outline-none'
    ' focus:ring-1 focus:ring-red-500 sm:text-sm'
)

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 sm:text-sm',
                'placeholder': 'email@example.com',
                'autocomplete': 'email',
            }
        ),
        label='Email',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 sm:text-sm',
                'placeholder': '••••••••',
                'autocomplete': 'current-password',
            }
        ),
        label='Password',
    )


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 sm:text-sm',
                'placeholder': 'email@example.com',
                'autocomplete': 'email',
            }
        ),
        label='Email',
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 sm:text-sm',
                'placeholder': 'First name',
                'autocomplete': 'given-name',
            }
        ),
        label='First name',
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 sm:text-sm',
                'placeholder': 'Last name',
                'autocomplete': 'family-name',
            }
        ),
        label='Last name',
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 sm:text-sm',
                'placeholder': '••••••••',
                'autocomplete': 'new-password',
            }
        ),
        label='Password',
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 sm:text-sm',
                'placeholder': '••••••••',
                'autocomplete': 'new-password',
            }
        ),
        label='Confirm password',
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 sm:text-sm',
                'placeholder': 'email@example.com',
                'autocomplete': 'email',
            }
        ),
        label='Email',
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 sm:text-sm',
                'placeholder': '••••••••',
                'autocomplete': 'new-password',
            }
        ),
        label='New password',
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 sm:text-sm',
                'placeholder': '••••••••',
                'autocomplete': 'new-password',
            }
        ),
        label='Confirm new password',
    )


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = (
            'client_type', 'name', 'company_code', 'vat_code',
            'email', 'phone_number', 'address', 'city',
        )
        widgets = {
            'client_type': Select2Widget(attrs={'class': TAILWIND_INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'company_code': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'vat_code': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'email': forms.EmailInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'phone_number': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'address': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'city': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            'phone_number', 'address', 'city', 'personal_code',
            'postal_code', 'apartment_number', 'bank_account', 'bank_name',
        )
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'address': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'city': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'personal_code': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'postal_code': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'apartment_number': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'bank_account': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'bank_name': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
        }


class UserCompanyForm(forms.ModelForm):
    class Meta:
        model = UserCompany
        fields = (
            'company_name', 'company_code', 'vat_code', 'address',
            'city', 'postal_code', 'apartment_number', 'bank_account',
            'bank_name',
        )
        widgets = {
            'company_name': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'company_code': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'vat_code': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'address': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'city': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'postal_code': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'apartment_number': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'bank_account': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'bank_name': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = (
            'client', 'series', 'number', 'status',
            'issue_date', 'due_date', 'tax_enabled', 'tax_rate', 'notes',
        )
        widgets = {
            'client': Select2Widget(attrs={'class': TAILWIND_INPUT_CLASS}),
            'series': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'number': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'status': Select2Widget(attrs={'class': TAILWIND_INPUT_CLASS}),
            'issue_date': forms.DateInput(
                attrs={'class': TAILWIND_INPUT_CLASS, 'type': 'date'},
            ),
            'due_date': forms.DateInput(
                attrs={'class': TAILWIND_INPUT_CLASS, 'type': 'date'},
            ),
            'tax_enabled': forms.CheckboxInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'tax_rate': Select2Widget(attrs={'class': TAILWIND_INPUT_CLASS}),
            'notes': forms.Textarea(
                attrs={'class': TAILWIND_INPUT_CLASS, 'rows': 3},
            ),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ('description', 'unit', 'quantity', 'unit_price')
        widgets = {
            'description': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'unit': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'unit_price': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASS}),
        }


InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm,
    extra=1, can_delete=True,
)
