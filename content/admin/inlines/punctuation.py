# PATH: content/admin/inlines/punctuation.py
# ACTION: Replace the entire existing file with this content.
# CHANGES FROM ORIGINAL:
#   - ChunkPunctuationFocusInline: added "Open Focus Editor" button so teachers
#     can jump directly to the focus edit page (with rules + questions) in one click.
#     The focus_preview now shows colour-coded rule/question counts and a
#     completeness score so gaps are visible without opening the focus.
#   - Everything else (PunctuationRuleInline, PunctuationExampleInline,
#     FocusRuleInline, PunctuationQuestionInline, attempt inlines) is UNCHANGED.

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from content.models.punctuation import (
    PunctuationRule,
    PunctuationExample,
    ChunkPunctuationFocus,
    ChunkPunctuationFocusRule,
    PunctuationQuestion,
    PunctuationPracticeAttempt,
    PunctuationTestAttempt,
)


# ── UNCHANGED ─────────────────────────────────────────────────────────────────

class PunctuationRuleInline(admin.TabularInline):
    model = PunctuationRule
    extra = 1
    fields = ("rule_text", "rule_preview")
    readonly_fields = ("rule_preview",)
    ordering = ("id",)
    show_change_link = True

    def rule_preview(self, obj):
        if not obj.pk:
            return ""
        return format_html('<span style="color:#666;">{}</span>', obj.rule_text[:100])
    rule_preview.short_description = "Preview"


class PunctuationExampleInline(admin.TabularInline):
    model = PunctuationExample
    extra = 1
    fields = ("sentence", "example_preview")
    readonly_fields = ("example_preview",)
    ordering = ("id",)
    show_change_link = True

    def example_preview(self, obj):
        if not obj.pk:
            return ""
        return format_html('<span style="color:#666;">{}</span>', obj.sentence[:80])
    example_preview.short_description = "Preview"


class FocusRuleInline(admin.TabularInline):
    model = ChunkPunctuationFocusRule
    extra = 1
    autocomplete_fields = ("rule",)
    ordering = ("order",)
    fields = ("rule", "order", "rule_preview")
    readonly_fields = ("rule_preview",)

    def rule_preview(self, obj):
        if not obj.pk or not obj.rule_id:
            return ""
        url = reverse('admin:content_punctuationrule_change', args=[obj.rule.id])
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            url, obj.rule.rule_text[:60]
        )
    rule_preview.short_description = "Rule Preview"


