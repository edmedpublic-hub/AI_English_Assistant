from django.urls import path
from content import views
from content.views import history_views

urlpatterns = [
    path("tests/history/", views.test_history, name="test_history"),

    path(
        "tests/history/<int:attempt_id>/",
        history_views.attempt_detail,
        name="attempt_detail",
    ),
]
