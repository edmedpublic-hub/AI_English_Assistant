# content/admin/punctuation.py

from django.contrib import admin
from content.models.punctuation import (
    PunctuationMark,
    PunctuationRule,
    PunctuationExample,
    ChunkPunctuationFocus,
    PunctuationAttempt,
    PunctuationTestAttempt,
)
from content.admin.inlines.punctuation import (
    PunctuationRuleInline,
    PunctuationExampleInline,
    PunctuationQuestionInline,
)


# -----------------------------
# Curriculum (rare edits)
# -----------------------------
@admin.register(PunctuationMark)
class PunctuationMarkAdmin(admin.ModelAdmin):
    list_display = ("name", "symbol", "order_index")
    search_fields = ("name", "symbol")
    ordering = ("order_index",)
    inlines = [PunctuationRuleInline]

    # Prevent accidental deletion of global marks
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PunctuationRule)
class PunctuationRuleAdmin(admin.ModelAdmin):
    list_display = ("mark", "short_rule")
    search_fields = ("rule_text", "mark__name")
    ordering = ("mark",)

    def short_rule(self, obj):
        return obj.rule_text[:80]


@admin.register(PunctuationExample)
class PunctuationExampleAdmin(admin.ModelAdmin):
    list_display = ("rule", "short_sentence")
    search_fields = ("sentence", "rule__rule_text")
    ordering = ("rule",)

    def short_sentence(self, obj):
        return obj.sentence[:80]


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
    inlines = [PunctuationQuestionInline]

    # Prevent duplicate sequence orders per chunk (enforced at DB level too)
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("chunk", "mark")


# -----------------------------
# Analytics (read-only)
# -----------------------------
@admin.register(PunctuationAttempt)
class PunctuationAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "is_correct", "attempted_at")
    list_filter = ("is_correct", "attempted_at")
    search_fields = ("student__username", "question__question_text")
    ordering = ("-attempted_at",)
    readonly_fields = [f.name for f in PunctuationAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PunctuationTestAttempt)
class PunctuationTestAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "focus", "score_percent", "created_at")
    list_filter = ("score_percent", "created_at")
    search_fields = ("student__username", "focus__focus_title")
    ordering = ("-created_at",)
    readonly_fields = [f.name for f in PunctuationTestAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False