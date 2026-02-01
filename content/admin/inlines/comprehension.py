from django.contrib import admin
# LessonChunk is imported from core, while questions stay in comprehension
from content.models.core import LessonChunk
from content.models.comprehension import ComprehensionQuestion


class LessonChunkInline(admin.StackedInline):
    """
    Allows teachers to break English text into smaller,
    manageable chunks for students to read.
    """
    model = LessonChunk
    extra = 1
    fields = ("order", "content_english", "content_urdu")
    ordering = ("order",)


class ComprehensionQuestionInline(admin.TabularInline):
    """
    Appears inside Lesson admin.
    This is the main authoring interface for comprehension questions.
    """
    model = ComprehensionQuestion
    extra = 1
    fields = ("question", "answer")
    ordering = ("id",)