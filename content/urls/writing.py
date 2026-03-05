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

app_name = "writing"

urlpatterns = [
    path("hub/", chunk_writing_view, name="hub"),
    path("<int:focus_id>/teach/", writing_teach, name="teach"),
    path("<int:focus_id>/practice/", writing_practice, name="practice"),
    path("<int:focus_id>/test/", writing_test, name="test"),
    path("<int:focus_id>/test/<int:attempt_id>/result/", writing_test_result_detail, name="test-result"),
    path("<int:focus_id>/test/history/", writing_test_history, name="test-history"),
]