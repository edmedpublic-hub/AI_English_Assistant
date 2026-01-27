from django.contrib import admin
from content.models.core import Textbook, Unit, Lesson, LessonChunk

# Import inlines from other domains
from content.admin.inlines.grammar import ChunkGrammarFocusInline
from content.admin.inlines.comprehension import ComprehensionQuestionInline, LessonChunkInline
# later:
# from content.admin.inlines.vocabulary import ChunkVocabularyInline


# -----------------------------
# Textbook
# -----------------------------
@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display = ("title", "class_level")
    search_fields = ("title", "class_level")


# -----------------------------
# Unit
# -----------------------------
@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("title", "number", "textbook")
    list_filter = ("textbook",)
    ordering = ("textbook", "number")


# -----------------------------
# Lesson
# -----------------------------
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "number", "unit")
    list_filter = ("unit",)
    ordering = ("unit", "number")

    inlines = [
        LessonChunkInline,
        ComprehensionQuestionInline,
    ]


# -----------------------------
# LessonChunk (your main editor)
# -----------------------------
@admin.register(LessonChunk)
class LessonChunkAdmin(admin.ModelAdmin):
    list_display = ("lesson", "order", "short_text")
    ordering = ("lesson", "order")

    # This is the key: everything flows through the chunk
    inlines = [
        ChunkGrammarFocusInline,
        # ChunkVocabularyInline will go here next
    ]

    def short_text(self, obj):
        return obj.english_text[:60]

    short_text.short_description = "Chunk preview"