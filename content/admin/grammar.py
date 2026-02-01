from django.contrib import admin

from content.models.grammar import (
    GrammarConcept,
    GrammarRule,
    GrammarExample,
    ChunkGrammarFocus,
    GrammarAttempt,
    GrammarTestAttempt,
)

from content.admin.inlines.grammar import GrammarQuestionInline


# -----------------------------
# Curriculum (rarely edited)
# -----------------------------
class GrammarExampleInline(admin.TabularInline):
    model = GrammarExample
    extra = 1


class GrammarRuleInline(admin.TabularInline):
    model = GrammarRule
    extra = 1
    inlines = [GrammarExampleInline]  # allows examples under rules


@admin.register(GrammarConcept)
class GrammarConceptAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "order_index")
    search_fields = ("name", "category")
    list_filter = ("category",)
    ordering = ("order_index",)
    inlines = [GrammarRuleInline]


@admin.register(GrammarRule)
class GrammarRuleAdmin(admin.ModelAdmin):
    list_display = ("concept", "short_rule")

    def short_rule(self, obj):
        return obj.rule_text[:80]


@admin.register(GrammarExample)
class GrammarExampleAdmin(admin.ModelAdmin):
    list_display = ("rule", "short_sentence")

    def short_sentence(self, obj):
        return obj.sentence[:80]


# -----------------------------
# Authoring (important area)
# -----------------------------
@admin.register(ChunkGrammarFocus)
class ChunkGrammarFocusAdmin(admin.ModelAdmin):
    list_display = ("focus_title", "chunk", "concept", "depth_level", "sequence_order")
    list_filter = ("concept", "depth_level")
    search_fields = ("focus_title", "chunk__lesson__title")
    ordering = ("chunk", "sequence_order")
    autocomplete_fields = ("concept", "chunk")
    inlines = [GrammarQuestionInline]


# -----------------------------
# Analytics (read-only)
# -----------------------------
@admin.register(GrammarAttempt)
class GrammarAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "is_correct", "attempted_at")
    list_filter = ("is_correct", "attempted_at")
    search_fields = ("student__username", "question__question_text")
    readonly_fields = [f.name for f in GrammarAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GrammarTestAttempt)
class GrammarTestAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "focus", "score_percent", "created_at")
    list_filter = ("score_percent", "created_at")
    search_fields = ("student__username", "focus__focus_title")
    readonly_fields = [f.name for f in GrammarTestAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False