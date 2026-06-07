from __future__ import annotations

from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from team_finder.utils import json_body as _json_body
from team_finder.utils import paginate_queryset

from .forms import ProjectForm
from .models import Project, Skill

PROJECTS_PER_PAGE = 12
SKILL_SUGGESTIONS_LIMIT = 10


def _can_manage_project(user, project):
    return user.is_authenticated and (
        user.is_staff or user.is_superuser or project.owner_id == user.id
    )


def project_list_view(request):
    projects_qs = (
        Project.objects.select_related("owner")
        .prefetch_related("participants", "skills")
        .order_by("-created_at")
    )
    active_skill = request.GET.get("skill", "").strip()
    if active_skill:
        projects_qs = projects_qs.filter(skills__name__iexact=active_skill).distinct()

    page_obj = paginate_queryset(
        projects_qs, request.GET.get("page"), PROJECTS_PER_PAGE
    )
    context = {
        "projects": page_obj,
        "page_obj": page_obj,
        "all_skills": Skill.objects.order_by("name"),
        "active_skill": active_skill,
    }
    return render(request, "projects/project_list.html", context)


def project_detail_view(request, project_id: int):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related(
            "participants", "skills"
        ),
        pk=project_id,
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required(login_url="/users/login/")
def create_project_view(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect(project.get_absolute_url())
    else:
        form = ProjectForm()
    return render(
        request, "projects/create-project.html", {"form": form, "is_edit": False}
    )


@login_required(login_url="/users/login/")
def edit_project_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    if not _can_manage_project(request.user, project):
        return HttpResponseForbidden("Forbidden")

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            updated = form.save()
            return redirect(updated.get_absolute_url())
    else:
        form = ProjectForm(instance=project)
    return render(
        request, "projects/create-project.html", {"form": form, "is_edit": True}
    )


@login_required(login_url="/users/login/")
def complete_project_view(request, project_id: int):
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Project not found"},
            status=HTTPStatus.NOT_FOUND,
        )
    if not _can_manage_project(request.user, project):
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)
    if project.status != Project.STATUS_OPEN:
        return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": project.status})


@login_required(login_url="/users/login/")
def toggle_participate_view(request, project_id: int):
    project = (
        Project.objects.prefetch_related("participants").filter(pk=project_id).first()
    )
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Project not found"},
            status=HTTPStatus.NOT_FOUND,
        )
    if request.user.id == project.owner_id:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)

    participant = project.participants.filter(pk=request.user.pk).exists()
    if participant:
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True
    return JsonResponse({"status": "ok", "participant": participant})


def project_skill_suggestions_view(request):
    query = request.GET.get("q", "").strip()
    skills = Skill.objects.all()
    if query:
        skills = skills.filter(name__istartswith=query)
    skills = skills.order_by("name").values("id", "name")[:SKILL_SUGGESTIONS_LIMIT]
    return JsonResponse(list(skills), safe=False)


@login_required(login_url="/users/login/")
def add_project_skill_view(request, project_id: int):
    project = Project.objects.prefetch_related("skills").filter(pk=project_id).first()
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Project not found"},
            status=HTTPStatus.NOT_FOUND,
        )
    if not _can_manage_project(request.user, project):
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)

    data = _json_body(request)
    skill = None
    created = False
    if data.get("skill_id"):
        skill = Skill.objects.filter(pk=data["skill_id"]).first()
        if skill is None:
            return JsonResponse(
                {"status": "error", "message": "Skill not found"},
                status=HTTPStatus.NOT_FOUND,
            )
    else:
        name = str(data.get("name", "")).strip()
        if not name:
            return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)
        skill = Skill.objects.filter(name__iexact=name).first()
        if skill is None:
            skill = Skill.objects.create(name=name)
            created = True

    added = False
    if skill and not project.skills.filter(pk=skill.pk).exists():
        project.skills.add(skill)
        added = True

    return JsonResponse(
        {
            "status": "ok",
            "skill_id": skill.pk,
            "id": skill.pk,
            "name": skill.name,
            "created": created,
            "added": added,
        }
    )


@login_required(login_url="/users/login/")
def remove_project_skill_view(request, project_id: int, skill_id: int):
    project = Project.objects.prefetch_related("skills").filter(pk=project_id).first()
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Project not found"},
            status=HTTPStatus.NOT_FOUND,
        )
    if not _can_manage_project(request.user, project):
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)

    skill = Skill.objects.filter(pk=skill_id).first()
    if skill is None:
        return JsonResponse(
            {"status": "error", "message": "Skill not found"},
            status=HTTPStatus.NOT_FOUND,
        )
    if not project.skills.filter(pk=skill.pk).exists():
        return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)
    project.skills.remove(skill)
    return JsonResponse({"status": "ok", "removed": True})
