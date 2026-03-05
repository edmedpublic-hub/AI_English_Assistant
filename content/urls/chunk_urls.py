# content/urls/chunk_urls.py

from django.urls import path, include

from content.views.chunk_core import chunk_hub
from content.views.grammar.hub import chunk_grammar_view
from content.views.punctuation.hub import chunk_punctuation_view
from content.views.comprehension.hub import chunk_comprehension_view
from content.views.writing.hub import chunk_writing_view
from content.views.progress.hub import chunk_progress_view
from content.views.pronunciation.hub import chunk_pronunciation_view

urlpatterns = [
    # --------------------------------------------------
    # CORE CHUNK HUB
    # --------------------------------------------------
    path("<int:chunk_id>/", chunk_hub, name="chunk_hub"),

    # --------------------------------------------------
    # VOCABULARY
    # No namespace needed — vocabulary already has unique names
    # (chunk_vocabulary_hub, practice, fill, synonyms, antonyms,
    #  test, history, attempt-detail)
    # --------------------------------------------------
    path("<int:chunk_id>/vocabulary/", include("content.urls.vocabulary")),

    # --------------------------------------------------
    # GRAMMAR  →  content:grammar:teach / practice / test
    # --------------------------------------------------
    path("<int:chunk_id>/grammar/", chunk_grammar_view, name="chunk_grammar"),
    path(
        "<int:chunk_id>/grammar/module/",
        include(("content.urls.grammar", "grammar")),
    ),

    # --------------------------------------------------
    # PUNCTUATION  →  content:punctuation:teach / practice / test etc.
    # --------------------------------------------------
    path("<int:chunk_id>/punctuation/", chunk_punctuation_view, name="chunk_punctuation"),
    path(
        "<int:chunk_id>/punctuation/module/",
        include(("content.urls.punctuation", "punctuation")),
    ),

    # --------------------------------------------------
    # COMPREHENSION  →  content:comprehension:teach / practice / test etc.
    # --------------------------------------------------
    path("<int:chunk_id>/comprehension/", chunk_comprehension_view, name="chunk_comprehension"),
    path(
        "<int:chunk_id>/comprehension/module/",
        include(("content.urls.comprehension", "comprehension")),
    ),

    # --------------------------------------------------
    # WRITING  →  content:writing:teach / practice / test etc.
    # --------------------------------------------------
    path("<int:chunk_id>/writing/", chunk_writing_view, name="chunk_writing"),
    path(
        "<int:chunk_id>/writing/module/",
        include(("content.urls.writing", "writing")),
    ),

    # --------------------------------------------------
    # PRONUNCIATION  →  content:pronunciation:teach / practice / result etc.
    # --------------------------------------------------
    path("<int:chunk_id>/pronunciation/", chunk_pronunciation_view, name="chunk_pronunciation"),
    path(
        "<int:chunk_id>/pronunciation/module/",
        include(("content.urls.pronunciation", "pronunciation")),
    ),

    # --------------------------------------------------
    # PROGRESS
    # --------------------------------------------------
    path("<int:chunk_id>/progress/", chunk_progress_view, name="chunk_progress"),
]