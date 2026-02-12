# content/admin/punctuation.py

from django.contrib import admin
from content.models.punctuation import (
    PunctuationMark,
    PunctuationRule,
    PunctuationExample,
    ChunkPunctuationFocus,
    ChunkPunctuationFocusRule, # Added new through model
    PunctuationQuestion,
    # PunctuationAttempt removed to match updated models
    PunctuationTestAttempt,
)
from content.admin.inlines.punctuation import (
    PunctuationRuleInline,
    PunctuationExampleInline,
    PunctuationQuestionInline,
    FocusRuleInline, # We will need to define this in the next step
)

# -----------------------------
# Curriculum (rare edits)
# -----------------------------
@admin.register(PunctuationMark)
class PunctuationMarkAdmin(admin.ModelAdmin):
    list_display = ("name", "symbol", "order_index", "last_updated")
    search_fields = ("name", "symbol")
    ordering = ("order_index",)
    inlines = [PunctuationRuleInline]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PunctuationRule)
class PunctuationRuleAdmin(admin.ModelAdmin):
    list_display = ("mark", "short_rule")
    search_fields = ("rule_text", "mark__name")
    ordering = ("mark",)
    inlines = [PunctuationExampleInline] # Added inline for examples

    def short_rule(self, obj):
        return obj.rule_text[:80]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("mark")


@admin.register(PunctuationExample)
class PunctuationExampleAdmin(admin.ModelAdmin):
    list_display = ("rule", "short_sentence")
    search_fields = ("sentence", "rule__rule_text")
    ordering = ("rule",)

    def short_sentence(self, obj):
        return obj.sentence[:80]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("rule", "rule__mark")


# -----------------------------
# Authoring (core work area)
# -----------------------------
@admin.register(ChunkPunctuationFocus)
class ChunkPunctuationFocusAdmin(admin.ModelAdmin):
    list_display = ("focus_title", "chunk", "mark", "depth_level", "sequence_order")
    list_filter = ("mark", "depth_level")
    search_fields = ("focus_title", "chunk__lesson__title")
    ordering = ("chunk", "sequence_order")
    autocomplete_fields = ("chunk", "mark")
    # Added FocusRuleInline so teachers can pick global rules for this focus
    inlines = [FocusRuleInline, PunctuationQuestionInline] 

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("chunk", "mark")


# Global inspection of questions (important for debugging & analytics)
@admin.register(PunctuationQuestion)
class PunctuationQuestionAdmin(admin.ModelAdmin):
    list_display = ("short_question", "focus", "question_type")
    list_filter = ("question_type", "focus__mark")
    search_fields = ("question_text", "focus__focus_title")
    ordering = ("focus", "id")
    autocomplete_fields = ("focus",)

    def short_question(self, obj):
        return obj.question_text[:80]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("focus", "focus__mark")


# -----------------------------
# Analytics (read-only)
# -----------------------------

# PunctuationAttemptAdmin removed as the model no longer exists

@admin.register(PunctuationTestAttempt)
class PunctuationTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "focus",
        "score_percent",
        "is_mastered",
        "correct_answers",
        "total_questions",
        "created_at",
    )

    list_filter = ("is_mastered", "focus")
    search_fields = ("student__username", "focus__focus_title")
    readonly_fields = (
        "student",
        "focus",
        "score_percent",
        "is_mastered",
        "correct_answers",
        "total_questions",
        "created_at",
    )

    ordering = ("-created_at",)
