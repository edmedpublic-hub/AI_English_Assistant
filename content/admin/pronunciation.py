from django.contrib import admin
from content.models.pronunciation import PronunciationAttempt


@admin.register(PronunciationAttempt)
class PronunciationAttemptAdmin(admin.ModelAdmin):
    """
    Read-only diagnostic view for pronunciation attempts.
    """
    list_display = (
        "student_id",
        "chunk",
        "ai_score",
        "timestamp",
    )

    list_filter = ("ai_score", "timestamp")
    search_fields = ("student_id", "chunk__lesson__title")
    ordering = ("-timestamp",)

    readonly_fields = [f.name for f in PronunciationAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False