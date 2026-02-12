# content/admin/inlines/writing.py

from django.contrib import admin
from content.models.writing import WritingPrompt, WritingResponse, WritingAttempt


class WritingPromptInline(admin.TabularInline):
    """
    Inline editor for WritingPrompts under ChunkWritingFocus or UnitWritingTask.
    """
    model = WritingPrompt
    extra = 1
    fields = ("prompt_text", "expected_keywords", "rubric")
    show_change_link = True


class WritingResponseInline(admin.TabularInline):
    """
    Inline editor for student responses under WritingPrompt.
    """
    model = WritingResponse
    extra = 0
    fields = ("student", "response_text", "score", "feedback", "submitted_at")
    readonly_fields = ("submitted_at",)
    show_change_link = True


class WritingAttemptInline(admin.TabularInline):
    """
    Inline editor for attempts under WritingResponse.
    """
    model = WritingAttempt
    extra = 0
    fields = ("attempt_number", "time_spent", "hints_used")
    show_change_link = True