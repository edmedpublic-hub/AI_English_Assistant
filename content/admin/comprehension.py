from django.contrib import admin
from content.models.comprehension import (
    ComprehensionQuestion,
    ComprehensionAttempt,
)


# -----------------------------
# Authoring
# -----------------------------

@admin.register(ComprehensionQuestion)
class ComprehensionQuestionAdmin(admin.ModelAdmin):
    list_display = ("short_question", "lesson")
    search_fields = ("question", "lesson__title")

    def short_question(self, obj):
        return obj.question[:80]


# -----------------------------
# Analytics (read-only)
# -----------------------------

@admin.register(ComprehensionAttempt)
class ComprehensionAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "question", "is_correct", "timestamp")
    list_filter = ("is_correct",)
    search_fields = ("student_id", "question__question")

    readonly_fields = [f.name for f in ComprehensionAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False