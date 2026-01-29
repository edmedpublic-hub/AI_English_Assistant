from django.urls import path
from content.views import (
    chunk_vocabulary,
    chunk_vocabulary_practice,
    chunk_vocabulary_test,
    chunk_vocab_fill,
    chunk_vocab_synonyms,
    chunk_vocab_antonyms,
)

urlpatterns = [
    # Vocabulary Hub
    path("chunks/<int:chunk_id>/vocabulary/", chunk_vocabulary, name="chunk_vocabulary"),

    # Practice hub
    path("chunks/<int:chunk_id>/vocabulary/practice/", chunk_vocabulary_practice, name="chunk_vocabulary_practice"),

    # Test
    path("chunks/<int:chunk_id>/vocabulary/test/", chunk_vocabulary_test, name="chunk_vocabulary_test"),

    # Dedicated practice types
    path("chunks/<int:chunk_id>/vocabulary/fill/", chunk_vocab_fill, name="chunk_vocab_fill"),
    path("chunks/<int:chunk_id>/vocabulary/synonyms/", chunk_vocab_synonyms, name="chunk_vocab_synonyms"),
    path("chunks/<int:chunk_id>/vocabulary/antonyms/", chunk_vocab_antonyms, name="chunk_vocab_antonyms"),
]