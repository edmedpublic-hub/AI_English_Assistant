# content/urls/grammar.py
from django.urls import path
from content.views.grammar import teach, practice, test

app_name = "grammar"

urlpatterns = [
    path("<int:focus_id>/teach/", teach.grammar_teach, name="teach"),
    path("<int:focus_id>/practice/", practice.grammar_practice, name="practice"),
    path("<int:focus_id>/test/", test.grammar_test, name="test"),
]