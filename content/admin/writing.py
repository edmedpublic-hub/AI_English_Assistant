from django.contrib import admin
from content.models.writing import WritingTask, SentenceAttempt


# ----------------------------
# Writing tasks (authoring)
# ----------------------------
@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = (
        "lesson",
        "difficulty",
        "short_prompt",
    )

    list_filter = ("difficulty",)
    search_fields = ("prompt", "lesson__title")
    ordering = ("lesson",)

    def short_prompt(self, obj):
        return obj.prompt[:80]
    short_prompt.short_description = "Prompt"


# ----------------------------
# Sentence attempts (analytics)
# ----------------------------
@admin.register(SentenceAttempt)
class SentenceAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student_id",
        "writing_task",
        "ai_score",
        "timestamp",
    )

    list_filter = ("ai_score", "timestamp")
    search_fields = ("student_id", "writing_task__prompt")
    ordering = ("-timestamp",)

    readonly_fields = [f.name for f in SentenceAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False