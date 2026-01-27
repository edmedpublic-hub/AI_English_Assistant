from django.contrib import admin

from content.models.punctuation import (
    PunctuationMark,
    PunctuationRule,
    PunctuationExample,
    ChunkPunctuationFocus,
    PunctuationAttempt,
    PunctuationTestAttempt,
)

from content.admin.inlines.punctuation import PunctuationQuestionInline


# -----------------------------
# Curriculum (rare edits)
# -----------------------------

class PunctuationRuleInline(admin.TabularInline):
    model = PunctuationRule
    extra = 1


class PunctuationExampleInline(admin.TabularInline):
    model = PunctuationExample
    extra = 1


@admin.register(PunctuationMark)
class PunctuationMarkAdmin(admin.ModelAdmin):
    list_display = ("name", "symbol", "order_index")
    search_fields = ("name", "symbol")
    ordering = ("order_index",)

    inlines = [PunctuationRuleInline]


@admin.register(PunctuationRule)
class PunctuationRuleAdmin(admin.ModelAdmin):
    list_display = ("mark", "short_rule")

    def short_rule(self, obj):
        return obj.rule_text[:80]


@admin.register(PunctuationExample)
class PunctuationExampleAdmin(admin.ModelAdmin):
    list_display = ("rule", "short_sentence")

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

    inlines = [PunctuationQuestionInline]


# -----------------------------
# Analytics (read-only)
# -----------------------------

@admin.register(PunctuationAttempt)
class PunctuationAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "is_correct", "attempted_at")
    readonly_fields = [f.name for f in PunctuationAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PunctuationTestAttempt)
class PunctuationTestAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "focus", "score_percent", "created_at")
    readonly_fields = [f.name for f in PunctuationTestAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False