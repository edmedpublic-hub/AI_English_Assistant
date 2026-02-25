# content/admin/inlines/comprehension.py

"""
Admin inline classes for the Comprehension domain.
Provides nested editing interfaces for comprehension focuses with Bloom's taxonomy levels.
"""

from django.contrib import admin
from django.utils.html import format_html
from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionQuestion,
    ComprehensionPracticeAttempt,
    ComprehensionTestAttempt,
    ComprehensionQuestionAttempt,
    BloomLevel
)


# ============================================================
# CHUNK COMPREHENSION FOCUS (Main teaching layer)
# ============================================================

class ChunkComprehensionFocusInline(admin.StackedInline):
    """
    Appears inside LessonChunk.
    Primary comprehension authoring surface.
    Shows comprehension focuses with Bloom's taxonomy levels and questions.
    """
    model = ChunkComprehensionFocus
    extra = 0
    min_num = 0
    max_num = 3  # Maximum 3 focuses per chunk (one per Bloom's level)
    show_change_link = True
    
    fieldsets = (
        ('Comprehension Focus', {
            'fields': (
                'focus_title',
                'focus_description',
                'level',
                'depth_level',
                'sequence_order',
                'focus_preview',
            )
        }),
    )
    
    readonly_fields = ('focus_preview',)
    ordering = ('sequence_order',)
    
    def focus_preview(self, obj):
        """Show quick stats about this focus"""
        if not obj.pk:
            return "Not saved yet"
        
        # Count questions
        question_count = obj.questions.count()
        
        # Get level info
        level_display = obj.get_level_display()
        level_color = {
            'literal': '#28a745',      # Green
            'inferential': '#fd7e14',  # Orange
            'evaluative': '#dc3545',   # Red
        }.get(obj.level, '#6c757d')
        
        # Format the preview
        html = f"""
        <div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; border-left: 4px solid {level_color};">
            <strong>Bloom's Level:</strong> <span style="color: {level_color};">{level_display}</span><br>
            <strong>Depth Level:</strong> {obj.depth_level}/5<br>
            <strong>Questions:</strong> {question_count}
        </div>
        """
        
        if question_count > 0:
            html += f'<div style="margin-top: 5px;">✓ Has {question_count} question(s)</div>'
        else:
            html += '<div style="color: #856404; background-color: #fff3cd; padding: 4px; margin-top: 5px; border-radius: 4px;">⚠️ No questions yet</div>'
        
        # Show sequence validation
        expected_order = {
            'literal': 1,
            'inferential': 2,
            'evaluative': 3,
        }
        
        if obj.level and obj.sequence_order != expected_order.get(obj.level):
            html += f'<div style="color: #721c24; background-color: #f8d7da; padding: 4px; margin-top: 5px; border-radius: 4px;">⚠️ Sequence order should be {expected_order[obj.level]} for {level_display} level</div>'
        
        return format_html(html)
    focus_preview.short_description = "Focus Overview"


# ============================================================
# QUESTIONS under a CHUNK FOCUS (Tabular Layout)
# ============================================================

class ComprehensionQuestionInline(admin.TabularInline):
    """
    Inline for authoring comprehension questions (tabular layout).
    Appears inside ChunkComprehensionFocus admin.
    """
    model = ComprehensionQuestion
    extra = 1
    min_num = 0
    max_num = 15  # Reasonable limit per focus
    
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
        """Show a preview of how the question will appear to students"""
        if not obj.pk:
            return "Preview available after saving"
        
        html = f"""
        <div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 0.9em;">
            <p><strong>Question:</strong> {obj.question_text[:100]}</p>
        """
        
        if obj.question_type == 'mcq' and obj.options:
            options = obj.get_options_list()
            html += '<div style="margin-left: 15px;">'
            for i, opt in enumerate(options, 1):
                if opt == obj.correct_answer:
                    html += f'<p style="color: #28a745;">✓ {i}. {opt} <span style="color: #28a745;">(correct)</span></p>'
                else:
                    html += f'<p style="color: #666;">{i}. {opt}</p>'
            html += '</div>'
        elif obj.question_type == 'true_false':
            html += f'<p><strong>Correct Answer:</strong> <span style="color: #28a745;">{obj.correct_answer}</span></p>'
        else:
            html += f'<p><strong>Answer:</strong> {obj.correct_answer}</p>'
        
        if obj.explanation:
            html += f'<p style="margin-top: 5px; padding-top: 5px; border-top: 1px dashed #ccc;"><em>💡 {obj.explanation[:100]}</em></p>'
        
        html += "</div>"
        
        return format_html(html)
    question_preview.short_description = "Preview"


