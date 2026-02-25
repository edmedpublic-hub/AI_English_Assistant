# content/urls/punctuation.py

from django.urls import path
from content.views.punctuation import (
    chunk_punctuation_view,
    teach_punctuation_view,
    punctuation_practice,
    punctuation_test,
    punctuation_test_result,
    punctuation_attempt_detail,
)

urlpatterns = [
    # --------------------------------------------------
    # HUB
    # --------------------------------------------------
    path(
        "hub/",
        chunk_punctuation_view,
        name="hub",
    ),

    # --------------------------------------------------
    # TEACH
    # --------------------------------------------------
    path(
        "<int:focus_id>/teach/",
        teach_punctuation_view,
        name="teach",
    ),

    # --------------------------------------------------
    # PRACTICE
    # --------------------------------------------------
    path(
        "<int:focus_id>/practice/",
        punctuation_practice,
        name="practice",
    ),

    # --------------------------------------------------
    # TEST
    # --------------------------------------------------
    path(
        "<int:focus_id>/test/",
        punctuation_test,
        name="test",
    ),

    # --------------------------------------------------
    # TEST RESULT
    # --------------------------------------------------
    path(
        "<int:focus_id>/result/",
        punctuation_test_result,
        name="test_result",
    ),

    # --------------------------------------------------
    # ATTEMPT DETAIL
    # --------------------------------------------------
    path(
        "<int:focus_id>/attempt/<int:attempt_id>/",
        punctuation_attempt_detail,
        name="attempt-detail",
    ),
]