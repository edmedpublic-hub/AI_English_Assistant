# translation/api_urls.py

from django.urls import path

from .api_views import (
    TranslationTextbookListAPIView,
    TranslationTextbookDetailAPIView,
    TranslationUnitDetailAPIView,
    TranslationLessonDetailAPIView,
)

urlpatterns = [
    path(
        "textbooks/",
        TranslationTextbookListAPIView.as_view(),
        name="translation-textbook-list",
    ),
    path(
        "textbooks/<slug:slug>/",
        TranslationTextbookDetailAPIView.as_view(),
        name="translation-textbook-detail",
    ),
    path(
        "units/<uuid:pk>/",
        TranslationUnitDetailAPIView.as_view(),
        name="translation-unit-detail",
    ),
    path(
        "lessons/<uuid:pk>/",
        TranslationLessonDetailAPIView.as_view(),
        name="translation-lesson-detail",
    ),
]
