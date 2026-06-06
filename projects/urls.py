from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("list/", views.project_list_view, name="list"),
    path("create-project/", views.create_project_view, name="create"),
    path("<int:project_id>/", views.project_detail_view, name="detail"),
    path("<int:project_id>/edit/", views.edit_project_view, name="edit"),
    path("<int:project_id>/complete/", views.complete_project_view, name="complete"),
    path(
        "<int:project_id>/toggle-participate/",
        views.toggle_participate_view,
        name="toggle-participate",
    ),
    path("skills/", views.project_skill_suggestions_view, name="skills"),
    path(
        "<int:project_id>/skills/add/", views.add_project_skill_view, name="skill-add"
    ),
    path(
        "<int:project_id>/skills/<int:skill_id>/remove/",
        views.remove_project_skill_view,
        name="skill-remove",
    ),
]
