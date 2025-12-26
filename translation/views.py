# translation/views.py

from django.shortcuts import render, get_object_or_404

from .models import (
    TranslationTextbook,
    TranslationUnit,
    TranslationLesson,
)


# ====================================================
# TEMPLATE VIEWS (HTML PAGES)
# ====================================================

def translation_home(request):
    """
    Landing page for the translation module.
    Lists all textbooks.
    """
    textbooks = TranslationTextbook.objects.all()

    return render(
        request,
        "translation/index.html",
        {"textbooks": textbooks},
    )


def translation_textbook_units(request, slug):
    """
    Show units belonging to a textbook.
    """
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
        {
            "textbook": textbook,
            "units": units,
        },
    )


def translation_unit_lessons(request, unit_id):
    """
    Show lessons belonging to a unit.
    """
    unit = get_object_or_404(
        TranslationUnit,
        id=unit_id,
    )

    lessons = unit.lessons.all()

    return render(
        request,
        "translation/lessons.html",
        {
            "unit": unit,
            "lessons": lessons,
        },
    )


def translation_player(request, lesson_id):
    """
    Lesson player view.
    """
    lesson = get_object_or_404(
        TranslationLesson,
        pk=lesson_id,
    )

    return render(
        request,
        "translation/player.html",
        {
            "lesson": lesson,
            "lesson_id": lesson.id,
            "unit": lesson.unit,
        },
    )
