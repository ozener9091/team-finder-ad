from __future__ import annotations

import json
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator


def normalize_phone(value: str) -> str:
    return "+7" + value[1:] if value.startswith("8") else value


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


def json_body(request):
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
    return request.POST


def paginate_queryset(queryset, page_number, per_page):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)
