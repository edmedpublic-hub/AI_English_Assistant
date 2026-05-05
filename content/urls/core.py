# content/urls/core.py
from django.urls import path, include
from content.views.core import (
    content_index,
    textbook_list,
    textbook_detail,
    unit_detail,
    lesson_detail,
)

urlpatterns = [
    path("", content_index, name="content_index"),
    path("textbooks/", textbook_list, name="textbook_list"),
    path("textbooks/<int:pk>/", textbook_detail, name="textbook_detail"),
    path("units/<int:pk>/", unit_detail, name="unit_detail"),
    path("lessons/<int:pk>/", lesson_detail, name="lesson_detail"),
    path("chunks/", include("content.urls.chunk_urls")),
]