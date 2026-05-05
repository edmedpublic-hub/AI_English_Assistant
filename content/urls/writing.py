from django.urls import path
from content.views.writing import (
    WritingHubView, WritingTeachView, WritingTeachSubmitView,
    WritingPracticeView, WritingPracticeSubmitView,
    WritingInterventionFixView, WritingTestView,
    WritingTestSubmitView, WritingTestResultView,
)

urlpatterns = [
    path("unit/<int:unit_id>/", WritingHubView.as_view(), name="writing_hub"),
    path("unit/<int:unit_id>/stage/<int:stage_id>/teach/", WritingTeachView.as_view(), name="writing_teach"),
    path("unit/<int:unit_id>/stage/<int:stage_id>/teach/submit/", WritingTeachSubmitView.as_view(), name="writing_teach_submit"),
    path("unit/<int:unit_id>/stage/<int:stage_id>/practice/", WritingPracticeView.as_view(), name="writing_practice"),
    path("unit/<int:unit_id>/stage/<int:stage_id>/practice/submit/", WritingPracticeSubmitView.as_view(), name="writing_practice_submit"),
    path("intervention/<int:intervention_id>/fix/", WritingInterventionFixView.as_view(), name="writing_intervention_fix"),
    path("unit/<int:unit_id>/stage/<int:stage_id>/test/", WritingTestView.as_view(), name="writing_test"),
    path("unit/<int:unit_id>/stage/<int:stage_id>/test/submit/", WritingTestSubmitView.as_view(), name="writing_test_submit"),
    path("unit/<int:unit_id>/stage/<int:stage_id>/test/result/<int:attempt_id>/", WritingTestResultView.as_view(), name="writing_test_result"),
]