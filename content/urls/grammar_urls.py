from django.urls import path

from content.views.grammar import hub, teach, practice, test


urlpatterns = [
    # Grammar Hub (per chunk)
    path(
        "chunks/<int:chunk_id>/grammar/",
        hub.chunk_grammar_view,
        name="chunk_grammar",
    ),

    # Grammar → Teach
    path(
        "chunks/<int:chunk_id>/grammar/<int:focus_id>/teach/",
        teach.grammar_teach,
        name="grammar_teach",
    ),

    # Grammar → Practice
    path(
        "chunks/<int:chunk_id>/grammar/<int:focus_id>/practice/",
        practice.grammar_practice,
        name="grammar_practice",
    ),

    # Grammar → Test
    path(
        "chunks/<int:chunk_id>/grammar/<int:focus_id>/test/",
        test.grammar_test,
        name="grammar_test",
    ),
]
