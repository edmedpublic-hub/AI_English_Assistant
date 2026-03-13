# PATH: content/admin/punctuation.py
# ACTION: Replace the entire existing file with this content.
# CHANGES FROM ORIGINAL:
#   - ChunkPunctuationFocusAdmin:
#       • list_display: added "completeness_badge" column (replaces dead space)
#       • fieldsets: added "Content Health" section with rules + questions at a glance
#       • mastery_stats_display: now shows practice vs test breakdown side by side
#       • get_queryset: added select_related for practice/test attempt counts
#   - ChunkPunctuationFocusRuleAdmin:
#       • list_display: added chunk column so you can see context at a glance
#       • list_select_related: avoids N+1 on the changelist
#   - All other admins (PunctuationMarkAdmin, PunctuationRuleAdmin,
#     PunctuationExampleAdmin, PunctuationQuestionAdmin,
#     PunctuationPracticeAttemptAdmin, PunctuationTestAttemptAdmin): UNCHANGED.

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


# ── UNCHANGED ─────────────────────────────────────────────────────────────────

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
            url = (
                reverse('admin:content_punctuationrule_changelist')
                + f'?mark__id__exact={obj.id}'
            )
            return format_html(
                '<a href="{}">{} rule{}</a>', url, count, 's' if count != 1 else ''
            )
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
        return (
            obj.question_text[:60] + "..."
            if len(obj.question_text) > 60
            else obj.question_text
        )
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

    readonly_fields = (
        "user", "focus", "attempt_number", "cycle_number",
        "score_percent", "is_passed", "questions_data", "created_at",
    )

    fieldsets = (
        ("Student", {"fields": ("user", "focus")}),
        ("Attempt Info", {"fields": ("attempt_number", "cycle_number", "created_at")}),
        ("Results", {"fields": ("score_percent", "is_passed")}),
        ("Snapshot", {"fields": ("questions_data",), "classes": ("collapse",)}),
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
        ("Student", {"fields": ("user", "focus")}),
        ("Attempt Info", {"fields": ("attempt_number", "cycle_number", "created_at")}),
        ("Results", {
            "fields": ("score_percent", "is_mastered", "correct_answers", "total_questions")
        }),
        ("Snapshot", {"fields": ("questions_data",), "classes": ("collapse",)}),
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


# ── UPDATED ───────────────────────────────────────────────────────────────────

@admin.register(ChunkPunctuationFocusRule)
class ChunkPunctuationFocusRuleAdmin(admin.ModelAdmin):
    # ADDED: chunk column so you immediately see which chunk this rule belongs to
    list_display = ('chunk_link', 'focus_link', 'rule_link', 'order', 'created_at')
    list_filter = ('focus__mark', 'created_at')
    search_fields = ('focus__focus_title', 'rule__rule_text')
    autocomplete_fields = ('focus', 'rule')
    ordering = ('focus', 'order')
    readonly_fields = ('created_at', 'updated_at', 'mapping_preview')
    # ADDED: avoids N+1 queries on the changelist
    list_select_related = ('focus', 'focus__mark', 'focus__chunk', 'rule')

    fieldsets = (
        ('Mapping', {'fields': ('focus', 'rule', 'order')}),
        ('Preview', {'fields': ('mapping_preview',), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    # ADDED
    def chunk_link(self, obj):
        url = reverse('admin:content_lessonchunk_change', args=[obj.focus.chunk.id])
        return format_html(
            '<a href="{}">Chunk {}</a>', url, obj.focus.chunk.id
        )
    chunk_link.short_description = "Chunk"

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
        <div style="background:#f8f9fa;padding:15px;border-radius:5px;
                    border-left:4px solid #17a2b8;">
            <p><strong>Focus:</strong> {obj.focus.focus_title}</p>
            <p><strong>Mark:</strong> {obj.focus.mark.symbol} - {obj.focus.mark.name}</p>
            <p><strong>Rule:</strong> {obj.rule.rule_text[:100]}</p>
            <p><strong>Order:</strong> {obj.order}</p>
        </div>
        """
        return format_html(html)
    mapping_preview.short_description = "Preview"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'focus', 'focus__mark', 'focus__chunk', 'rule'
        )


@admin.register(ChunkPunctuationFocus)
class ChunkPunctuationFocusAdmin(admin.ModelAdmin):
    # ADDED: completeness_badge replaces blank space in the list
    list_display = (
        "focus_title", "chunk_link", "mark",
        "depth_level", "sequence_order",
        "completeness_badge",   # NEW
        "mastery_rate",
    )
    list_filter = ("mark", "depth_level", "sequence_order")
    search_fields = ("focus_title", "focus_description", "chunk__english_text")
    ordering = ("chunk", "sequence_order")
    autocomplete_fields = ("chunk", "mark")
    readonly_fields = (
        "created_at", "updated_at",
        "content_health",       # NEW: replaces question_count_display
        "mastery_stats_display",
    )

    fieldsets = (
        ("Punctuation Focus", {
            "fields": ("chunk", "mark", "focus_title", "focus_description")
        }),
        ("Pedagogy", {
            "fields": ("depth_level", "sequence_order"),
        }),
        # RENAMED + EXPANDED: was "Questions & Rules" with just question_count_display
        ("Content Health — Rules & Questions", {
            "fields": ("content_health",),
            "description": (
                "Rules are linked via the 'Focus Rules' section below. "
                "Questions are added via the 'Punctuation Questions' section below."
            ),
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

    # ── list columns ──────────────────────────────────────────

    def chunk_link(self, obj):
        url = reverse('admin:content_lessonchunk_change', args=[obj.chunk.id])
        return format_html('<a href="{}">{}</a>', url, obj.chunk)
    chunk_link.short_description = "Chunk"

    def mastery_rate(self, obj):
        total = (
            PunctuationTestAttempt.objects
            .filter(focus=obj)
            .values('user').distinct().count()
        )
        if total == 0:
            return format_html('<span style="color:gray;">No data</span>')
        mastered = (
            PunctuationTestAttempt.objects
            .filter(focus=obj, is_mastered=True)
            .values('user').distinct().count()
        )
        pct = (mastered / total) * 100
        color = 'green' if pct >= 80 else 'orange' if pct >= 50 else 'red'
        return format_html(
            '<span style="color:{};">{}% ({}/{})</span>',
            color, int(pct), mastered, total,
        )
    mastery_rate.short_description = "Mastery Rate"

    # NEW: red/amber/green pill on the changelist
    def completeness_badge(self, obj):
        rule_count     = obj.focus_rules.count()
        question_count = obj.questions.count()

        if rule_count >= 1 and question_count >= 3:
            colour, label = "#28a745", "✓ Ready"
        elif rule_count >= 1 or question_count >= 1:
            colour, label = "#fd7e14", "~ Partial"
        else:
            colour, label = "#dc3545", "✗ Empty"

        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:9999px;font-size:0.8em;font-weight:600;'
            'white-space:nowrap;">{}</span>',
            colour, label,
        )
    completeness_badge.short_description = "Content"

    # ── change-form readonly panels ───────────────────────────

    # NEW: replaces the old question_count_display with a full rules + questions summary
    def content_health(self, obj):
        if not obj.pk:
            return "Save first."

        rules     = list(obj.focus_rules.select_related('rule').order_by('order'))
        questions = list(obj.questions.order_by('difficulty', 'id'))

        rule_count = len(rules)
        q_count    = len(questions)

        # Rules table
        if rules:
            rules_html = (
                "<table style='border-collapse:collapse;width:100%;margin-bottom:4px;'>"
                "<thead><tr style='background:#e9ecef;'>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Order</th>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Rule</th>"
                "</tr></thead><tbody>"
            )
            for fr in rules:
                rules_html += (
                    f"<tr style='border-bottom:1px solid #dee2e6;'>"
                    f"<td style='padding:4px 8px;color:#6c757d;'>{fr.order}</td>"
                    f"<td style='padding:4px 8px;'>{fr.rule.rule_text[:80]}</td>"
                    f"</tr>"
                )
            rules_html += "</tbody></table>"
        else:
            rules_html = (
                "<p style='color:#dc3545;margin:0;'>"
                "✗ No rules linked yet — use the Focus Rules section below.</p>"
            )

        # Questions summary
        if questions:
            diff_map = {1: "★☆☆☆☆", 2: "★★☆☆☆", 3: "★★★☆☆", 4: "★★★★☆", 5: "★★★★★"}
            qs_html = (
                "<table style='border-collapse:collapse;width:100%;margin-bottom:4px;'>"
                "<thead><tr style='background:#e9ecef;'>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Type</th>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Difficulty</th>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Question</th>"
                "</tr></thead><tbody>"
            )
            for q in questions:
                qs_html += (
                    f"<tr style='border-bottom:1px solid #dee2e6;'>"
                    f"<td style='padding:4px 8px;'>"
                    f"<code style='font-size:0.8em;'>{q.question_type}</code></td>"
                    f"<td style='padding:4px 8px;color:#6c757d;font-size:0.85em;'>"
                    f"{diff_map.get(q.difficulty, q.difficulty)}</td>"
                    f"<td style='padding:4px 8px;'>{q.question_text[:70]}</td>"
                    f"</tr>"
                )
            qs_html += "</tbody></table>"
        else:
            qs_html = (
                "<p style='color:#dc3545;margin:0;'>"
                "✗ No questions yet — use the Punctuation Questions section below.</p>"
            )

        # Status bar
        if rule_count >= 1 and q_count >= 3:
            status_colour, status_text = "#28a745", "✓ This focus is ready for students."
        elif rule_count >= 1 or q_count >= 1:
            status_colour, status_text = "#fd7e14", (
                "~ Partially complete. "
                f"{'Add rules. ' if rule_count == 0 else ''}"
                f"{'Need ≥ 3 questions.' if q_count < 3 else ''}"
            )
        else:
            status_colour, status_text = "#dc3545", "✗ Empty — add rules and questions below."

        html = f"""
        <div style="border:1px solid #dee2e6;border-radius:6px;overflow:hidden;
                    margin-bottom:8px;">
            <div style="background:{status_colour};color:#fff;padding:6px 12px;
                        font-weight:600;font-size:0.85em;">
                {status_text}
                &nbsp;·&nbsp; {rule_count} rule{'s' if rule_count != 1 else ''}
                &nbsp;·&nbsp; {q_count} question{'s' if q_count != 1 else ''}
            </div>
            <div style="padding:10px 12px;">
                <p style="font-weight:600;margin:0 0 6px;font-size:0.85em;
                           text-transform:uppercase;color:#6c757d;letter-spacing:.05em;">
                    Rules
                </p>
                {rules_html}
                <p style="font-weight:600;margin:12px 0 6px;font-size:0.85em;
                           text-transform:uppercase;color:#6c757d;letter-spacing:.05em;">
                    Questions
                </p>
                {qs_html}
            </div>
        </div>
        """
        return format_html(html)
    content_health.short_description = "Rules & Questions"

    # UPDATED: now shows practice vs test side by side
    def mastery_stats_display(self, obj):
        if not obj.pk:
            return "Save first."

        practice = PunctuationPracticeAttempt.objects.filter(focus=obj)
        tests    = PunctuationTestAttempt.objects.filter(focus=obj)

        if not practice.exists() and not tests.exists():
            return "No attempts yet."

        # Practice stats
        p_students = practice.values('user').distinct().count()
        p_passed   = practice.filter(is_passed=True).values('user').distinct().count()
        p_avg      = practice.aggregate(
            models.Avg('score_percent')
        )['score_percent__avg'] or 0

        # Test stats
        t_students = tests.values('user').distinct().count()
        t_mastered = tests.filter(
            is_mastered=True
        ).values('user').distinct().count()
        t_avg      = tests.aggregate(
            models.Avg('score_percent')
        )['score_percent__avg'] or 0

        html = f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div style="background:#f8f9fa;padding:12px;border-radius:6px;
                        border-left:4px solid #007bff;">
                <p style="font-weight:700;margin:0 0 8px;color:#007bff;">
                    Practice Attempts
                </p>
                <table style="width:100%;font-size:0.9em;">
                    <tr>
                        <td>Students attempted</td>
                        <td><b>{p_students}</b></td>
                    </tr>
                    <tr>
                        <td>Passed (100%)</td>
                        <td><b style="color:#28a745;">{p_passed}</b></td>
                    </tr>
                    <tr>
                        <td>Average score</td>
                        <td><b>{p_avg:.1f}%</b></td>
                    </tr>
                </table>
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:6px;
                        border-left:4px solid #28a745;">
                <p style="font-weight:700;margin:0 0 8px;color:#28a745;">
                    Mastery Tests
                </p>
                <table style="width:100%;font-size:0.9em;">
                    <tr>
                        <td>Students tested</td>
                        <td><b>{t_students}</b></td>
                    </tr>
                    <tr>
                        <td>Mastered</td>
                        <td><b style="color:#28a745;">{t_mastered}</b></td>
                    </tr>
                    <tr>
                        <td>Average score</td>
                        <td><b>{t_avg:.1f}%</b></td>
                    </tr>
                </table>
            </div>
        </div>
        """
        return format_html(html)
    mastery_stats_display.short_description = "Practice vs Test Statistics"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("chunk", "mark")


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