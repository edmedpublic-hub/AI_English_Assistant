from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.permissions import AllowAny

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

# ====================================================
# TEMPLATE VIEWS (HTML PAGES)
# ====================================================

def translation_home(request):
    textbooks = TranslationTextbook.objects.all()
    return render(
        request,
        "translation/index.html",
        {"textbooks": textbooks},
    )


def translation_textbook_units(request, slug):
    textbook = get_object_or_404(
        TranslationTextbook,
        slug=slug,
    )
    units = (
        TranslationUnit.objects
        .filter(textbook=textbook)
        .order_by("unit_number", "id")
    )
    return render(
        request,
        "translation/units.html",
        {"textbook": textbook, "units": units},
    )


def translation_unit_lessons(request, unit_id):
    unit = get_object_or_404(
        TranslationUnit,
        id=unit_id,
    )
    lessons = unit.lessons.all()
    return render(
        request,
        "translation/lessons.html",
        {"unit": unit, "lessons": lessons},
    )


def translation_player(request, lesson_id):
    lesson = get_object_or_404(TranslationLesson, pk=lesson_id)
    return render(
        request,
        "translation/player.html",
        {
            "lesson": lesson,
            "lesson_id": lesson.id,
            "unit": lesson.unit,
        },
    )

# ====================================================
# API VIEWS (JSON ONLY)
# ====================================================

class TranslationTextbookListAPIView(generics.ListAPIView):
    queryset = TranslationTextbook.objects.all()
    serializer_class = TranslationTextbookSerializer
    permission_classes = [AllowAny]


class TranslationTextbookDetailAPIView(generics.RetrieveAPIView):
    queryset = TranslationTextbook.objects.all()
    serializer_class = TranslationTextbookSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class TranslationUnitDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve a single unit by primary key (UUID).
    URL kwarg: pk
    """
    queryset = TranslationUnit.objects.all()
    serializer_class = TranslationUnitSerializer
    # DRF default lookup_field = "pk"
    permission_classes = [AllowAny]


class TranslationLessonDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve a single lesson by primary key (UUID).
    URL kwarg: pk
    """
    queryset = TranslationLesson.objects.all()
    serializer_class = TranslationLessonSerializer
    # DRF default lookup_field = "pk"
    permission_classes = [AllowAny]
