# content/urls/writing.py

from django.urls import path
from content.views.writing import (
    chunk_writing_view,
    writing_teach,
    writing_practice,
    writing_test,
    writing_test_result_detail,
    writing_test_history,
)

urlpatterns = [
    # --------------------------------------------------
    # HUB
    # --------------------------------------------------
    path(
        "hub/",
        chunk_writing_view,
        name="hub",
    ),

    # --------------------------------------------------
    # TEACH
    # --------------------------------------------------
    path(
        "<int:focus_id>/teach/",
        writing_teach,
        name="teach",
    ),

    # --------------------------------------------------
    # PRACTICE
    # --------------------------------------------------
    path(
        "<int:focus_id>/practice/",
        writing_practice,
        name="practice",
    ),

    # --------------------------------------------------
    # TEST
    # --------------------------------------------------
    path(
        "<int:focus_id>/test/",
        writing_test,
        name="test",
    ),

    # --------------------------------------------------
    # TEST RESULT DETAIL
    # --------------------------------------------------
    path(
        "<int:focus_id>/test/<int:attempt_id>/result/",
        writing_test_result_detail,
        name="test-result",
    ),

    # --------------------------------------------------
    # TEST HISTORY
    # --------------------------------------------------
    path(
        "<int:focus_id>/test/history/",
        writing_test_history,
        name="test-history",
    ),
]