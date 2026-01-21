from django.contrib import admin
from ..models.grammar import GrammarAttempt


@admin.register(GrammarAttempt)
class GrammarAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "grammar_question", "selected_answer", "is_correct", "timestamp")
    search_fields = ("student__username", "grammar_question__question_text")
    list_filter = ("is_correct", "timestamp", "grammar_question__grammar_point")
    ordering = ("-timestamp",)