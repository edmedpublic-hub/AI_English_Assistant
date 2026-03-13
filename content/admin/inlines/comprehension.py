# PATH: content/admin/inlines/comprehension.py
# ACTION: Replace the entire existing file with this content.
# CHANGES FROM ORIGINAL:
#   - focus_preview in ChunkComprehensionFocusInline: replaced
#     format_html(f-string) with escape() + mark_safe() to prevent
#     KeyError crash when chunk text contains Arabic/Unicode characters.
#     Also added "✏ Open Focus Editor" button matching punctuation pattern.
#   - question_preview in ComprehensionQuestionInline and
#     ComprehensionQuestionStackedInline: same unsafe format_html fix.
#   - All analytics inlines, exports: UNCHANGED.

from django.contrib import admin
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.urls import reverse
from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionQuestion,
    ComprehensionPracticeAttempt,
    ComprehensionTestAttempt,
    ComprehensionQuestionAttempt,
    BloomLevel,
)


# ═══════════════════════════════════════════════════════════════
#  SHARED HELPERS
# ═══════════════════════════════════════════════════════════════

LEVEL_COLOURS = {
    'literal':     '#28a745',
    'inferential': '#fd7e14',
    'evaluative':  '#dc3545',
}

EXPECTED_ORDER = {
    'literal': 1,
    'inferential': 2,
    'evaluative': 3,
}


def _question_preview_html(obj):
    """
    Safely builds question preview HTML using escape() on all user values.
    Returns a mark_safe string.
    """
    if not obj.pk:
        return "Preview available after saving"

    parts = [
        '<div style="background:#f8f9fa;padding:12px;border-radius:6px;'
        'border-left:4px solid #007bff;">',
        f'<p style="font-weight:bold;margin-bottom:8px;">'
        f'📝 {escape(obj.question_text)}</p>',
    ]

    if obj.question_type == 'mcq' and obj.options:
        options = obj.get_options_list()
        parts.append('<div style="margin-left:20px;">')
        for i, opt in enumerate(options, 1):
            escaped_opt = escape(opt)
            if opt == obj.correct_answer:
                parts.append(
                    f'<p style="color:#28a745;">✓ {i}. {escaped_opt} (correct)</p>'
                )
            else:
                parts.append(f'<p style="color:#666;">{i}. {escaped_opt}</p>')
        parts.append('</div>')
    elif obj.question_type == 'true_false':
        parts.append(
            f'<p><strong>Correct Answer:</strong> '
            f'<span style="color:#28a745;">{escape(obj.correct_answer or "")}</span></p>'
        )
    else:
        parts.append(
            f'<p><strong>Answer:</strong> {escape(obj.correct_answer or "")}</p>'
        )

    if obj.explanation:
        parts.append(
            f'<p style="margin-top:8px;padding-top:8px;border-top:1px dashed #ccc;">'
            f'<em>💡 {escape(obj.explanation[:120])}</em></p>'
        )

    parts.append('</div>')
    return mark_safe("".join(parts))


# ═══════════════════════════════════════════════════════════════
#  CHUNK COMPREHENSION FOCUS INLINE  (inside LessonChunkAdmin)
# ═══════════════════════════════════════════════════════════════

class ChunkComprehensionFocusInline(admin.StackedInline):
    """
    Appears inside LessonChunk admin.
    Shows Bloom's level, question count, and a direct link to the focus editor.
    """
    model = ChunkComprehensionFocus
    extra = 0
    min_num = 0
    max_num = 3
    show_change_link = True

    fieldsets = (
        ('Comprehension Focus', {
            'fields': (
                'focus_title',
                'focus_description',
                'level',
                'depth_level',
                'sequence_order',
            ),
        }),
        ('Content Status', {
            'fields': ('focus_status_panel',),
            'description': (
                'Questions are managed on the Focus edit page. '
                'Use the button below to open it directly.'
            ),
        }),
    )

    readonly_fields = ('focus_status_panel',)
    ordering = ('sequence_order',)

    def focus_status_panel(self, obj):
        if not obj.pk:
            return mark_safe(
                '<span style="color:#6c757d;">Save the chunk first, '
                'then return here to manage questions.</span>'
            )

        question_count = obj.questions.count()
        level_colour   = LEVEL_COLOURS.get(obj.level, '#6c757d')
        level_display  = escape(obj.get_level_display())

        # Question count RAG
        q_colour = (
            "#28a745" if question_count >= 3
            else "#fd7e14" if question_count >= 1
            else "#dc3545"
        )
        q_icon = (
            "✓" if question_count >= 3
            else "~" if question_count >= 1
            else "✗"
        )
        q_warning = (
            "" if question_count >= 3
            else (
                "&nbsp;<span style='color:#856404;background:#fff3cd;"
                "padding:1px 6px;border-radius:3px;font-size:0.85em;'>"
                "⚠ need ≥ 3</span>"
            )
        )

        # Sequence order validation warning
        seq_warning = ""
        if obj.level and obj.sequence_order != EXPECTED_ORDER.get(obj.level):
            expected = EXPECTED_ORDER.get(obj.level, "?")
            seq_warning = (
                f'<div style="color:#721c24;background:#f8d7da;padding:4px 8px;'
                f'border-radius:4px;margin-top:8px;font-size:0.85em;">'
                f'⚠ Sequence order should be {expected} for {level_display} level'
                f'</div>'
            )

        focus_url = reverse(
            'admin:content_chunkcomprehensionfocus_change', args=[obj.pk]
        )

        html = (
            f'<div style="background:#f8f9fa;padding:12px;border-radius:6px;'
            f'border-left:4px solid {level_colour};font-size:0.9em;">'
            f'<div style="margin-bottom:8px;">'
            f'<strong>Bloom\'s Level:</strong> '
            f'<span style="color:{level_colour};font-weight:600;">{level_display}</span>'
            f'</div>'
            f'<table style="border-collapse:collapse;width:100%;margin-bottom:10px;">'
            f'<tr>'
            f'<td style="padding:3px 10px 3px 0;width:120px;">Questions</td>'
            f'<td>'
            f'<span style="color:{q_colour};font-weight:bold;">{q_icon} {question_count}</span>'
            f'{q_warning}'
            f'</td>'
            f'</tr>'
            f'</table>'
            f'{seq_warning}'
            f'<a href="{focus_url}" '
            f'style="display:inline-block;padding:5px 14px;background:#17a2b8;'
            f'color:#fff;border-radius:4px;text-decoration:none;'
            f'font-size:0.85em;font-weight:600;margin-top:6px;">'
            f'✏ Open Focus Editor (add questions)'
            f'</a>'
            f'</div>'
        )
        return mark_safe(html)
    focus_status_panel.short_description = "Questions & Status"


