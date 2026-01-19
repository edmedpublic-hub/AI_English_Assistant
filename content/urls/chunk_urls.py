from django.urls import path
from content import views

urlpatterns = [
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
]
