from django.contrib import admin
from ..models.grammar import GrammarPoint, GrammarQuestion, GrammarTestAttempt


@admin.register(GrammarPoint)
class GrammarPointAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "chunk")
    search_fields = ("title", "explanation", "examples")
    list_filter = ("lesson", "chunk")


@admin.register(GrammarQuestion)
class GrammarQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "grammar_point", "question_type", "correct_answer", "difficulty")
    search_fields = ("question_text", "correct_answer")
    list_filter = ("question_type", "difficulty", "grammar_point")
    ordering = ("grammar_point", "id")


@admin.register(GrammarTestAttempt)
class GrammarTestAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "grammar_point", "score_percent", "correct_answers", "total_questions", "created_at")
    search_fields = ("student__username", "grammar_point__title")
    list_filter = ("score_percent", "created_at", "grammar_point")
    ordering = ("-created_at",)