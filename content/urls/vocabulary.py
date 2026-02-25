# content/urls/vocabulary.py

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

# No app_name here because it's already under the 'content' namespace

urlpatterns = [
    # Leave the path empty "" because the parent URL (core/chunk_urls) 
    # already handles the "<int:chunk_id>/vocabulary/" part.
    path("", chunk_vocabulary, name="chunk_vocabulary_hub"),
    
    path("practice/", chunk_vocabulary_practice, name="practice"),
    path("fill/", chunk_vocab_fill, name="fill"),
    path("synonyms/", chunk_vocab_synonyms, name="synonyms"),
    path("antonyms/", chunk_vocab_antonyms, name="antonyms"),
    path("test/", chunk_vocabulary_test, name="test"),
    path("history/", test_history, name="history"),
    path("attempt/<int:attempt_id>/", attempt_detail, name="attempt-detail"),
]