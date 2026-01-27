from django.contrib import admin
from content.models.grammar import ChunkGrammarFocus, GrammarQuestion


class ChunkGrammarFocusInline(admin.StackedInline):
    """
    Appears inside LessonChunk.
    Primary grammar authoring surface.
    """
    model = ChunkGrammarFocus
    extra = 0
    show_change_link = True

    fields = (
        "concept",
        "focus_title",
        "focus_description",
        "depth_level",
        "sequence_order",
    )
    ordering = ("sequence_order",)


class GrammarQuestionInline(admin.TabularInline):
    """
    Questions are edited inside ChunkGrammarFocus admin.
    """
    model = GrammarQuestion
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