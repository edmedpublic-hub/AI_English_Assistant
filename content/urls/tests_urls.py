from django.urls import path
from content.views import test_history, attempt_detail

urlpatterns = [
    path("tests/history/", test_history, name="test_history"),
    path("tests/history/<int:attempt_id>/", attempt_detail, name="attempt_detail"),
]