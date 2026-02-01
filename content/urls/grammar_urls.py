from django.urls import path
# Import each module from the new grammar views package
from content.views.grammar import teach, exercise, test, hub

# Note: chunk_grammar_view (the hub) wasn't in your previous URL list, 
# but I've kept these consistent with your existing names.

urlpatterns = [
    # Grammar → Teach
    path(
        "chunks/<int:chunk_id>/grammar/<int:focus_id>/teach/",
        teach.grammar_teach,
        name="grammar_teach",
    ),

    # Grammar → Practice / Exercise
    path(
        "chunks/<int:chunk_id>/grammar/<int:focus_id>/exercise/",
        exercise.grammar_exercise,
        name="grammar_exercise",
    ),

    # Grammar → Test
    path(
        "chunks/<int:chunk_id>/grammar/<int:focus_id>/test/",
        test.grammar_test,
        name="grammar_test",
    ),
]