# ═══════════════════════════════════════════════════════════════
#  COMPREHENSION QUESTION INLINE — Tabular  (inside FocusAdmin)
# ═══════════════════════════════════════════════════════════════

class ComprehensionQuestionInline(admin.TabularInline):
    model = ComprehensionQuestion
    extra = 1
    min_num = 0
    max_num = 15
    show_change_link = True

    fields = (
        "question_text",
        "question_type",
        "difficulty",
        "correct_answer",
        "options",
        "question_preview",
    )
    readonly_fields = ("question_preview",)
    ordering = ("difficulty", "id")

    def question_preview(self, obj):
        return _question_preview_html(obj)
    question_preview.short_description = "Preview"


# ═══════════════════════════════════════════════════════════════
#  COMPREHENSION QUESTION INLINE — Stacked  (alternative)
# ═══════════════════════════════════════════════════════════════

class ComprehensionQuestionStackedInline(admin.StackedInline):
    model = ComprehensionQuestion
    extra = 1
    min_num = 0
    max_num = 10

    fieldsets = (
        ('Question', {
            'fields': ('question_text', 'question_type', 'difficulty'),
        }),
        ('Answer', {
            'fields': ('options', 'correct_answer', 'explanation'),
            'description': 'For MCQ: One option per line',
        }),
        ('Preview', {
            'fields': ('question_preview',),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('question_preview',)
    ordering = ('difficulty', 'id')

    def question_preview(self, obj):
        return _question_preview_html(obj)
    question_preview.short_description = "Student View"


# ═══════════════════════════════════════════════════════════════
#  ANALYTICS INLINES  (unchanged)
# ═══════════════════════════════════════════════════════════════

class ComprehensionPracticeAttemptInline(admin.TabularInline):
    model = ComprehensionPracticeAttempt
    extra = 0
    readonly_fields = [
        'user', 'attempt_number', 'cycle_number',
        'score_percent', 'is_passed', 'attempted_at',
    ]
    fields = [
        'user', 'attempt_number', 'cycle_number',
        'score_percent', 'is_passed', 'attempted_at',
    ]
    ordering = ['-attempted_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ComprehensionTestAttemptInline(admin.TabularInline):
    model = ComprehensionTestAttempt
    extra = 0
    readonly_fields = [
        'user', 'attempt_number', 'cycle_number',
        'score_percent', 'is_mastered', 'created_at',
    ]
    fields = [
        'user', 'attempt_number', 'cycle_number',
        'score_percent', 'is_mastered', 'created_at',
    ]
    ordering = ['-created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ComprehensionQuestionAttemptInline(admin.TabularInline):
    model = ComprehensionQuestionAttempt
    extra = 0
    readonly_fields = [
        'user', 'cycle_number', 'attempt_number',
        'selected_answer', 'open_ended_answer',
        'is_correct', 'attempted_at',
    ]
    fields = [
        'user', 'cycle_number', 'attempt_number',
        'is_correct', 'attempted_at',
    ]
    ordering = ['-attempted_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'ChunkComprehensionFocusInline',
    'ComprehensionQuestionInline',
    'ComprehensionQuestionStackedInline',
    'ComprehensionPracticeAttemptInline',
    'ComprehensionTestAttemptInline',
    'ComprehensionQuestionAttemptInline',
]