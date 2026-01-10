from django.urls import path
from . import views

urlpatterns = [
    # Core content navigation
    path("", views.index, name="content_index"),
    path("textbooks/", views.textbook_list, name="textbook_list"),
    path("textbooks/<int:pk>/", views.textbook_detail, name="textbook_detail"),
    path("units/", views.unit_list, name="unit_list"),
    path("units/<int:pk>/", views.unit_detail, name="unit_detail"),
    path("lessons/", views.lesson_list, name="lesson_list"),
    path("lessons/<int:pk>/", views.lesson_detail, name="lesson_detail"),
    path("chunks/<int:pk>/", views.chunk_detail, name="chunk_detail"),

    # Chunk study routes (all served from views/chunks.py)
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/vocabulary/",
        views.chunk_vocabulary,
        name="chunk_vocabulary",
    ),
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/grammar/",
        views.chunk_grammar,
        name="chunk_grammar",
    ),
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/comprehension/",
        views.chunk_comprehension,
        name="chunk_comprehension",
    ),
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/punctuation/",
        views.chunk_punctuation,
        name="chunk_punctuation",
    ),
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/writing/",
        views.chunk_writing,
        name="chunk_writing",
    ),
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/progress/",
        views.chunk_progress,
        name="chunk_progress",
    ),
    path(
    "lesson/<int:lesson_id>/chunk/<int:chunk_id>/vocabulary/practice/",
    views.chunk_vocabulary_practice,
    name="chunk_vocabulary_practice",
),
path(
    "lesson/<int:lesson_id>/chunk/<int:chunk_id>/vocabulary/test/",
    views.chunk_vocabulary_test,
    name="chunk_vocabulary_test",
),
]