# translation/urls.py

from django.urls import path
from .views import (
    translation_home,
    translation_textbook_units,
    translation_unit_lessons,
    translation_player,
)

app_name = "translation"

urlpatterns = [
    # Homepage
    path(
        "",
        translation_home,
        name="translation-home",
    ),

    # Textbook units
    path(
        "textbooks/<slug:slug>/",
        translation_textbook_units,
        name="translation-textbook-units",
    ),

    # Unit lessons
    path(
        "units/<uuid:unit_id>/",
        translation_unit_lessons,
        name="translation-unit-lessons",
    ),

    # Lesson player
    path(
        "player/<uuid:lesson_id>/",
        translation_player,
        name="translation-player",
    ),
]