from django.contrib import admin
from content.models.core import LessonChunk


class LessonChunkInline(admin.StackedInline):
    """
    Allows teachers to break English text into smaller,
    manageable chunks for students to read.
    """
    model = LessonChunk
    extra = 1
    fields = ("order", "content_english", "content_urdu")
    ordering = ("order",)