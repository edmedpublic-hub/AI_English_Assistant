# content/admin/inlines/punctuation.py

from django.contrib import admin
from content.models.punctuation import (
    PunctuationRule,
    PunctuationExample,
    PunctuationQuestion,
)


class PunctuationRuleInline(admin.TabularInline):
    """
    Inline for punctuation rules under a mark.
    """
    model = PunctuationRule
    extra = 1
    fields = ("rule_text",)
    ordering = ("id",)
    show_change_link = True  # allow quick jump to full rule edit


class PunctuationExampleInline(admin.TabularInline):
    """
    Inline for punctuation examples under a rule.
    """
    model = PunctuationExample
    extra = 1
    fields = ("sentence",)
    ordering = ("id",)
    show_change_link = True  # quick navigation to full example


class PunctuationQuestionInline(admin.TabularInline):
    """
    Appears inside ChunkPunctuationFocus admin.
    This is the main authoring interface for punctuation practice questions.
    """
    model = PunctuationQuestion
    extra = 1
    fields = (
        "question_text",
        "question_type",
        "options",
        "correct_answer",
        "difficulty",
        "explanation",
    )
    ordering = ("difficulty", "id")
    show_change_link = True
    autocomplete_fields = ()  # reserved for future if options grow large