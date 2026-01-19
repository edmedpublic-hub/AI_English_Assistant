from django.urls import path
from content import views

urlpatterns = [
    # Practice hub
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/vocabulary/practice/",
        views.chunk_vocabulary_practice,
        name="chunk_vocabulary_practice",
    ),

    # Test
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/vocabulary/test/",
        views.chunk_vocabulary_test,
        name="chunk_vocabulary_test",
    ),

    # Dedicated practice types
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/vocabulary/fill/",
        views.chunk_vocab_fill,
        name="chunk_vocab_fill",
    ),
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/vocabulary/synonyms/",
        views.chunk_vocab_synonyms,
        name="chunk_vocab_synonyms",
    ),
    path(
        "lesson/<int:lesson_id>/chunk/<int:chunk_id>/vocabulary/antonyms/",
        views.chunk_vocab_antonyms,
        name="chunk_vocab_antonyms",
    ),
]
