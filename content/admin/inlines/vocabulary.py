# PATH: content/admin/inlines/vocabulary.py
# ACTION: Replace the entire existing file with this content.
# CHANGES FROM ORIGINAL:
#   - item_preview in ChunkVocabularyInline and VocabularyItemInline:
#     replaced format_html(f"...{variable}...") with mark_safe(html)
#     because format_html() calls .format() on the string which crashes
#     when any field value contains Arabic/Unicode characters like ﷺ
#     that include curly-brace-like codepoints.
#   - quick_preview in VocabularyItemQuickInline: same fix.
#   - Removed autocomplete_fields = ("lesson", "chunk") from both inlines
#     because autocomplete requires search_fields on the related ModelAdmin,
#     which is not guaranteed. Using raw_id_fields is safer, or just omitting.
#   - Everything else is unchanged.

from django.contrib import admin
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.urls import reverse
from content.models.vocabulary import VocabularyItem, StudentVocabMastery


# ═══════════════════════════════════════════════════════════════
#  SHARED HELPER
# ═══════════════════════════════════════════════════════════════

def _build_item_preview(obj, border_color="#6f42c1"):
    """
    Safely builds the vocabulary item preview HTML.
    Uses escape() on every user-supplied value so that Arabic text,
    special characters, and curly braces never break rendering.
    Returns a mark_safe string — safe because we escape all values.
    """
    if not obj.pk:
        return "Preview available after saving"

    parts = [
        f'<div style="background:#f8f9fa;padding:8px;border-radius:4px;'
        f'font-size:0.9em;border-left:4px solid {border_color};">',
        f'<p><strong>Word:</strong> {escape(obj.word)} '
        f'<em>({escape(obj.get_part_of_speech_display())})</em></p>',
    ]

    if obj.meaning:
        parts.append(
            f'<p><strong>Meaning:</strong> {escape(obj.meaning[:100])}</p>'
        )
    if obj.urdu:
        parts.append(
            f'<p><strong>اردو:</strong> {escape(obj.urdu)}</p>'
        )
    if obj.synonyms:
        parts.append(
            f'<p><strong>Synonyms:</strong> {escape(obj.synonyms[:100])}</p>'
        )
    if obj.antonyms:
        parts.append(
            f'<p><strong>Antonyms:</strong> {escape(obj.antonyms[:100])}</p>'
        )
    if obj.example_sentence:
        parts.append(
            f'<p><strong>Example:</strong> '
            f'<em>&#8220;{escape(obj.example_sentence[:100])}&#8221;</em></p>'
        )

    # Mastery stats
    mastery_count = StudentVocabMastery.objects.filter(
        vocab_item=obj, mastery_level='mastered'
    ).count()
    if mastery_count > 0:
        parts.append(
            f'<p style="color:green;">✓ Mastered by {mastery_count} student(s)</p>'
        )

    parts.append('</div>')
    return mark_safe("".join(parts))


# ═══════════════════════════════════════════════════════════════
#  CHUNK VOCABULARY INLINE  (used in LessonChunkAdmin)
# ═══════════════════════════════════════════════════════════════

class ChunkVocabularyInline(admin.TabularInline):
    """
    Appears inside LessonChunk admin.
    Primary vocabulary authoring surface for chunks.
    """
    model = VocabularyItem
    extra = 1
    min_num = 0
    max_num = 20
    verbose_name = "Vocabulary Item"
    verbose_name_plural = "Vocabulary Items"
    show_change_link = True

    fields = (
        "word",
        "part_of_speech",
        "urdu",
        "meaning",
        "synonyms",
        "antonyms",
        "example_sentence",
        "item_preview",
    )
    readonly_fields = ("item_preview",)
    ordering = ("word",)

    def item_preview(self, obj):
        return _build_item_preview(obj, border_color="#6f42c1")
    item_preview.short_description = "Preview"


# ═══════════════════════════════════════════════════════════════
#  VOCABULARY ITEM INLINE  (full version)
# ═══════════════════════════════════════════════════════════════

class VocabularyItemInline(admin.TabularInline):
    """
    Full inline for vocabulary editing inside LessonChunk.
    """
    model = VocabularyItem
    extra = 1
    min_num = 0
    max_num = 20
    show_change_link = True

    fields = (
        "word",
        "part_of_speech",
        "urdu",
        "meaning",
        "synonyms",
        "antonyms",
        "example_sentence",
        "item_preview",
    )
    readonly_fields = ("item_preview",)
    ordering = ("word",)

    def item_preview(self, obj):
        return _build_item_preview(obj, border_color="#0d6efd")
    item_preview.short_description = "Preview"


# ═══════════════════════════════════════════════════════════════
#  VOCABULARY ITEM QUICK INLINE  (minimal, fast entry)
# ═══════════════════════════════════════════════════════════════

class VocabularyItemQuickInline(admin.TabularInline):
    """
    Simplified inline for quick vocabulary entry.
    """
    model = VocabularyItem
    extra = 1
    min_num = 0
    max_num = 20

    fields = (
        "word",
        "part_of_speech",
        "urdu",
        "quick_preview",
    )
    readonly_fields = ("quick_preview",)
    ordering = ("word",)

    def quick_preview(self, obj):
        if not obj.pk:
            return ""
        parts = [f'<span style="color:#666;">{escape(obj.word)}']
        if obj.urdu:
            parts.append(f" | اردو: {escape(obj.urdu)}")
        parts.append("</span>")
        return mark_safe("".join(parts))
    quick_preview.short_description = "Preview"


# ═══════════════════════════════════════════════════════════════
#  STUDENT MASTERY INLINE  (read-only analytics)
# ═══════════════════════════════════════════════════════════════

class StudentVocabMasteryInline(admin.TabularInline):
    """
    Read-only inline showing which students have mastered a vocabulary item.
    """
    model = StudentVocabMastery
    extra = 0
    readonly_fields = [
        'user', 'mastery_level', 'accuracy_display',
        'total_attempts', 'correct_attempts', 'last_practiced',
    ]
    fields = [
        'user', 'mastery_level', 'accuracy_display',
        'total_attempts', 'last_practiced',
    ]
    ordering = ['-last_practiced']
    can_delete = False
    verbose_name = "Student Mastery Record"
    verbose_name_plural = "Student Mastery Records"

    def accuracy_display(self, obj):
        accuracy = obj.accuracy_percentage
        colour = (
            '#28a745' if accuracy >= 80
            else '#fd7e14' if accuracy >= 50
            else '#dc3545'
        )
        return format_html(
            '<span style="color:{};font-weight:bold;">{}%</span>',
            colour, accuracy,
        )
    accuracy_display.short_description = "Accuracy"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'ChunkVocabularyInline',
    'VocabularyItemInline',
    'VocabularyItemQuickInline',
    'StudentVocabMasteryInline',
]