# content/admin/core.py

from django.contrib import admin
from django.utils.html import format_html
from content.models.core import Textbook, Unit, Lesson, LessonChunk

# Import inlines from all domains
from content.admin.inlines.grammar import ChunkGrammarFocusInline
from content.admin.inlines.punctuation import ChunkPunctuationFocusInline
from content.admin.inlines.comprehension import ChunkComprehensionFocusInline
from content.admin.inlines.vocabulary import ChunkVocabularyInline
from content.admin.inlines.pronunciation import ChunkPronunciationFocusInline
from content.admin.inlines.core import LessonChunkInline

# Writing inline — now unit-level, not chunk-level
from content.admin.inlines.writing import WritingStageContentInline


# ============================================================
# TEXTBOOK ADMIN
# ============================================================

@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display  = ("title", "class_level", "unit_count", "created_at")
    list_filter   = ("class_level",)
    search_fields = ("title", "description", "class_level")
    ordering      = ("class_level", "title")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "class_level", "description")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def unit_count(self, obj):
        count = obj.units.count()
        return format_html(
            '<b>{}</b> unit{}', count, 's' if count != 1 else ''
        )
    unit_count.short_description = "Units"


# ============================================================
# UNIT ADMIN
# Writing stage content is entered here — one record
# per stage per unit. This is the content authoring surface.
# ============================================================

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display  = ("title", "number", "textbook", "lesson_count", "created_at")
    list_filter   = ("textbook",)
    search_fields = ("title", "textbook__title", "description")
    ordering      = ("textbook", "number")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("textbook", "number", "title", "description")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # Writing stage content lives here now
    inlines = [WritingStageContentInline]

    def lesson_count(self, obj):
        count = obj.lessons.count()
        return format_html(
            '<b>{}</b> lesson{}', count, 's' if count != 1 else ''
        )
    lesson_count.short_description = "Lessons"


# ============================================================
# LESSON ADMIN
# ============================================================

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display  = ("title", "number", "unit", "chunk_count", "has_audio")
    list_filter   = ("unit__textbook", "unit")
    search_fields = ("title", "english_text", "unit__title")
    ordering      = ("unit", "number")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("unit", "number", "title")
        }),
        ("Content", {
            "fields": ("english_text", "translated_text", "audio_file"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    inlines = [LessonChunkInline]

    def chunk_count(self, obj):
        count = obj.chunks.count()
        return format_html(
            '<b>{}</b> chunk{}', count, 's' if count != 1 else ''
        )
    chunk_count.short_description = "Chunks"

    def has_audio(self, obj):
        return bool(obj.audio_file)
    has_audio.boolean = True
    has_audio.short_description = "Audio"


# ============================================================
# LESSON CHUNK ADMIN
# Writing has moved to unit level — no writing inline here.
# ============================================================

@admin.register(LessonChunk)
class LessonChunkAdmin(admin.ModelAdmin):
    list_display  = (
        "id", "lesson", "order",
        "text_preview", "focus_count", "audio_status"
    )
    list_filter   = (
        "lesson__unit__textbook", "lesson__unit", "lesson"
    )
    ordering      = ("lesson", "order")
    search_fields = (
        "english_text", "translated_text", "lesson__title"
    )
    readonly_fields = (
        "created_at", "updated_at", "focus_count_display"
    )

    fieldsets = (
        ("Lesson Context", {
            "fields": ("lesson", "order")
        }),
        ("Content", {
            "fields": (
                "english_text",
                "translated_text",
                "audio_file",
                "translated_audio_file",
            ),
        }),
        ("Metadata", {
            "fields": (
                "estimated_time_minutes",
                "focus_count_display",
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # Writing inline removed — writing is now unit-level
    inlines = [
        ChunkGrammarFocusInline,
        ChunkPunctuationFocusInline,
        ChunkComprehensionFocusInline,
        ChunkVocabularyInline,
        ChunkPronunciationFocusInline,
    ]

    def text_preview(self, obj):
        text = obj.english_text or ""
        return text[:60] + "..." if len(text) > 60 else text
    text_preview.short_description = "Preview"

    def focus_count(self, obj):
        """Count total focuses across all domains except writing."""
        count = (
            obj.grammar_focuses.count() +
            obj.punctuation_focuses.count() +
            obj.comprehension_focuses.count() +
            obj.vocab_items.count() +
            obj.pronunciation_focuses.count()
        )
        return count
    focus_count.short_description = "Total Focuses"

    def focus_count_display(self, obj):
        """Detailed breakdown of focuses by domain."""
        counts = {
            "Grammar":       obj.grammar_focuses.count(),
            "Punctuation":   obj.punctuation_focuses.count(),
            "Comprehension": obj.comprehension_focuses.count(),
            "Vocabulary":    obj.vocab_items.count(),
            "Pronunciation": obj.pronunciation_focuses.count(),
        }
        html = "<table style='width:100%'>"
        for domain, count in counts.items():
            colour = "green" if count > 0 else "gray"
            html += (
                f"<tr>"
                f"<td>{domain}:</td>"
                f"<td style='color:{colour};font-weight:bold'>"
                f"{count}</td>"
                f"</tr>"
            )
        html += "</table>"
        return format_html(html)
    focus_count_display.short_description = "Focuses by Domain"

    def audio_status(self, obj):
        if obj.audio_file and obj.translated_audio_file:
            return format_html(
                '<span style="color:green;">✓ Both</span>'
            )
        elif obj.audio_file:
            return format_html(
                '<span style="color:orange;">English only</span>'
            )
        elif obj.translated_audio_file:
            return format_html(
                '<span style="color:orange;">Urdu only</span>'
            )
        return format_html(
            '<span style="color:red;">✗ No audio</span>'
        )
    audio_status.short_description = "Audio"