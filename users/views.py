from __future__ import annotations

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LoginForm, PasswordChangeStrictForm, ProfileForm, RegistrationForm
from .models import User


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/projects/list/")
    else:
        form = RegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.user)
            return redirect("/projects/list/")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def user_list_view(request):
    participants = User.objects.order_by("id")
    paginator = Paginator(participants, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "users/participants.html",
        {
            "participants": page_obj,
            "page_obj": page_obj,
        },
    )


def user_detail_view(request, user_id: int):
    user = get_object_or_404(
        User.objects.prefetch_related("owned_projects__participants", "owned_projects"),
        pk=user_id,
    )
    return render(request, "users/user-details.html", {"user": user})


@login_required(login_url="/users/login/")
def edit_profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(f"/users/{request.user.id}/")
    else:
        form = ProfileForm(instance=request.user)
    return render(
        request, "users/edit_profile.html", {"form": form, "user": request.user}
    )


@login_required(login_url="/users/login/")
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeStrictForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect(f"/users/{request.user.id}/")
    else:
        form = PasswordChangeStrictForm(request.user)
    return render(request, "users/change_password.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/projects/list/")
