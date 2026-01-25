from django.contrib import admin
from ..models.grammar import GrammarQuestion, GrammarTestAttempt

@admin.register(GrammarQuestion)
class GrammarQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "question_type", "correct_answer", "difficulty")
    search_fields = ("question_text", "correct_answer")
    list_filter = ("question_type", "difficulty")
   


@admin.register(GrammarTestAttempt)
class GrammarTestAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "score_percent", "correct_answers", "total_questions", "created_at")
    search_fields = ("student__username",)
    list_filter = ("score_percent", "created_at")
    ordering = ("-created_at",)