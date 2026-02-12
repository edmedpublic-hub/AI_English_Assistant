from django.urls import path
from content.views.grammar import teach, practice, test, hub

app_name = "grammar"

urlpatterns = [
    # Hub (focus list inside a chunk)
    path(
        "",
        hub.chunk_grammar_view,
        name="hub",
    ),

    # Focus-level routes
    path(
        "<int:focus_id>/teach/",
        teach.grammar_teach,
        name="teach",
    ),
    path(
        "<int:focus_id>/practice/",
        practice.grammar_practice,
        name="practice",
    ),
    path(
        "<int:focus_id>/test/",
        test.grammar_test,
        name="test",
    ),
]
