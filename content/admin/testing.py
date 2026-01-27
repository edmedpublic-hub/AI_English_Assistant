from django.contrib import admin
from content.models.testing import (
    VocabularyTestSession,
    VocabularyTestQuestion,
    VocabularyTestAnswer,
    VocabularyTestAttempt,
)


# ----------------------------
# Test Sessions (overview)
# ----------------------------
@admin.register(VocabularyTestSession)
class VocabularyTestSessionAdmin(admin.ModelAdmin):
    list_display = (
        "student_id",
        "chunk",
        "score_percentage",
        "passed",
        "started_at",
        "completed_at",
    )

    list_filter = ("passed", "started_at")
    search_fields = ("student_id", "chunk__lesson__title")
    ordering = ("-started_at",)

    readonly_fields = [f.name for f in VocabularyTestSession._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ----------------------------
# Individual Questions in Session
# ----------------------------
@admin.register(VocabularyTestQuestion)
class VocabularyTestQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "order",
        "question_type",
        "vocab_item",
    )

    list_filter = ("question_type",)
    search_fields = ("session__student_id", "vocab_item__word")
    ordering = ("session", "order")

    readonly_fields = [f.name for f in VocabularyTestQuestion._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ----------------------------
# Individual Answers
# ----------------------------
@admin.register(VocabularyTestAnswer)
class VocabularyTestAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "selected_option",
        "is_correct",
        "answered_at",
    )

    list_filter = ("is_correct",)
    ordering = ("-answered_at",)

    readonly_fields = [f.name for f in VocabularyTestAnswer._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ----------------------------
# Aggregate Attempts (summary)
# ----------------------------
@admin.register(VocabularyTestAttempt)
class VocabularyTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "lesson",
        "chunk",
        "score_percent",
        "created_at",
    )

    list_filter = ("score_percent", "created_at")
    search_fields = ("user__username", "lesson__title")
    ordering = ("-created_at",)

    readonly_fields = [f.name for f in VocabularyTestAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False