from django.contrib import admin
from content.models.punctuation import ChunkPunctuationFocus, PunctuationQuestion


class ChunkPunctuationFocusInline(admin.StackedInline):
    """
    Appears inside LessonChunk admin.
    Primary punctuation authoring surface.
    """
    model = ChunkPunctuationFocus
    extra = 0
    show_change_link = True

    fields = (
        "mark",
        "focus_title",
        "focus_description",
        "depth_level",
        "sequence_order",
    )
    ordering = ("sequence_order",)


class PunctuationQuestionInline(admin.TabularInline):
    """
    Questions edited inside ChunkPunctuationFocus admin.
    """
    model = PunctuationQuestion
    extra = 1

    fields = (
        "question_text",
        "question_type",
        "options",
        "correct_answer",
        "difficulty",
        "explanation",
    )
    ordering = ("difficulty",)