# content/admin/writing.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from content.models.writing import (
    ChunkWritingFocus,
    UnitWritingTask,
    WritingPrompt,
    WritingPracticeAttempt,
    WritingTestAttempt,
)
from .inlines.writing import (
    WritingPromptInline,
    WritingPracticeAttemptInline,
    WritingTestAttemptInline,
)


# ============================================================
# CHUNK-LEVEL WRITING FOCUS
# ============================================================

@admin.register(ChunkWritingFocus)
class ChunkWritingFocusAdmin(admin.ModelAdmin):
    list_display = (
        "chunk_link", 
        "focus_title", 
        "depth_level", 
        "sequence_order",
        "prompt_count",
        "mastery_rate"
    )
    search_fields = ("focus_title", "focus_description", "chunk__english_text")
    list_filter = ("depth_level", "sequence_order")
    autocomplete_fields = ("chunk",)
    readonly_fields = ("created_at", "updated_at", "prompt_count_display", "mastery_stats_display")
    
    fieldsets = (
        ("Writing Focus", {
            "fields": ("chunk", "focus_title", "focus_description")
        }),
        ("Pedagogy", {
            "fields": ("depth_level", "sequence_order"),
        }),
        ("Prompts", {
            "fields": ("prompt_count_display",),
        }),
        ("Mastery Statistics", {
            "fields": ("mastery_stats_display",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    
    inlines = [WritingPromptInline]

    def chunk_link(self, obj):
        url = reverse('admin:content_lessonchunk_change', args=[obj.chunk.id])
        return format_html('<a href="{}">{}</a>', url, obj.chunk)
    chunk_link.short_description = "Chunk"
    
    def prompt_count(self, obj):
        return obj.prompts.count()
    prompt_count.short_description = "Prompts"
    
    def prompt_count_display(self, obj):
        count = obj.prompts.count()
        if count > 0:
            url = reverse('admin:content_writingprompt_changelist') + f'?focus__id__exact={obj.id}'
            return format_html('<a href="{}">{} prompt{}</a>', url, count, 's' if count != 1 else '')
        return format_html('<span style="color: orange;">No prompts yet</span>')
    prompt_count_display.short_description = "Prompts"
    
    def mastery_rate(self, obj):
        """Show what percentage of students have mastered this focus"""
        total_attempts = WritingTestAttempt.objects.filter(focus=obj).values('user').distinct().count()
        if total_attempts == 0:
            return format_html('<span style="color:gray;">No data</span>')
        
        mastered = WritingTestAttempt.objects.filter(
            focus=obj, 
            is_mastered=True
        ).values('user').distinct().count()
        
        percentage = (mastered / total_attempts) * 100
        color = 'green' if percentage >= 80 else 'orange' if percentage >= 50 else 'red'
        
        return format_html(
            '<span style="color:{};">{}% ({} of {})</span>',
            color, int(percentage), mastered, total_attempts
        )
    mastery_rate.short_description = "Mastery Rate"
    
    def mastery_stats_display(self, obj):
        """Detailed mastery statistics"""
        attempts = WritingTestAttempt.objects.filter(focus=obj)
        
        if not attempts.exists():
            return "No attempts yet"
        
        total_students = attempts.values('user').distinct().count()
        mastered_students = attempts.filter(is_mastered=True).values('user').distinct().count()
        
        avg_score = attempts.aggregate(models.Avg('overall_score'))['overall_score__avg']
        
        # Attempt distribution
        attempt_counts = {}
        for i in range(1, 4):
            attempt_counts[f'attempt_{i}'] = attempts.filter(attempt_number=i).count()
        
        html = f"""
        <table style="width:100%">
            <tr><td>Total Students:</td><td><b>{total_students}</b></td></tr>
            <tr><td>Mastered (100%):</td><td><b style="color:green;">{mastered_students}</b></td></tr>
            <tr><td>Average Score:</td><td><b>{avg_score:.1f}%</b></td></tr>
            <tr><td colspan="2"><hr></td></tr>
            <tr><td>Attempt 1:</td><td>{attempt_counts.get('attempt_1', 0)}</td></tr>
            <tr><td>Attempt 2:</td><td>{attempt_counts.get('attempt_2', 0)}</td></tr>
            <tr><td>Attempt 3:</td><td>{attempt_counts.get('attempt_3', 0)}</td></tr>
        </table>
        """
        return format_html(html)
    mastery_stats_display.short_description = "Mastery Statistics"


# ============================================================
# UNIT-LEVEL WRITING TASKS
# ============================================================

@admin.register(UnitWritingTask)
class UnitWritingTaskAdmin(admin.ModelAdmin):
    list_display = (
        "unit_link", 
        "task_title", 
        "stage", 
        "difficulty_level", 
        "order",
        "prompt_count"
    )
    search_fields = ("task_title", "task_description")
    list_filter = ("stage", "difficulty_level", "unit__textbook")
    autocomplete_fields = ("unit",)
    readonly_fields = ("created_at", "updated_at", "prompt_count_display")
    
    fieldsets = (
        ("Task Details", {
            "fields": ("unit", "task_title", "task_description", "stage")
        }),
        ("Difficulty", {
            "fields": ("difficulty_level", "order"),
        }),
        ("Prompts", {
            "fields": ("prompt_count_display",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    
    inlines = [WritingPromptInline]

    def unit_link(self, obj):
        url = reverse('admin:content_unit_change', args=[obj.unit.id])
        return format_html('<a href="{}">{}</a>', url, obj.unit)
    unit_link.short_description = "Unit"
    
    def prompt_count(self, obj):
        return obj.prompts.count()
    prompt_count.short_description = "Prompts"
    
    def prompt_count_display(self, obj):
        count = obj.prompts.count()
        if count > 0:
            url = reverse('admin:content_writingprompt_changelist') + f'?task__id__exact={obj.id}'
            return format_html('<a href="{}">{} prompt{}</a>', url, count, 's' if count != 1 else '')
        return format_html('<span style="color: orange;">No prompts yet</span>')
    prompt_count_display.short_description = "Prompts"


# ============================================================
# WRITING PROMPTS
# ============================================================

@admin.register(WritingPrompt)
class WritingPromptAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "prompt_preview", 
        "prompt_type",
        "focus_link", 
        "task_link",
        "rubric_preview"
    )
    search_fields = ("prompt_text", "expected_keywords")
    list_filter = ("prompt_type", "focus", "task")
    autocomplete_fields = ("focus", "task")
    readonly_fields = ("created_at", "updated_at", "rubric_display")
    
    fieldsets = (
        ("Prompt Details", {
            "fields": ("focus", "task", "prompt_type", "prompt_text")
        }),
        ("Assessment", {
            "fields": ("expected_keywords", "rubric", "rubric_display"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def prompt_preview(self, obj):
        return obj.prompt_text[:60] + "..." if len(obj.prompt_text) > 60 else obj.prompt_text
    prompt_preview.short_description = "Prompt"
    
    def focus_link(self, obj):
        if obj.focus:
            url = reverse('admin:content_chunkwritingfocus_change', args=[obj.focus.id])
            return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
        return "-"
    focus_link.short_description = "Focus"
    
    def task_link(self, obj):
        if obj.task:
            url = reverse('admin:content_unitwritingtask_change', args=[obj.task.id])
            return format_html('<a href="{}">{}</a>', url, obj.task.task_title)
        return "-"
    task_link.short_description = "Task"
    
    def rubric_preview(self, obj):
        if not obj.rubric:
            return "No rubric"
        
        html = "<ul style='margin:0;padding-left:15px;'>"
        for criterion, max_score in obj.rubric.items():
            html += f"<li><strong>{criterion}:</strong> {max_score} pts</li>"
        html += "</ul>"
        return format_html(html)
    rubric_preview.short_description = "Rubric"
    
    def rubric_display(self, obj):
        """Detailed rubric display"""
        if not obj.rubric:
            return "No rubric defined"
        
        html = "<table style='width:100%'>"
        html += "<tr><th>Criterion</th><th>Max Score</th></tr>"
        for criterion, max_score in obj.rubric.items():
            html += f"<tr><td>{criterion}</td><td>{max_score}</td></tr>"
        html += "</table>"
        return format_html(html)
    rubric_display.short_description = "Rubric Details"


# ============================================================
# PRACTICE ATTEMPTS (Read-only Analytics)
# ============================================================

@admin.register(WritingPracticeAttempt)
class WritingPracticeAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user_link",
        "prompt_link",
        "attempt_number",
        "cycle_number",
        "keyword_match_score",
        "is_passed",
        "created_at"
    )
    list_filter = ("is_passed", "attempt_number", "cycle_number", "created_at")
    search_fields = ("user__username", "prompt__prompt_text")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in WritingPracticeAttempt._meta.fields]
    
    fieldsets = (
        ("Student", {
            "fields": ("user", "prompt")
        }),
        ("Attempt Details", {
            "fields": ("attempt_number", "cycle_number", "created_at")
        }),
        ("Response", {
            "fields": ("response_text",)
        }),
        ("Results", {
            "fields": ("keyword_match_score", "is_passed", "time_spent_seconds")
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def prompt_link(self, obj):
        url = reverse('admin:content_writingprompt_change', args=[obj.prompt.id])
        return format_html('<a href="{}">{}</a>', url, obj.prompt.id)
    prompt_link.short_description = "Prompt"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# TEST ATTEMPTS (Read-only Analytics)
# ============================================================

@admin.register(WritingTestAttempt)
class WritingTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user_link",
        "focus_link",
        "task_link",
        "attempt_number",
        "cycle_number",
        "overall_score",
        "is_mastered",
        "created_at"
    )
    list_filter = ("is_mastered", "attempt_number", "cycle_number", "created_at")
    search_fields = ("user__username", "focus__focus_title", "task__task_title")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in WritingTestAttempt._meta.fields]
    
    fieldsets = (
        ("Student", {
            "fields": ("user", "focus", "task", "prompt")
        }),
        ("Attempt Details", {
            "fields": ("attempt_number", "cycle_number", "created_at")
        }),
        ("Response", {
            "fields": ("response_text",)
        }),
        ("Results", {
            "fields": ("rubric_scores", "overall_score", "is_mastered", "feedback")
        }),
        ("Timestamps", {
            "fields": ("time_spent_seconds",),
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def focus_link(self, obj):
        if obj.focus:
            url = reverse('admin:content_chunkwritingfocus_change', args=[obj.focus.id])
            return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
        return "-"
    focus_link.short_description = "Focus"
    
    def task_link(self, obj):
        if obj.task:
            url = reverse('admin:content_unitwritingtask_change', args=[obj.task.id])
            return format_html('<a href="{}">{}</a>', url, obj.task.task_title)
        return "-"
    task_link.short_description = "Task"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# LEGACY MODELS (Removed - consolidated into new attempt models)
# ============================================================
# WritingResponse and WritingAttempt have been consolidated into
# WritingPracticeAttempt and WritingTestAttempt
# Their admins are no longer needed