# reading/urls.py
from django.urls import path
from .views import (
    ReadingLessonListView,
    ReadingLessonDetailView,
    reading_home,
    reading_detail,
)

urlpatterns = [
    # --------------------
    # API Endpoints (JSON)
    # --------------------
    path("api/lessons/", ReadingLessonListView.as_view(), name="reading-lesson-list"),
    path("api/lessons/<int:pk>/", ReadingLessonDetailView.as_view(), name="reading-lesson-detail"),

    # --------------------
    # Template Pages
    # --------------------
    path("", reading_home, name="reading"),                      # /reading/
    path("<int:pk>/", reading_detail, name="reading-detail"),    # /reading/5/
]
