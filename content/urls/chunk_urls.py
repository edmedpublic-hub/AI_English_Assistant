# content/urls/chunk_urls.py

from django.urls import path, include

from content.views.chunk_core import chunk_hub
from content.views.grammar.hub import chunk_grammar_view
from content.views.punctuation.hub import chunk_punctuation_view
from content.views.comprehension.hub import chunk_comprehension_view
from content.views.progress.hub import chunk_progress_view
from content.views.pronunciation.hub import chunk_pronunciation_view

# Writing has moved to unit-level.
# There is no chunk-level writing view.
# Writing is accessed via the unit writing hub:
#   /content/units/<unit_id>/writing/
# The chunk_writing_view and chunk writing module
# are removed from chunk URLs.

urlpatterns = [
    # --------------------------------------------------
    # CORE CHUNK HUB
    # --------------------------------------------------
    path("<int:chunk_id>/", chunk_hub, name="chunk_hub"),

    # --------------------------------------------------
    # VOCABULARY
    # --------------------------------------------------
    path("<int:chunk_id>/vocabulary/", include("content.urls.vocabulary")),

    # --------------------------------------------------
    # GRAMMAR
    # --------------------------------------------------
    path("<int:chunk_id>/grammar/", chunk_grammar_view, name="chunk_grammar"),
    path(
        "<int:chunk_id>/grammar/module/",
        include(("content.urls.grammar", "grammar")),
    ),

    # --------------------------------------------------
    # PUNCTUATION
    # --------------------------------------------------
    path("<int:chunk_id>/punctuation/", chunk_punctuation_view, name="chunk_punctuation"),
    path(
        "<int:chunk_id>/punctuation/module/",
        include(("content.urls.punctuation", "punctuation")),
    ),

    # --------------------------------------------------
    # COMPREHENSION
    # --------------------------------------------------
    path("<int:chunk_id>/comprehension/", chunk_comprehension_view, name="chunk_comprehension"),
    path(
        "<int:chunk_id>/comprehension/module/",
        include(("content.urls.comprehension", "comprehension")),
    ),

    # --------------------------------------------------
    # WRITING — removed from chunk level.
    # Writing is now unit-level.
    # Access writing via:
    #   /content/units/<unit_id>/writing/
    # --------------------------------------------------

    # --------------------------------------------------
    # PRONUNCIATION
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