class PunctuationQuestionInline(admin.StackedInline):
    model = PunctuationQuestion
    extra = 1
    min_num = 0
    max_num = 10

    fieldsets = (
        ('Question', {
            'fields': ('question_text', 'question_type', 'difficulty')
        }),
        ('Answer Options', {
            'fields': ('options', 'correct_answer', 'explanation'),
            'description': (
                'For MCQ: Use pipe | separator. Example: Option A | Option B | Option C'
            )
        }),
        ('Preview', {
            'fields': ('question_preview',),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('question_preview',)
    ordering = ('difficulty', 'id')
    show_change_link = True

    def question_preview(self, obj):
        if not obj.pk:
            return "Preview available after saving"
        html = (
            '<div style="background:#f8f9fa;padding:12px;border-radius:6px;'
            'border-left:4px solid #007bff;">'
            f'<p style="font-weight:bold;margin-bottom:8px;">📝 {obj.question_text}</p>'
        )
        if obj.question_type == 'mcq' and obj.options:
            options = obj.options_list
            html += '<div style="margin-left:20px;">'
            for i, opt in enumerate(options, 1):
                if opt == obj.correct_answer:
                    html += f'<p style="color:#28a745;">✓ {i}. {opt} <span>(correct)</span></p>'
                else:
                    html += f'<p style="color:#666;">{i}. {opt}</p>'
            html += '</div>'
        else:
            html += (
                f'<p><strong>Correct Answer:</strong> '
                f'<span style="color:#28a745;">{obj.correct_answer}</span></p>'
            )
        if obj.explanation:
            html += (
                f'<p style="margin-top:8px;border-top:1px dashed #ccc;">'
                f'<em>💡 {obj.explanation}</em></p>'
            )
        html += '</div>'
        return format_html(html)
    question_preview.short_description = "Student View"


class PunctuationPracticeAttemptInline(admin.TabularInline):
    model = PunctuationPracticeAttempt
    extra = 0
    readonly_fields = [
        'user', 'attempt_number', 'cycle_number',
        'score_percent', 'is_passed', 'created_at',
    ]
    fields = [
        'user', 'attempt_number', 'cycle_number',
        'score_percent', 'is_passed', 'created_at',
    ]
    ordering = ['-created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class PunctuationTestAttemptInline(admin.TabularInline):
    model = PunctuationTestAttempt
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


# ── UPDATED ───────────────────────────────────────────────────────────────────

class ChunkPunctuationFocusInline(admin.StackedInline):
    """
    Shown inside LessonChunkAdmin.
    Now includes:
      • Colour-coded completeness panel (rules + questions with RAG status)
      • "Open Focus Editor" button → goes directly to ChunkPunctuationFocusAdmin
        change page where teacher can manage rules and questions without hunting
    """
    model = ChunkPunctuationFocus
    extra = 0
    min_num = 0
    max_num = 3
    show_change_link = True  # keeps the existing "change" link as well

    fieldsets = (
        ('Punctuation Focus', {
            'fields': (
                'mark', 'focus_title', 'focus_description',
                'depth_level', 'sequence_order',
            )
        }),
        ('Content Status', {
            'fields': ('focus_status_panel',),
            'description': (
                'Rules and questions are managed on the Focus edit page. '
                'Use the button below to open it directly.'
            ),
        }),
    )

    readonly_fields = ('focus_status_panel',)
    ordering = ('sequence_order',)
    autocomplete_fields = ('mark',)

    def focus_status_panel(self, obj):
        if not obj.pk:
            return format_html(
                '<span style="color:#6c757d;">Save the chunk first, '
                'then return here to manage rules and questions.</span>'
            )

        question_count = obj.questions.count()
        rule_count = obj.focus_rules.count()
        mark_name = obj.mark.name if obj.mark else "No mark selected"
        mark_symbol = obj.mark.symbol if obj.mark else ""

        # RAG colours
        rule_colour  = "#28a745" if rule_count >= 1  else "#dc3545"
        q_colour     = "#28a745" if question_count >= 3 else (
                       "#fd7e14" if question_count >= 1  else "#dc3545")
        rule_icon    = "✓" if rule_count >= 1    else "✗"
        q_icon       = "✓" if question_count >= 3 else ("~" if question_count >= 1 else "✗")

        # Direct link to the focus change page
        focus_url = reverse(
            'admin:content_chunkpunctuationfocus_change', args=[obj.pk]
        )

        html = f"""
        <div style="background:#f8f9fa;padding:12px;border-radius:6px;
                    border-left:4px solid #17a2b8;font-size:0.9em;">
            <div style="margin-bottom:8px;">
                <strong>{mark_symbol} {mark_name}</strong>
            </div>
            <table style="border-collapse:collapse;width:100%;margin-bottom:10px;">
                <tr>
                    <td style="padding:3px 10px 3px 0;width:120px;">Rules linked</td>
                    <td>
                        <span style="color:{rule_colour};font-weight:bold;">
                            {rule_icon} {rule_count}
                        </span>
                        {"" if rule_count else
                         "&nbsp;<span style='color:#856404;background:#fff3cd;"
                         "padding:1px 6px;border-radius:3px;font-size:0.85em;'>"
                         "⚠ none linked</span>"}
                    </td>
                </tr>
                <tr>
                    <td style="padding:3px 10px 3px 0;">Questions</td>
                    <td>
                        <span style="color:{q_colour};font-weight:bold;">
                            {q_icon} {question_count}
                        </span>
                        {"" if question_count >= 3 else
                         "&nbsp;<span style='color:#856404;background:#fff3cd;"
                         "padding:1px 6px;border-radius:3px;font-size:0.85em;'>"
                         "⚠ need ≥ 3</span>"}
                    </td>
                </tr>
            </table>
            <a href="{focus_url}"
               style="display:inline-block;padding:5px 14px;background:#17a2b8;
                      color:#fff;border-radius:4px;text-decoration:none;
                      font-size:0.85em;font-weight:600;">
                ✏ Open Focus Editor (add rules &amp; questions)
            </a>
        </div>
        """
        return format_html(html)
    focus_status_panel.short_description = "Rules & Questions"


__all__ = [
    'PunctuationRuleInline',
    'PunctuationExampleInline',
    'ChunkPunctuationFocusInline',
    'FocusRuleInline',
    'PunctuationQuestionInline',
    'PunctuationPracticeAttemptInline',
    'PunctuationTestAttemptInline',
]