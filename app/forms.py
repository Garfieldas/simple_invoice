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

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'email@example.com',
                'autocomplete': 'email',
            }
        ),
        label='Email',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
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
                'placeholder': 'Last name',
                'autocomplete': 'family-name',
            }
        ),
        label='Last name',
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '••••••••',
                'autocomplete': 'new-password',
            }
        ),
        label='Password',
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
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
                'placeholder': '••••••••',
                'autocomplete': 'new-password',
            }
        ),
        label='New password',
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
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
            'client_type': Select2Widget,
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            'phone_number', 'address', 'city', 'personal_code',
            'postal_code', 'apartment_number', 'bank_account', 'bank_name',
        )


class UserCompanyForm(forms.ModelForm):
    class Meta:
        model = UserCompany
        fields = (
            'company_name', 'company_code', 'vat_code', 'address',
            'city', 'postal_code', 'apartment_number', 'bank_account',
            'bank_name',
        )


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = (
            'client', 'series', 'number', 'status',
            'issue_date', 'due_date', 'tax_enabled', 'tax_rate', 'notes',
        )
        widgets = {
            'client': Select2Widget,
            'status': Select2Widget,
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'tax_rate': Select2Widget,
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ('description', 'unit', 'quantity', 'unit_price')


InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm,
    extra=1, can_delete=True,
)
