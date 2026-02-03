from django.urls import path
from content.views.chunk_core import chunk_hub
from content.views.vocabulary.hub import chunk_vocabulary
from content.views.grammar.hub import chunk_grammar_view
from content.views.punctuation.hub import chunk_punctuation_view
from content.views.comprehension.hub import chunk_comprehension_view
from content.views.writing.hub import chunk_writing_view
from content.views.progress.hub import chunk_progress_view

urlpatterns = [
    path("<int:chunk_id>/", chunk_hub, name="chunk_hub"),
    path("<int:chunk_id>/vocabulary/", chunk_vocabulary, name="chunk_vocabulary"),
    path("<int:chunk_id>/grammar/", chunk_grammar_view, name="chunk_grammar"),
    path("<int:chunk_id>/punctuation/", chunk_punctuation_view, name="chunk_punctuation"),
    path("<int:chunk_id>/comprehension/", chunk_comprehension_view, name="chunk_comprehension"),
    path("<int:chunk_id>/writing/", chunk_writing_view, name="chunk_writing"),
    path("<int:chunk_id>/progress/", chunk_progress_view, name="chunk_progress"),
]