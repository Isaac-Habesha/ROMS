from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser

INPUT_TW = 'w-full px-3.5 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500'
SELECT_TW = 'w-full px-3.5 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500'
CHECKBOX_TW = 'w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500'


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': INPUT_TW,
            'placeholder': 'Username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_TW,
            'placeholder': 'Password',
        })
    )


class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': INPUT_TW}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': INPUT_TW}),
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT_TW}),
            'first_name': forms.TextInput(attrs={'class': INPUT_TW}),
            'last_name': forms.TextInput(attrs={'class': INPUT_TW}),
            'email': forms.EmailInput(attrs={'class': INPUT_TW}),
            'phone_number': forms.TextInput(attrs={'class': INPUT_TW}),
            'role': forms.Select(attrs={'class': SELECT_TW}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'role', 'is_active_employee']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_TW}),
            'last_name': forms.TextInput(attrs={'class': INPUT_TW}),
            'email': forms.EmailInput(attrs={'class': INPUT_TW}),
            'phone_number': forms.TextInput(attrs={'class': INPUT_TW}),
            'role': forms.Select(attrs={'class': SELECT_TW}),
            'is_active_employee': forms.CheckboxInput(attrs={'class': CHECKBOX_TW}),
        }
