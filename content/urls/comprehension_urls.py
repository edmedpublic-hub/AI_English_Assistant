# content/urls/comprehension_urls.py

from django.urls import path
from content.views.comprehension import hub, teach, practice, test

app_name = "comprehension"

urlpatterns = [
    path("<int:chunk_id>/hub/", hub.ComprehensionHubView.as_view(), name="hub"),
    path("<int:focus_id>/teach/", teach.ComprehensionTeachView.as_view(), name="teach"),
    path("<int:focus_id>/practice/", practice.ComprehensionPracticeView.as_view(), name="practice"),
    path("<int:student_id>/test/results/", test.ComprehensionTestResultsView.as_view(), name="test_results"),
]