from django.urls import path
from content.views.core import (
    content_index,
    textbook_list,
    textbook_detail,
    unit_detail,
    lesson_detail,
)
from content.views.chunk_core import chunk_hub

app_name = "core"  # ✅ namespace for reverse lookups

urlpatterns = [
    # Entry
    path("", content_index, name="content_index"),

    # Textbooks
    path("textbooks/", textbook_list, name="textbook_list"),
    path("textbooks/<int:pk>/", textbook_detail, name="textbook_detail"),

    # Units (inside textbook)
    path("units/<int:pk>/", unit_detail, name="unit_detail"),

    # Lessons (inside unit)
    path("lessons/<int:pk>/", lesson_detail, name="lesson_detail"),

    # Chunk hub (learning entry point)
    path("chunks/<int:chunk_id>/", chunk_hub, name="chunk_hub"),
]