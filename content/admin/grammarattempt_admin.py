from django.contrib import admin
from ..models.grammar import GrammarAttempt


@admin.register(GrammarAttempt)
class GrammarAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "question",
        "selected_answer",
        "is_correct",
        "attempted_at",
    )

    list_filter = ("is_correct", "attempted_at")
    search_fields = ("student__username", "question__question_text")
    ordering = ("-attempted_at",)