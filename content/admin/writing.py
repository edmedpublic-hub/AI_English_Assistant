# content/admin/writing.py

from django.contrib import admin
from content.models.writing import (
    ChunkWritingFocus,
    UnitWritingTask,
    WritingPrompt,
    WritingResponse,
    WritingAttempt,
    WritingTestAttempt,
)
from .inlines.writing import (
    WritingPromptInline,
    WritingResponseInline,
    WritingAttemptInline,
)


@admin.register(ChunkWritingFocus)
class ChunkWritingFocusAdmin(admin.ModelAdmin):
    list_display = ("chunk", "focus_title", "depth_level", "sequence_order")
    search_fields = ("focus_title", "focus_description")
    list_filter = ("depth_level",)
    inlines = [WritingPromptInline]


@admin.register(UnitWritingTask)
class UnitWritingTaskAdmin(admin.ModelAdmin):
    list_display = ("unit", "task_title", "stage", "difficulty_level", "order")
    search_fields = ("task_title", "task_description")
    list_filter = ("stage", "difficulty_level")
    inlines = [WritingPromptInline]


@admin.register(WritingPrompt)
class WritingPromptAdmin(admin.ModelAdmin):
    list_display = ("id", "prompt_text", "focus", "task")
    search_fields = ("prompt_text", "expected_keywords")
    list_filter = ("focus", "task")
    inlines = [WritingResponseInline]


@admin.register(WritingResponse)
class WritingResponseAdmin(admin.ModelAdmin):
    list_display = ("student", "prompt", "score", "submitted_at")
    search_fields = ("response_text", "feedback")
    list_filter = ("score", "submitted_at")
    inlines = [WritingAttemptInline]


@admin.register(WritingAttempt)
class WritingAttemptAdmin(admin.ModelAdmin):
    list_display = ("response", "attempt_number", "time_spent", "hints_used")
    list_filter = ("attempt_number",)


@admin.register(WritingTestAttempt)
class WritingTestAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "prompt", "overall_score", "created_at")
    list_filter = ("overall_score", "created_at")
    search_fields = ("student__username",)