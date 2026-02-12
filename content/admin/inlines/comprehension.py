from django.contrib import admin
from content.models.comprehension import ComprehensionQuestion


class ComprehensionQuestionInline(admin.TabularInline):
    """
    Inline for authoring comprehension questions.
    Appears inside ChunkComprehensionFocus admin.
    """
    model = ComprehensionQuestion
    extra = 1
    fields = (
        "question_text",
        "question_type",
        "difficulty",
        "correct_answer",
        "options",
    )
    ordering = ("id",)