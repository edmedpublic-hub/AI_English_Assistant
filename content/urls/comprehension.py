# content/urls/comprehension.py

from django.urls import path

from content.views.comprehension import (
    chunk_comprehension_view,
    comprehension_teach_view,
    ComprehensionPracticeView,
    ComprehensionTestSubmitView,
    comprehension_result_view,
    comprehension_attempt_detail_view,
    comprehension_practice_result_view,
)


urlpatterns = [
    # --------------------------------------------------
    # HUB
    # --------------------------------------------------
    path(
        "hub/",
        chunk_comprehension_view,
        name="hub",
    ),

    # --------------------------------------------------
    # TEACH
    # --------------------------------------------------
    path(
        "<int:focus_id>/teach/",
        comprehension_teach_view,
        name="teach",
    ),

    # --------------------------------------------------
    # PRACTICE
    # --------------------------------------------------
    path(
        "<int:focus_id>/practice/",
        ComprehensionPracticeView.as_view(),
        name="practice",
    ),

    # --------------------------------------------------
    # PRACTICE RESULT
    # --------------------------------------------------
    path(
        "<int:focus_id>/practice/result/",
        comprehension_practice_result_view,
        name="practice-result",
    ),
    path(
        "<int:focus_id>/practice/result/<int:practice_id>/",
        comprehension_practice_result_view,
        name="practice-result-detail",
    ),

    # --------------------------------------------------
    # TEST SUBMISSION
    # --------------------------------------------------
    path(
        "<int:focus_id>/test/",
        ComprehensionTestSubmitView.as_view(),
        name="test",
    ),

    # --------------------------------------------------
    # TEST RESULT
    # --------------------------------------------------
    path(
        "<int:focus_id>/result/",
        comprehension_result_view,
        name="result",
    ),

    # --------------------------------------------------
    # ATTEMPT DETAIL (history browsing)
    # --------------------------------------------------
    path(
        "<int:focus_id>/attempt/<int:attempt_id>/",
        comprehension_attempt_detail_view,
        name="attempt-detail",
    ),
]