# ============================================================
# QUESTIONS under a CHUNK FOCUS (Stacked Layout)
# ============================================================

class ComprehensionQuestionStackedInline(admin.StackedInline):
    """
    Alternative stacked layout for more complex question editing.
    Provides more space for longer questions and explanations.
    """
    model = ComprehensionQuestion
    extra = 1
    min_num = 0
    max_num = 10
    
    fieldsets = (
        ('Question', {
            'fields': ('question_text', 'question_type', 'difficulty')
        }),
        ('Answer', {
            'fields': ('options', 'correct_answer', 'explanation'),
            'description': 'For MCQ: One option per line'
        }),
        ('Preview', {
            'fields': ('question_preview',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('question_preview',)
    ordering = ('difficulty', 'id')
    
    def question_preview(self, obj):
        """Show a preview of how the question will appear to students"""
        if not obj.pk:
            return "Preview available after saving"
        
        html = f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #007bff;">
            <p style="font-weight: bold; margin-bottom: 8px;">📝 {obj.question_text}</p>
        """
        
        if obj.question_type == 'mcq' and obj.options:
            options = obj.get_options_list()
            html += '<div style="margin-left: 20px;">'
            for i, opt in enumerate(options, 1):
                if opt == obj.correct_answer:
                    html += f'<p style="color: #28a745;">✓ {i}. {opt}</p>'
                else:
                    html += f'<p style="color: #666;">{i}. {opt}</p>'
            html += '</div>'
        else:
            html += f'<p><strong>Correct Answer:</strong> <span style="color: #28a745;">{obj.correct_answer}</span></p>'
        
        if obj.explanation:
            html += f'<p style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed #ccc;"><em>💡 {obj.explanation}</em></p>'
        
        html += '</div>'
        
        return format_html(html)
    question_preview.short_description = "Student View"


# ============================================================
# ANALYTICS INLINES (Read-only)
# ============================================================

class ComprehensionPracticeAttemptInline(admin.TabularInline):
    """
    Read-only inline for practice attempts within ChunkComprehensionFocus admin.
    """
    model = ComprehensionPracticeAttempt
    extra = 0
    readonly_fields = ['user', 'attempt_number', 'cycle_number', 'score_percent', 'is_passed', 'attempted_at']
    fields = ['user', 'attempt_number', 'cycle_number', 'score_percent', 'is_passed', 'attempted_at']
    ordering = ['-attempted_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class ComprehensionTestAttemptInline(admin.TabularInline):
    """
    Read-only inline for test attempts within ChunkComprehensionFocus admin.
    """
    model = ComprehensionTestAttempt
    extra = 0
    readonly_fields = ['user', 'attempt_number', 'cycle_number', 'score_percent', 'is_mastered', 'created_at']
    fields = ['user', 'attempt_number', 'cycle_number', 'score_percent', 'is_mastered', 'created_at']
    ordering = ['-created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class ComprehensionQuestionAttemptInline(admin.TabularInline):
    """
    Read-only inline for question attempts within ComprehensionQuestion admin.
    """
    model = ComprehensionQuestionAttempt
    extra = 0
    readonly_fields = ['user', 'cycle_number', 'attempt_number', 'selected_answer', 'open_ended_answer', 'is_correct', 'attempted_at']
    fields = ['user', 'cycle_number', 'attempt_number', 'is_correct', 'attempted_at']
    ordering = ['-attempted_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'ChunkComprehensionFocusInline',
    'ComprehensionQuestionInline',
    'ComprehensionQuestionStackedInline',
    'ComprehensionPracticeAttemptInline',
    'ComprehensionTestAttemptInline',
    'ComprehensionQuestionAttemptInline',
]