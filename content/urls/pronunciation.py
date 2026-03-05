# content/urls/pronunciation.py
from django.urls import path
from content.views.pronunciation import (
    chunk_pronunciation_view,
    pronunciation_teach,
    pronunciation_practice,
    pronunciation_result,
)

app_name = "pronunciation"

urlpatterns = [
    path("hub/", chunk_pronunciation_view, name="hub"),
    path("<int:focus_id>/teach/", pronunciation_teach, name="teach"),
    path("<int:focus_id>/practice/", pronunciation_practice, name="practice"),
    path("<int:focus_id>/result/", pronunciation_result, name="result"),
]