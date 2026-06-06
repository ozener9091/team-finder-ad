from __future__ import annotations

from urllib.parse import urlparse

from django import forms
from django.core.exceptions import ValidationError

from .models import Project


def validate_github_url(value: str) -> str:
    if not value:
        return value
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or hostname not in {
        "github.com",
        "www.github.com",
    }:
        raise ValidationError("Ссылка должна вести именно на Github.")
    return value


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на Github",
            "status": "Статус",
        }
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "off"}),
            "description": forms.Textarea(attrs={"rows": 6}),
            "github_url": forms.URLInput(
                attrs={"placeholder": "https://github.com/username/repo"}
            ),
            "status": forms.Select(),
        }

    def clean_github_url(self):
        value = self.cleaned_data.get("github_url")
        if not value:
            return value
        return validate_github_url(value)
