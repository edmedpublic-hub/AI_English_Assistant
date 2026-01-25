from django.contrib import admin
from ..models.core import LessonChunk
from .actions import generate_vocab


@admin.register(LessonChunk)
class LessonChunkAdmin(admin.ModelAdmin):
    list_display = ("lesson", "order", "english_text")
    ordering = ("lesson", "order")
    actions = [generate_vocab]