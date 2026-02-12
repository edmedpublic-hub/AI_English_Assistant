from django.contrib import admin
from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionQuestion,
    ComprehensionAttempt,
)
from content.admin.inlines.comprehension import ComprehensionQuestionInline

# -----------------------------
# Focus-level authoring
# -----------------------------
@admin.register(ChunkComprehensionFocus)
class ChunkComprehensionFocusAdmin(admin.ModelAdmin):
    list_display = ("focus_title", "chunk", "level", "sequence_order")
    search_fields = ("focus_title", "chunk__title")
    ordering = ("chunk", "sequence_order")
    inlines = [ComprehensionQuestionInline]

# -----------------------------
# Question authoring
# -----------------------------
@admin.register(ComprehensionQuestion)
class ComprehensionQuestionAdmin(admin.ModelAdmin):
    list_display = ("short_question", "focus", "question_type", "difficulty")
    search_fields = ("question_text", "focus__focus_title", "focus__chunk__title")
    ordering = ("focus", "id")

    def short_question(self, obj):
        return obj.question_text[:80]
    short_question.short_description = "Question preview"

# -----------------------------
# Analytics (read-only)
# -----------------------------
@admin.register(ComprehensionAttempt)
class ComprehensionAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "is_correct", "attempted_at")
    list_filter = ("is_correct", "attempted_at")
    search_fields = ("student__username", "question__question_text")
    ordering = ("-attempted_at",)
    readonly_fields = [f.name for f in ComprehensionAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False