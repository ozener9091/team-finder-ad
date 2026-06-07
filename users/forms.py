from __future__ import annotations

import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from team_finder.utils import normalize_phone, validate_github_url

from .models import User

PHONE_RE = re.compile(r"^(?:8|\+7)\d{10}$")


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
    )

    class Meta:
        model = User
        fields = ("name", "surname", "email")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Имейл",
        }
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "surname": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Имейл", widget=forms.EmailInput(attrs={"autocomplete": "email"})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            self.user = authenticate(email=email, password=password)
            if self.user is None:
                raise ValidationError("Неверный имейл или пароль")
        return cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "Ссылка на Github",
        }
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "surname": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "about": forms.Textarea(attrs={"rows": 4}),
            "phone": forms.TextInput(attrs={"placeholder": "+7XXXXXXXXXX"}),
            "github_url": forms.URLInput(
                attrs={"placeholder": "https://github.com/username"}
            ),
        }

    def clean_phone(self):
        raw_phone = (self.cleaned_data.get("phone") or "").strip()
        if not raw_phone:
            return None
        if not PHONE_RE.match(raw_phone):
            raise ValidationError(
                "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
            )
        normalized = normalize_phone(raw_phone)
        qs = User.objects.exclude(pk=self.instance.pk).filter(phone=normalized)
        if qs.exists():
            raise ValidationError("Пользователь с таким телефоном уже существует.")
        return normalized

    def clean_github_url(self):
        value = self.cleaned_data.get("github_url")
        if not value:
            return value
        return validate_github_url(value)


class PasswordChangeStrictForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("autocomplete", "off")


class UserAdminCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "name", "surname")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают.")
        validate_password(password2)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Пароль")

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "name",
            "surname",
            "avatar",
            "about",
            "phone",
            "github_url",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
