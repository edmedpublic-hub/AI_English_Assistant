# D:\AI_English_Assistant\content\urls\vocabulary_urls.py
from django.urls import path
from content.views.vocabulary.hub import chunk_vocabulary
from content.views.vocabulary.practice import (
    chunk_vocabulary_practice,
    chunk_vocab_fill,
    chunk_vocab_synonyms,
    chunk_vocab_antonyms,
)
from content.views.vocabulary.test import (
    chunk_vocabulary_test,
    test_history,
    attempt_detail,
)

urlpatterns = [
    # Vocabulary Hub (The landing page)
    path("chunks/<int:chunk_id>/vocabulary/", chunk_vocabulary, name="chunk_vocabulary"),

    # Practice
    path("chunks/<int:chunk_id>/vocabulary/practice/", chunk_vocabulary_practice, name="chunk_vocabulary_practice"),
    path("chunks/<int:chunk_id>/vocabulary/fill/", chunk_vocab_fill, name="chunk_vocab_fill"),
    path("chunks/<int:chunk_id>/vocabulary/synonyms/", chunk_vocab_synonyms, name="chunk_vocab_synonyms"),
    path("chunks/<int:chunk_id>/vocabulary/antonyms/", chunk_vocab_antonyms, name="chunk_vocab_antonyms"),

    # Test
    path("chunks/<int:chunk_id>/vocabulary/test/", chunk_vocabulary_test, name="chunk_vocabulary_test"),
    path("vocabulary/history/", test_history, name="test_history"),
    path("vocabulary/attempt/<int:attempt_id>/", attempt_detail, name="attempt_detail"),
]