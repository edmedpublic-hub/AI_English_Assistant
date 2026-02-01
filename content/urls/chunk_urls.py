from django.urls import path
from content.views.chunk_core import (
    chunk_hub,
    chunk_vocabulary,
    chunk_comprehension,
    chunk_punctuation,
    chunk_writing,
    chunk_progress,
)
from content.views.grammar.hub import chunk_grammar_view



urlpatterns = [
    path("<int:chunk_id>/", chunk_hub, name="chunk_hub"),
    path("<int:chunk_id>/vocabulary/", chunk_vocabulary, name="chunk_vocabulary"),
    path("<int:chunk_id>/grammar/", chunk_grammar_view, name="chunk_grammar"),
    path("<int:chunk_id>/comprehension/", chunk_comprehension, name="chunk_comprehension"),
    path("<int:chunk_id>/punctuation/", chunk_punctuation, name="chunk_punctuation"),
    path("<int:chunk_id>/writing/", chunk_writing, name="chunk_writing"),
    path("<int:chunk_id>/progress/", chunk_progress, name="chunk_progress"),
]