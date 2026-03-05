# content/admin/inlines/punctuation.py

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


class ChunkPunctuationFocusInline(admin.StackedInline):
    model = ChunkPunctuationFocus
    extra = 0
    min_num = 0
    max_num = 3
    show_change_link = True

    fieldsets = (
        ('Punctuation Focus', {
            'fields': (
                'mark', 'focus_title', 'focus_description',
                'depth_level', 'sequence_order', 'focus_preview',
            )
        }),
    )

    readonly_fields = ('focus_preview',)
    ordering = ('sequence_order',)
    autocomplete_fields = ('mark',)

    def focus_preview(self, obj):
        if not obj.pk:
            return "Not saved yet"
        question_count = obj.questions.count()
        rule_count = obj.focus_rules.count()
        mark_name = obj.mark.name if obj.mark else "No mark selected"
        mark_symbol = obj.mark.symbol if obj.mark else ""
        html = f"""
        <div style="background:#f8f9fa;padding:8px;border-radius:4px;">
            <strong>Mark:</strong> {mark_name} ({mark_symbol})<br>
            <strong>Questions:</strong> {question_count}<br>
            <strong>Rules:</strong> {rule_count}
        </div>
        """
        if question_count == 0:
            html += '<div style="color:#856404;background:#fff3cd;padding:4px;margin-top:5px;border-radius:4px;">⚠️ No questions yet</div>'
        if rule_count == 0:
            html += '<div style="color:#856404;background:#fff3cd;padding:4px;margin-top:5px;border-radius:4px;">⚠️ No rules linked</div>'
        return format_html(html)
    focus_preview.short_description = "Focus Overview"


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
        return format_html('<a href="{}" target="_blank">{}</a>', url, obj.rule.rule_text[:60])
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
            'description': 'For MCQ: Use pipe | separator. Example: Option A | Option B | Option C'
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
        html = f"""
        <div style="background:#f8f9fa;padding:12px;border-radius:6px;border-left:4px solid #007bff;">
            <p style="font-weight:bold;margin-bottom:8px;">📝 {obj.question_text}</p>
        """
        if obj.question_type == 'mcq' and obj.options:
            # FIXED: use options_list property not get_options_list()
            options = obj.options_list
            html += '<div style="margin-left:20px;">'
            for i, opt in enumerate(options, 1):
                if opt == obj.correct_answer:
                    html += f'<p style="color:#28a745;">✓ {i}. {opt} <span>(correct)</span></p>'
                else:
                    html += f'<p style="color:#666;">{i}. {opt}</p>'
            html += '</div>'
        else:
            html += f'<p><strong>Correct Answer:</strong> <span style="color:#28a745;">{obj.correct_answer}</span></p>'
        if obj.explanation:
            html += f'<p style="margin-top:8px;border-top:1px dashed #ccc;"><em>💡 {obj.explanation}</em></p>'
        html += '</div>'
        return format_html(html)
    question_preview.short_description = "Student View"


class PunctuationPracticeAttemptInline(admin.TabularInline):
    model = PunctuationPracticeAttempt
    extra = 0
    # FIXED: only fields that exist on the model
    readonly_fields = ['user', 'attempt_number', 'cycle_number', 'score_percent', 'is_passed', 'created_at']
    fields = ['user', 'attempt_number', 'cycle_number', 'score_percent', 'is_passed', 'created_at']
    ordering = ['-created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class PunctuationTestAttemptInline(admin.TabularInline):
    model = PunctuationTestAttempt
    extra = 0
    readonly_fields = ['user', 'attempt_number', 'cycle_number', 'score_percent', 'is_mastered', 'created_at']
    fields = ['user', 'attempt_number', 'cycle_number', 'score_percent', 'is_mastered', 'created_at']
    ordering = ['-created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


__all__ = [
    'PunctuationRuleInline',
    'PunctuationExampleInline',
    'ChunkPunctuationFocusInline',
    'FocusRuleInline',
    'PunctuationQuestionInline',
    'PunctuationPracticeAttemptInline',
    'PunctuationTestAttemptInline',
]