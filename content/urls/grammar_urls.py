# urls/grammar_urls.py

from django.urls import path
from content.views.grammar_views import (
    grammar_teach,
    grammar_exercise,
    grammar_test,
)

app_name = "grammar"

urlpatterns = [
    path("<int:lesson_id>/<int:chunk_id>/<int:point_id>/teach/", grammar_teach, name="teach"),
    path("<int:lesson_id>/<int:chunk_id>/<int:point_id>/exercise/", grammar_exercise, name="exercise"),
    path("<int:lesson_id>/<int:chunk_id>/<int:point_id>/test/", grammar_test, name="test"),
]