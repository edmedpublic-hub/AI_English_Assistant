# PATH: content/urls/comprehension.py
# ACTION: Replace the entire existing file with this content.
#
# CHANGES FROM ORIGINAL:
#   - Renamed "result" → "test-result" to match template references
#   - ComprehensionPracticeView is now the HTML view (LoginRequiredMixin + View)
#     so it correctly handles both GET (render form) and POST (score + redirect)
#   - ComprehensionTestSubmitView handles GET (render test.html) + POST (score)
#     GET handler added below in test.py note
#   - All names now consistent with template {% url %} tags:
#       content:comprehension:hub
#       content:comprehension:teach
#       content:comprehension:practice
#       content:comprehension:practice-result
#       content:comprehension:practice-result-detail
#       content:comprehension:test
#       content:comprehension:test-result
#       content:comprehension:attempt-detail

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

app_name = "comprehension"

urlpatterns = [
    # Hub
    path(
        "hub/",
        chunk_comprehension_view,
        name="hub",
    ),

    # Teach
    path(
        "<int:focus_id>/teach/",
        comprehension_teach_view,
        name="teach",
    ),

    # Practice (GET = render form, POST = score + redirect)
    path(
        "<int:focus_id>/practice/",
        ComprehensionPracticeView.as_view(),
        name="practice",
    ),

    # Practice results
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

    # Test (GET = render form, POST = score + redirect)
    path(
        "<int:focus_id>/test/",
        ComprehensionTestSubmitView.as_view(),
        name="test",
    ),

    # Test result  ← was "result", templates reference "test-result"
    path(
        "<int:focus_id>/test-result/",
        comprehension_result_view,
        name="test-result",
    ),

    # Specific attempt detail (history browsing)
    path(
        "<int:focus_id>/attempt/<int:attempt_id>/",
        comprehension_attempt_detail_view,
        name="attempt-detail",
    ),
]