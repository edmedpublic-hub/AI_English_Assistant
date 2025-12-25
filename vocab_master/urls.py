from django.urls import path
from .views import LessonListView, lesson_detail, learner_dashboard
from django.views.generic import TemplateView

app_name = "vocab_master"

urlpatterns = [
    # Home page (index.html)
    path("", TemplateView.as_view(template_name="index.html"), name="home"),

    # Lessons list
    path("lessons/", LessonListView.as_view(), name="lesson_list"),

    # Lesson detail
    path("lessons/<int:pk>/", lesson_detail, name="lesson_detail"),

    # Learner dashboard
    path("dashboard/", learner_dashboard, name="dashboard"),
]