# content/admin/punctuation.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from content.models.punctuation import (
    PunctuationMark,
    PunctuationRule,
    PunctuationExample,
    ChunkPunctuationFocus,
    ChunkPunctuationFocusRule,
    PunctuationQuestion,
    PunctuationPracticeAttempt,
    PunctuationTestAttempt,
)
from content.admin.inlines.punctuation import (
    PunctuationRuleInline,
    PunctuationExampleInline,
    PunctuationQuestionInline,
    FocusRuleInline,
    PunctuationPracticeAttemptInline,
    PunctuationTestAttemptInline,
)


@admin.register(PunctuationMark)
class PunctuationMarkAdmin(admin.ModelAdmin):
    list_display = ("name", "symbol", "order_index", "rule_count", "last_updated")
    list_filter = ("name",)
    search_fields = ("name", "symbol", "description")
    ordering = ("order_index",)
    readonly_fields = ("created_at", "updated_at", "rule_count_display")

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "symbol", "description", "order_index")
        }),
        ("Statistics", {
            "fields": ("rule_count_display",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    inlines = [PunctuationRuleInline]

    def rule_count(self, obj):
        return obj.rules.count()
    rule_count.short_description = "Rules"

    def rule_count_display(self, obj):
        count = obj.rules.count()
        if count > 0:
            url = reverse('admin:content_punctuationrule_changelist') + f'?mark__id__exact={obj.id}'
            return format_html('<a href="{}">{} rule{}</a>', url, count, 's' if count != 1 else '')
        return "No rules"
    rule_count_display.short_description = "Rules"

    def last_updated(self, obj):
        return obj.updated_at.strftime("%Y-%m-%d")
    last_updated.short_description = "Updated"

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PunctuationRule)
class PunctuationRuleAdmin(admin.ModelAdmin):
    list_display = ("mark", "rule_preview", "example_count", "usage_count")
    list_filter = ("mark",)
    search_fields = ("rule_text", "mark__name")
    ordering = ("mark", "id")
    autocomplete_fields = ("mark",)
    readonly_fields = ("created_at", "updated_at", "example_count_display")

    fieldsets = (
        ("Rule Details", {
            "fields": ("mark", "rule_text")
        }),
        ("Statistics", {
            "fields": ("example_count_display",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    inlines = [PunctuationExampleInline]

    def rule_preview(self, obj):
        return obj.rule_text[:60] + "..." if len(obj.rule_text) > 60 else obj.rule_text
    rule_preview.short_description = "Rule"

    def example_count(self, obj):
        return obj.examples.count()
    example_count.short_description = "Examples"

    def example_count_display(self, obj):
        count = obj.examples.count()
        return format_html('<b>{}</b> example{}', count, 's' if count != 1 else '')
    example_count_display.short_description = "Examples"

    def usage_count(self, obj):
        return obj.chunkpunctuationfocusrule_set.count()
    usage_count.short_description = "Used in"

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("mark")


@admin.register(PunctuationExample)
class PunctuationExampleAdmin(admin.ModelAdmin):
    list_display = ("rule", "sentence_preview")
    list_filter = ("rule__mark",)
    search_fields = ("sentence", "rule__rule_text")
    ordering = ("rule", "id")
    autocomplete_fields = ("rule",)
    readonly_fields = ("created_at", "updated_at")

    def sentence_preview(self, obj):
        return obj.sentence[:80] + "..." if len(obj.sentence) > 80 else obj.sentence
    sentence_preview.short_description = "Sentence"

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("rule", "rule__mark")


@admin.register(ChunkPunctuationFocusRule)
class ChunkPunctuationFocusRuleAdmin(admin.ModelAdmin):
    list_display = ('focus_link', 'rule_link', 'order', 'created_at')
    list_filter = ('focus__mark', 'created_at')
    search_fields = ('focus__focus_title', 'rule__rule_text')
    autocomplete_fields = ('focus', 'rule')
    ordering = ('focus', 'order')
    readonly_fields = ('created_at', 'updated_at', 'mapping_preview')

    fieldsets = (
        ('Mapping', {
            'fields': ('focus', 'rule', 'order')
        }),
        ('Preview', {
            'fields': ('mapping_preview',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def focus_link(self, obj):
        url = reverse('admin:content_chunkpunctuationfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def rule_link(self, obj):
        url = reverse('admin:content_punctuationrule_change', args=[obj.rule.id])
        return format_html('<a href="{}">{}</a>', url, obj.rule.rule_text[:50])
    rule_link.short_description = "Rule"

    def mapping_preview(self, obj):
        if not obj.pk:
            return "Not saved yet"
        html = f"""
        <div style="background:#f8f9fa;padding:15px;border-radius:5px;border-left:4px solid #17a2b8;">
            <p><strong>Focus:</strong> {obj.focus.focus_title}</p>
            <p><strong>Mark:</strong> {obj.focus.mark.symbol} - {obj.focus.mark.name}</p>
            <p><strong>Rule:</strong> {obj.rule.rule_text[:100]}</p>
            <p><strong>Order:</strong> {obj.order}</p>
        </div>
        """
        return format_html(html)
    mapping_preview.short_description = "Preview"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('focus', 'focus__mark', 'rule')


@admin.register(ChunkPunctuationFocus)
class ChunkPunctuationFocusAdmin(admin.ModelAdmin):
    list_display = (
        "focus_title", "chunk_link", "mark",
        "depth_level", "sequence_order", "question_count", "mastery_rate"
    )
    list_filter = ("mark", "depth_level", "sequence_order")
    search_fields = ("focus_title", "focus_description", "chunk__english_text")
    ordering = ("chunk", "sequence_order")
    autocomplete_fields = ("chunk", "mark")
    readonly_fields = ("created_at", "updated_at", "question_count_display", "mastery_stats_display")

    fieldsets = (
        ("Punctuation Focus", {
            "fields": ("chunk", "mark", "focus_title", "focus_description")
        }),
        ("Pedagogy", {
            "fields": ("depth_level", "sequence_order"),
        }),
        ("Questions & Rules", {
            "fields": ("question_count_display",),
        }),
        ("Mastery Statistics", {
            "fields": ("mastery_stats_display",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    inlines = [FocusRuleInline, PunctuationQuestionInline]

    def chunk_link(self, obj):
        url = reverse('admin:content_lessonchunk_change', args=[obj.chunk.id])
        return format_html('<a href="{}">{}</a>', url, obj.chunk)
    chunk_link.short_description = "Chunk"

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = "Questions"

    def question_count_display(self, obj):
        count = obj.questions.count()
        if count > 0:
            url = reverse('admin:content_punctuationquestion_changelist') + f'?focus__id__exact={obj.id}'
            return format_html('<a href="{}">{} question{}</a>', url, count, 's' if count != 1 else '')
        return format_html('<span style="color:orange;">No questions yet</span>')
    question_count_display.short_description = "Questions"

    def mastery_rate(self, obj):
        total = PunctuationTestAttempt.objects.filter(focus=obj).values('user').distinct().count()
        if total == 0:
            return format_html('<span style="color:gray;">No data</span>')
        mastered = PunctuationTestAttempt.objects.filter(
            focus=obj, is_mastered=True).values('user').distinct().count()
        pct = (mastered / total) * 100
        color = 'green' if pct >= 80 else 'orange' if pct >= 50 else 'red'
        return format_html('<span style="color:{};">{}% ({} of {})</span>', color, int(pct), mastered, total)
    mastery_rate.short_description = "Mastery Rate"

    def mastery_stats_display(self, obj):
        attempts = PunctuationTestAttempt.objects.filter(focus=obj)
        if not attempts.exists():
            return "No attempts yet"
        total_students = attempts.values('user').distinct().count()
        mastered_students = attempts.filter(is_mastered=True).values('user').distinct().count()
        avg_score = attempts.aggregate(models.Avg('score_percent'))['score_percent__avg'] or 0
        html = f"""
        <table style="width:100%">
            <tr><td>Total Students:</td><td><b>{total_students}</b></td></tr>
            <tr><td>Mastered:</td><td><b style="color:green;">{mastered_students}</b></td></tr>
            <tr><td>Average Score:</td><td><b>{avg_score:.1f}%</b></td></tr>
        </table>
        """
        return format_html(html)
    mastery_stats_display.short_description = "Mastery Statistics"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("chunk", "mark")


@admin.register(PunctuationQuestion)
class PunctuationQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "question_preview", "focus_link", "question_type", "difficulty", "has_options"
    )
    list_filter = ("question_type", "difficulty", "focus__mark")
    search_fields = ("question_text", "focus__focus_title", "correct_answer")
    ordering = ("focus", "id")
    autocomplete_fields = ("focus",)
    readonly_fields = ("created_at", "updated_at", "options_preview")

    fieldsets = (
        ("Question Details", {
            "fields": ("focus", "question_type", "difficulty", "question_text")
        }),
        ("Answer", {
            "fields": ("options", "options_preview", "correct_answer", "explanation"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def question_preview(self, obj):
        return obj.question_text[:60] + "..." if len(obj.question_text) > 60 else obj.question_text
    question_preview.short_description = "Question"

    def focus_link(self, obj):
        url = reverse('admin:content_chunkpunctuationfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def has_options(self, obj):
        return bool(obj.options)
    has_options.boolean = True
    has_options.short_description = "Has Options"

    def options_preview(self, obj):
        if not obj.options:
            return "No options"
        # FIXED: use options_list property, not get_options_list() method
        options = obj.options_list
        html = "<ul style='margin:0;padding-left:15px;'>"
        for opt in options:
            if opt == obj.correct_answer:
                html += f"<li><span style='color:green;font-weight:bold'>✓ {opt}</span></li>"
            else:
                html += f"<li>{opt}</li>"
        html += "</ul>"
        return format_html(html)
    options_preview.short_description = "Options Preview"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("focus", "focus__mark")


@admin.register(PunctuationPracticeAttempt)
class PunctuationPracticeAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user_link", "focus_link", "attempt_number",
        "cycle_number", "score_percent", "is_passed", "created_at",
    )
    list_filter = ("is_passed", "attempt_number", "cycle_number", "created_at")
    search_fields = ("user__username", "focus__focus_title")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    # FIXED: only reference fields that actually exist on the model
    readonly_fields = ("user", "focus", "attempt_number", "cycle_number",
                       "score_percent", "is_passed", "questions_data", "created_at")

    fieldsets = (
        ("Student", {
            "fields": ("user", "focus")
        }),
        ("Attempt Info", {
            "fields": ("attempt_number", "cycle_number", "created_at")
        }),
        ("Results", {
            "fields": ("score_percent", "is_passed")  # FIXED: removed correct_answers/total_questions
        }),
        ("Snapshot", {
            "fields": ("questions_data",),
            "classes": ("collapse",),
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def focus_link(self, obj):
        url = reverse('admin:content_chunkpunctuationfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PunctuationTestAttempt)
class PunctuationTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user_link", "focus_link", "attempt_number", "cycle_number",
        "score_percent", "is_mastered", "correct_answers", "total_questions", "created_at",
    )
    list_filter = ("is_mastered", "attempt_number", "cycle_number", "created_at")
    search_fields = ("user__username", "focus__focus_title")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in PunctuationTestAttempt._meta.fields]

    fieldsets = (
        ("Student", {
            "fields": ("user", "focus")
        }),
        ("Attempt Info", {
            "fields": ("attempt_number", "cycle_number", "created_at")
        }),
        ("Results", {
            "fields": ("score_percent", "is_mastered", "correct_answers", "total_questions")
        }),
        ("Snapshot", {
            "fields": ("questions_data",),
            "classes": ("collapse",),
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def focus_link(self, obj):
        url = reverse('admin:content_chunkpunctuationfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "focus")


__all__ = [
    'PunctuationMarkAdmin',
    'PunctuationRuleAdmin',
    'PunctuationExampleAdmin',
    'ChunkPunctuationFocusRuleAdmin',
    'ChunkPunctuationFocusAdmin',
    'PunctuationQuestionAdmin',
    'PunctuationPracticeAttemptAdmin',
    'PunctuationTestAttemptAdmin',
]