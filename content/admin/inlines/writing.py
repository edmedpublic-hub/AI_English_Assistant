# content/admin/inlines/writing.py

"""
Admin inline classes for the Writing domain.
Provides nested editing interfaces for writing focuses, prompts, and attempt tracking.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from content.models.writing import (
    ChunkWritingFocus,
    UnitWritingTask,
    WritingPrompt, 
    WritingPracticeAttempt, 
    WritingTestAttempt
)


# ============================================================
# CHUNK WRITING FOCUS INLINE (Main inline expected by core.py)
# ============================================================

class ChunkWritingFocusInline(admin.StackedInline):
    """
    Appears inside LessonChunk admin.
    Primary writing authoring surface for chunk-level writing focuses.
    This is the inline expected by content.admin.core.
    """
    model = ChunkWritingFocus
    extra = 0
    min_num = 0
    max_num = 3  # Maximum 3 focuses per chunk
    show_change_link = True
    
    fieldsets = (
        ('Writing Focus', {
            'fields': (
                'focus_title',
                'focus_description',
                'depth_level',
                'sequence_order',
                'focus_preview',
            )
        }),
    )
    
    readonly_fields = ('focus_preview',)
    ordering = ('sequence_order',)
    
    def focus_preview(self, obj):
        """Show quick stats about this writing focus"""
        if not obj.pk:
            return "Not saved yet"
        
        # Count prompts
        prompt_count = obj.prompts.count()
        
        # Format the preview
        html = f"""
        <div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; border-left: 4px solid #e83e8c;">
            <strong>Depth Level:</strong> {obj.depth_level}/5<br>
            <strong>Prompts:</strong> {prompt_count}
        </div>
        """
        
        if prompt_count > 0:
            html += f'<div style="margin-top: 5px;">✓ Has {prompt_count} prompt(s)</div>'
        else:
            html += '<div style="color: #856404; background-color: #fff3cd; padding: 4px; margin-top: 5px; border-radius: 4px;">⚠️ No prompts yet</div>'
        
        return format_html(html)
    focus_preview.short_description = "Focus Overview"


# ============================================================
# UNIT WRITING TASK INLINE (For unit-level tasks)
# ============================================================

class UnitWritingTaskInline(admin.StackedInline):
    """
    Inline for UnitWritingTask within Unit admin.
    Manages extended writing tasks at the unit level.
    """
    model = UnitWritingTask
    extra = 0
    min_num = 0
    max_num = 3  # Maximum tasks per unit
    show_change_link = True
    
    fieldsets = (
        ('Task Details', {
            'fields': (
                'task_title',
                'task_description',
                'stage',
                'difficulty_level',
                'order',
                'task_preview',
            )
        }),
    )
    
    readonly_fields = ('task_preview',)
    ordering = ('order',)
    
    def task_preview(self, obj):
        """Show preview of the writing task"""
        if not obj.pk:
            return "Not saved yet"
        
        # Count prompts
        prompt_count = obj.prompts.count()
        
        html = f"""
        <div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; border-left: 4px solid #fd7e14;">
            <strong>Stage:</strong> {obj.get_stage_display()}<br>
            <strong>Difficulty:</strong> {obj.difficulty_level}/5<br>
            <strong>Prompts:</strong> {prompt_count}
        </div>
        """
        
        if prompt_count == 0:
            html += '<div style="color: #856404; background-color: #fff3cd; padding: 4px; margin-top: 5px; border-radius: 4px;">⚠️ No prompts yet</div>'
        
        return format_html(html)
    task_preview.short_description = "Task Overview"


# ============================================================
# WRITING PROMPTS INLINE (Your existing inline)
# ============================================================

class WritingPromptInline(admin.TabularInline):
    """
    Inline editor for WritingPrompts under ChunkWritingFocus or UnitWritingTask.
    """
    model = WritingPrompt
    extra = 1
    min_num = 0
    max_num = 5  # Reasonable limit per focus/task
    
    fields = (
        "prompt_text", 
        "prompt_type",
        "expected_keywords", 
        "rubric",
        "prompt_preview"
    )
    readonly_fields = ("prompt_preview",)
    show_change_link = True
    ordering = ("id",)
    
    def prompt_preview(self, obj):
        """Show a preview of the prompt with rubric"""
        if not obj.pk:
            return "Preview available after saving"
        
        html = f"""
        <div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 0.9em;">
            <p><strong>Prompt:</strong> {obj.prompt_text[:100]}</p>
        """
        
        if obj.expected_keywords:
            html += f"<p><strong>Keywords:</strong> {obj.expected_keywords}</p>"
        
        if obj.rubric:
            html += "<p><strong>Rubric:</strong></p><ul style='margin:0;padding-left:20px;'>"
            for criterion, max_score in obj.rubric.items():
                html += f"<li><em>{criterion}</em>: {max_score} pts</li>"
            html += "</ul>"
        
        # Count attempts if any
        practice_count = WritingPracticeAttempt.objects.filter(prompt=obj).count()
        test_count = WritingTestAttempt.objects.filter(prompt=obj).count()
        
        if practice_count > 0 or test_count > 0:
            html += f"<p><span style='color: #666;'>{practice_count} practice, {test_count} test attempts</span></p>"
        
        html += "</div>"
        
        return format_html(html)
    prompt_preview.short_description = "Preview"


# ============================================================
# ANALYTICS INLINES (Your existing inlines)
# ============================================================

class WritingPracticeAttemptInline(admin.TabularInline):
    """
    Read-only inline for practice attempts under WritingPrompt or ChunkWritingFocus.
    """
    model = WritingPracticeAttempt
    extra = 0
    fields = (
        "user_link",
        "attempt_number",
        "cycle_number",
        "keyword_match_score",
        "is_passed",
        "created_at"
    )
    readonly_fields = (
        "user_link",
        "attempt_number",
        "cycle_number",
        "keyword_match_score",
        "is_passed",
        "created_at"
    )
    ordering = ("-created_at",)
    can_delete = False
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def has_add_permission(self, request, obj=None):
        return False


class WritingTestAttemptInline(admin.TabularInline):
    """
    Read-only inline for test attempts under WritingPrompt or ChunkWritingFocus.
    """
    model = WritingTestAttempt
    extra = 0
    fields = (
        "user_link",
        "attempt_number",
        "cycle_number",
        "overall_score",
        "is_mastered",
        "created_at"
    )
    readonly_fields = (
        "user_link",
        "attempt_number",
        "cycle_number",
        "overall_score",
        "is_mastered",
        "created_at"
    )
    ordering = ("-created_at",)
    can_delete = False
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def has_add_permission(self, request, obj=None):
        return False


class WritingTestAttemptDetailInline(admin.StackedInline):
    """
    Detailed view of test attempts with rubric scores.
    Best used in WritingPrompt admin.
    """
    model = WritingTestAttempt
    extra = 0
    fields = (
        "user_link",
        "attempt_number",
        "cycle_number",
        "response_text",
        "rubric_display",
        "overall_score",
        "is_mastered",
        "feedback",
        "created_at"
    )
    readonly_fields = (
        "user_link",
        "attempt_number",
        "cycle_number",
        "response_text",
        "rubric_display",
        "overall_score",
        "is_mastered",
        "feedback",
        "created_at"
    )
    ordering = ("-created_at",)
    can_delete = False
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def rubric_display(self, obj):
        """Display rubric scores in a readable format"""
        if not obj.rubric_scores:
            return "No rubric scores"
        
        html = "<table style='width:100%'>"
        html += "<tr><th>Criterion</th><th>Score</th></tr>"
        for criterion, score in obj.rubric_scores.items():
            html += f"<tr><td>{criterion}</td><td>{score}</td></tr>"
        html += "</table>"
        return format_html(html)
    rubric_display.short_description = "Rubric Scores"
    
    def has_add_permission(self, request, obj=None):
        return False


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'ChunkWritingFocusInline',        # Added this - fixes the import error
    'UnitWritingTaskInline',          # Added this for completeness
    'WritingPromptInline',
    'WritingPracticeAttemptInline',
    'WritingTestAttemptInline',
    'WritingTestAttemptDetailInline',
]