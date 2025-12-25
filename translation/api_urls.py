from django.urls import path
from .views import (
    TranslationTextbookListAPIView,
    TranslationTextbookDetailAPIView,
    TranslationUnitDetailAPIView,
    TranslationLessonDetailAPIView,
)

urlpatterns = [
    path(
        "textbooks/",
        TranslationTextbookListAPIView.as_view(),
        name="textbook-list",
    ),
    path(
        "textbooks/<slug:slug>/",
        TranslationTextbookDetailAPIView.as_view(),
        name="textbook-detail",
    ),
    path(
        "units/<uuid:pk>/",
        TranslationUnitDetailAPIView.as_view(),
        name="unit-detail",
    ),
    path(
        "lessons/<uuid:pk>/",
        TranslationLessonDetailAPIView.as_view(),
        name="lesson-detail",
    ),
]
