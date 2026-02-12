# content/urls/chunk_urls.py
from django.urls import path, include
from content.views.chunk_core import chunk_hub
from content.views.vocabulary.hub import chunk_vocabulary
from content.views.grammar.hub import chunk_grammar_view
from content.views.punctuation.hub import chunk_punctuation_view
from content.views.comprehension.hub import ComprehensionHubView
from content.views.writing.hub import chunk_writing_view
from content.views.progress.hub import chunk_progress_view

urlpatterns = [
    path("<int:chunk_id>/", chunk_hub, name="chunk_hub"),
    path("<int:chunk_id>/vocabulary/", chunk_vocabulary, name="chunk_vocabulary"),

    # Grammar hub
    path("<int:chunk_id>/grammar/", chunk_grammar_view, name="chunk_grammar"),
    # Grammar focus-level routes (teach, practice, test)
    path(
        "<int:chunk_id>/grammar/",
        include(("content.urls.grammar_urls", "grammar"), namespace="grammar")
    ),

    # Punctuation hub
    path("<int:chunk_id>/punctuation/", chunk_punctuation_view, name="chunk_punctuation"),
    # Punctuation focus-level routes (teach, practice, test)
    path(
        "<int:chunk_id>/punctuation/",
        include(("content.urls.punctuation", "punctuation"), namespace="punctuation")
    ),

    path("<int:chunk_id>/comprehension/", ComprehensionHubView.as_view(), name="chunk_comprehension"),
    path("<int:chunk_id>/writing/", chunk_writing_view, name="chunk_writing"),
    path("<int:chunk_id>/progress/", chunk_progress_view, name="chunk_progress"),
]