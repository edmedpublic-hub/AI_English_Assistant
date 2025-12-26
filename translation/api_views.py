from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.db.models import Prefetch

from .models import (
    TranslationTextbook,
    TranslationUnit,
    TranslationLesson,
)

from .serializers import (
    TranslationTextbookSerializer,
    TranslationUnitSerializer,
    TranslationLessonSerializer,
)


# --------------------------------------------------
# Helpers / Base behaviours
# --------------------------------------------------

class PublicPermissionMixin:
    """
    Public-read API.
    Adjust if you later add authentication.
    """
    permission_classes = [AllowAny]


# --------------------------------------------------
# TEXTBOOK API VIEWS
# --------------------------------------------------

class TranslationTextbookListAPIView(PublicPermissionMixin, generics.ListAPIView):
    """
    GET /api/translation/textbooks/
    Returns all published & active textbooks (with lightweight units).
    """

    serializer_class = TranslationTextbookSerializer

    def get_queryset(self):
        return (
            TranslationTextbook.objects
            .filter(is_active=True, published=True)
            .prefetch_related(
                Prefetch(
                    "units",
                    queryset=TranslationUnit.objects.order_by("unit_number")
                )
            )
            .order_by("title")
        )


class TranslationTextbookDetailAPIView(PublicPermissionMixin, generics.RetrieveAPIView):
    """
    GET /api/translation/textbooks/<slug:slug>/
    Returns a single published & active textbook.
    """

    serializer_class = TranslationTextbookSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            TranslationTextbook.objects
            .filter(is_active=True, published=True)
            .prefetch_related(
                Prefetch(
                    "units",
                    queryset=TranslationUnit.objects.order_by("unit_number")
                )
            )
        )


# --------------------------------------------------
# UNIT API VIEWS
# --------------------------------------------------

class TranslationUnitDetailAPIView(PublicPermissionMixin, generics.RetrieveAPIView):
    """
    GET /api/translation/units/<uuid:pk>/
    Returns a unit and its published & active lessons (lightweight).
    """

    serializer_class = TranslationUnitSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return (
            TranslationUnit.objects
            .select_related("textbook")
            .prefetch_related(
                Prefetch(
                    "lessons",
                    queryset=(
                        TranslationLesson.objects
                        .filter(is_active=True, published=True)
                        .order_by("lesson_number")
                    )
                )
            )
        )


# --------------------------------------------------
# LESSON API VIEWS
# --------------------------------------------------

class TranslationLessonDetailAPIView(PublicPermissionMixin, generics.RetrieveAPIView):
    """
    GET /api/translation/lessons/<uuid:pk>/
    Returns a full published & active lesson.
    """

    serializer_class = TranslationLessonSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return (
            TranslationLesson.objects
            .select_related("unit", "unit__textbook")
            .filter(is_active=True, published=True)
        )
