from django.contrib import admin
from ..models.core import Lesson
from .inlines import LessonChunkInline, VocabularyInline, WritingTaskInline


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "unit", "number")
    list_filter = ("unit__textbook", "unit")
    search_fields = ("title", "english_text")
    ordering = ("unit", "number")
    inlines = [
        LessonChunkInline,
        VocabularyInline,
        WritingTaskInline,
    ]