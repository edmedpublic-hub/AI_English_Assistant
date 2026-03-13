# PATH: content/admin/writing.py
# ACTION: This file was accidentally overwritten. This is the restored version,
#         built from content/models/writing.py to match all field and related names exactly.
#
# Models covered:
#   ChunkWritingFocus       — chunk-level focus (related_name: writing_focuses on LessonChunk)
#   UnitWritingTask         — unit-level extended task (related_name: writing_tasks on Unit)
#   WritingPrompt           — linked to either a focus OR a task (never both)
#   WritingPracticeAttempt  — practice layer (related_name: practice_attempts on focus/prompt)
#   WritingTestAttempt      — test layer (related_name: test_attempts on focus/task/prompt)
#
# Registered admins (matches content/admin/__init__.py imports exactly):
#   ChunkWritingFocusAdmin, UnitWritingTaskAdmin, WritingPromptAdmin,
#   WritingPracticeAttemptAdmin, WritingTestAttemptAdmin

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models

from content.models.writing import (
    ChunkWritingFocus,
    UnitWritingTask,
    WritingPrompt,
    WritingPracticeAttempt,
    WritingTestAttempt,
)


# ═══════════════════════════════════════════════════════════════
#  INLINES
# ═══════════════════════════════════════════════════════════════

class WritingPromptInline(admin.StackedInline):
    """Prompts nested inside ChunkWritingFocusAdmin or UnitWritingTaskAdmin."""
    model = WritingPrompt
    extra = 1
    fields = (
        "prompt_type", "prompt_text",
        "expected_keywords", "rubric",
    )
    show_change_link = True


class WritingPracticeAttemptInline(admin.TabularInline):
    model = WritingPracticeAttempt
    extra = 0
    readonly_fields = (
        "user", "prompt", "attempt_number", "cycle_number",
        "keyword_match_score", "is_passed", "created_at",
    )
    fields = (
        "user", "prompt", "attempt_number", "cycle_number",
        "keyword_match_score", "is_passed", "created_at",
    )
    ordering = ("-created_at",)
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class WritingTestAttemptInline(admin.TabularInline):
    model = WritingTestAttempt
    extra = 0
    readonly_fields = (
        "user", "prompt", "attempt_number", "cycle_number",
        "overall_score", "is_mastered", "created_at",
    )
    fields = (
        "user", "prompt", "attempt_number", "cycle_number",
        "overall_score", "is_mastered", "created_at",
    )
    ordering = ("-created_at",)
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════
#  CHUNK WRITING FOCUS ADMIN  ★ main domain editor for chunk-level writing
# ═══════════════════════════════════════════════════════════════

@admin.register(ChunkWritingFocus)
class ChunkWritingFocusAdmin(admin.ModelAdmin):
    list_display = (
        "focus_title", "chunk_link", "depth_level",
        "sequence_order", "completeness_badge", "mastery_rate",
    )
    list_filter = ("depth_level", "sequence_order")
    search_fields = ("focus_title", "focus_description", "chunk__english_text")
    ordering = ("chunk", "sequence_order")
    autocomplete_fields = ("chunk",)
    readonly_fields = (
        "created_at", "updated_at",
        "content_health", "mastery_stats_display",
    )

    fieldsets = (
        ("Writing Focus", {
            "fields": (
                "chunk", "focus_title", "focus_description",
                "depth_level", "sequence_order",
            )
        }),
        ("Content Health — Prompts & Attempts", {
            "fields": ("content_health",),
            "description": (
                "Prompts are added via the Writing Prompts section below. "
                "Each prompt can be used in practice and test attempts."
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

    inlines = [WritingPromptInline, WritingPracticeAttemptInline, WritingTestAttemptInline]

    # ── list columns ──────────────────────────────────────────

    def chunk_link(self, obj):
        url = reverse("admin:content_lessonchunk_change", args=[obj.chunk.id])
        return format_html('<a href="{}">{}</a>', url, obj.chunk)
    chunk_link.short_description = "Chunk"

    def completeness_badge(self, obj):
        prompt_count = obj.prompts.count()
        if prompt_count >= 2:
            colour, label = "#28a745", "✓ Ready"
        elif prompt_count == 1:
            colour, label = "#fd7e14", "~ Partial"
        else:
            colour, label = "#dc3545", "✗ Empty"
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:9999px;font-size:0.8em;font-weight:600;">{}</span>',
            colour, label,
        )
    completeness_badge.short_description = "Content"

    def mastery_rate(self, obj):
        total = (
            WritingTestAttempt.objects
            .filter(focus=obj)
            .values("user").distinct().count()
        )
        if total == 0:
            return format_html('<span style="color:gray;">No data</span>')
        mastered = (
            WritingTestAttempt.objects
            .filter(focus=obj, is_mastered=True)
            .values("user").distinct().count()
        )
        pct = (mastered / total) * 100
        color = "green" if pct >= 80 else "orange" if pct >= 50 else "red"
        return format_html(
            '<span style="color:{};">{}% ({}/{})</span>',
            color, int(pct), mastered, total,
        )
    mastery_rate.short_description = "Mastery Rate"

    # ── change-form panels ────────────────────────────────────

    def content_health(self, obj):
        if not obj.pk:
            return "Save first."

        prompts = list(obj.prompts.order_by("id"))
        prompt_count = len(prompts)

        if prompts:
            rows = ""
            for p in prompts:
                rows += (
                    f"<tr style='border-bottom:1px solid #dee2e6;'>"
                    f"<td style='padding:4px 8px;'>"
                    f"<code style='font-size:0.8em;'>{p.prompt_type}</code></td>"
                    f"<td style='padding:4px 8px;'>{p.prompt_text[:80]}</td>"
                    f"<td style='padding:4px 8px;color:#6c757d;font-size:0.85em;'>"
                    f"{'✓ keywords' if p.expected_keywords else '—'}</td>"
                    f"</tr>"
                )
            prompts_html = (
                "<table style='border-collapse:collapse;width:100%;'>"
                "<thead><tr style='background:#e9ecef;'>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Type</th>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Prompt</th>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Keywords</th>"
                f"</tr></thead><tbody>{rows}</tbody></table>"
            )
        else:
            prompts_html = (
                "<p style='color:#dc3545;margin:0;'>"
                "✗ No prompts yet — add them in the Writing Prompts section below.</p>"
            )

        if prompt_count >= 2:
            status_colour, status_text = "#28a745", "✓ This focus is ready for students."
        elif prompt_count == 1:
            status_colour, status_text = "#fd7e14", "~ Add at least one more prompt."
        else:
            status_colour, status_text = "#dc3545", "✗ Empty — add prompts below."

        html = f"""
        <div style="border:1px solid #dee2e6;border-radius:6px;overflow:hidden;">
            <div style="background:{status_colour};color:#fff;padding:6px 12px;
                        font-weight:600;font-size:0.85em;">
                {status_text}
                &nbsp;·&nbsp;
                {prompt_count} prompt{'s' if prompt_count != 1 else ''}
            </div>
            <div style="padding:10px 12px;">
                <p style="font-weight:600;margin:0 0 6px;font-size:0.85em;
                           text-transform:uppercase;color:#6c757d;letter-spacing:.05em;">
                    Prompts
                </p>
                {prompts_html}
            </div>
        </div>
        """
        return format_html(html)
    content_health.short_description = "Prompts"

    def mastery_stats_display(self, obj):
        if not obj.pk:
            return "Save first."

        practice = WritingPracticeAttempt.objects.filter(focus=obj)
        tests    = WritingTestAttempt.objects.filter(focus=obj)

        if not practice.exists() and not tests.exists():
            return "No attempts yet."

        p_students = practice.values("user").distinct().count()
        p_passed   = practice.filter(
            is_passed=True).values("user").distinct().count()
        p_avg      = practice.aggregate(
            models.Avg("keyword_match_score"))["keyword_match_score__avg"] or 0

        t_students = tests.values("user").distinct().count()
        t_mastered = tests.filter(
            is_mastered=True).values("user").distinct().count()
        t_avg      = tests.aggregate(
            models.Avg("overall_score"))["overall_score__avg"] or 0

        html = f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div style="background:#f8f9fa;padding:12px;border-radius:6px;
                        border-left:4px solid #007bff;">
                <p style="font-weight:700;margin:0 0 8px;color:#007bff;">
                    Practice Attempts
                </p>
                <table style="width:100%;font-size:0.9em;">
                    <tr><td>Students attempted</td><td><b>{p_students}</b></td></tr>
                    <tr><td>Passed</td>
                        <td><b style="color:#28a745;">{p_passed}</b></td></tr>
                    <tr><td>Avg keyword score</td><td><b>{p_avg:.1f}%</b></td></tr>
                </table>
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:6px;
                        border-left:4px solid #28a745;">
                <p style="font-weight:700;margin:0 0 8px;color:#28a745;">
                    Mastery Tests
                </p>
                <table style="width:100%;font-size:0.9em;">
                    <tr><td>Students tested</td><td><b>{t_students}</b></td></tr>
                    <tr><td>Mastered</td>
                        <td><b style="color:#28a745;">{t_mastered}</b></td></tr>
                    <tr><td>Average score</td><td><b>{t_avg:.1f}%</b></td></tr>
                </table>
            </div>
        </div>
        """
        return format_html(html)
    mastery_stats_display.short_description = "Practice vs Test Statistics"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("chunk")


# ═══════════════════════════════════════════════════════════════
#  UNIT WRITING TASK ADMIN  (unit-level extended writing)
# ═══════════════════════════════════════════════════════════════

@admin.register(UnitWritingTask)
class UnitWritingTaskAdmin(admin.ModelAdmin):
    list_display = (
        "task_title", "unit_link", "stage",
        "difficulty_level", "order", "prompt_count", "mastery_rate",
    )
    list_filter = ("stage", "difficulty_level", "unit__textbook")
    search_fields = ("task_title", "task_description", "unit__title")
    ordering = ("unit", "order")
    autocomplete_fields = ("unit",)
    readonly_fields = ("created_at", "updated_at", "mastery_stats_display")

    fieldsets = (
        ("Task Details", {
            "fields": (
                "unit", "task_title", "task_description",
                "stage", "difficulty_level", "order",
            )
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

    inlines = [WritingPromptInline, WritingTestAttemptInline]

    def unit_link(self, obj):
        url = reverse("admin:content_unit_change", args=[obj.unit.id])
        return format_html('<a href="{}">{}</a>', url, obj.unit)
    unit_link.short_description = "Unit"

    def prompt_count(self, obj):
        count = obj.prompts.count()
        colour = "#28a745" if count >= 1 else "#dc3545"
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>', colour, count
        )
    prompt_count.short_description = "Prompts"

    def mastery_rate(self, obj):
        total = (
            WritingTestAttempt.objects
            .filter(task=obj)
            .values("user").distinct().count()
        )
        if total == 0:
            return format_html('<span style="color:gray;">No data</span>')
        mastered = (
            WritingTestAttempt.objects
            .filter(task=obj, is_mastered=True)
            .values("user").distinct().count()
        )
        pct = (mastered / total) * 100
        color = "green" if pct >= 80 else "orange" if pct >= 50 else "red"
        return format_html(
            '<span style="color:{};">{}% ({}/{})</span>',
            color, int(pct), mastered, total,
        )
    mastery_rate.short_description = "Mastery Rate"

    def mastery_stats_display(self, obj):
        if not obj.pk:
            return "Save first."
        tests = WritingTestAttempt.objects.filter(task=obj)
        if not tests.exists():
            return "No test attempts yet."
        t_students = tests.values("user").distinct().count()
        t_mastered = tests.filter(
            is_mastered=True).values("user").distinct().count()
        t_avg      = tests.aggregate(
            models.Avg("overall_score"))["overall_score__avg"] or 0
        html = f"""
        <div style="background:#f8f9fa;padding:12px;border-radius:6px;
                    border-left:4px solid #28a745;max-width:300px;">
            <p style="font-weight:700;margin:0 0 8px;color:#28a745;">
                Mastery Tests (≥70% required)
            </p>
            <table style="width:100%;font-size:0.9em;">
                <tr><td>Students tested</td><td><b>{t_students}</b></td></tr>
                <tr><td>Mastered (≥70%)</td>
                    <td><b style="color:#28a745;">{t_mastered}</b></td></tr>
                <tr><td>Average score</td><td><b>{t_avg:.1f}%</b></td></tr>
            </table>
        </div>
        """
        return format_html(html)
    mastery_stats_display.short_description = "Test Statistics"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("unit")


# ═══════════════════════════════════════════════════════════════
#  WRITING PROMPT ADMIN  (standalone — also surfaced via inlines)
# ═══════════════════════════════════════════════════════════════

@admin.register(WritingPrompt)
class WritingPromptAdmin(admin.ModelAdmin):
    list_display = (
        "prompt_preview", "prompt_type",
        "linked_to", "has_keywords", "has_rubric",
    )
    list_filter = ("prompt_type",)
    search_fields = ("prompt_text", "focus__focus_title", "task__task_title")
    ordering = ("id",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Prompt Details", {
            "fields": ("prompt_type", "prompt_text")
        }),
        ("Linkage — choose exactly one", {
            "fields": ("focus", "task"),
            "description": (
                "Link this prompt to a Chunk Writing Focus (sentence-level) "
                "OR a Unit Writing Task (paragraph/essay). Never both."
            ),
        }),
        ("Automated Scoring", {
            "fields": ("expected_keywords", "rubric"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def prompt_preview(self, obj):
        text = obj.prompt_text or ""
        return text[:70] + "…" if len(text) > 70 else text
    prompt_preview.short_description = "Prompt"

    def linked_to(self, obj):
        if obj.focus_id:
            url = reverse(
                "admin:content_chunkwritingfocus_change", args=[obj.focus_id]
            )
            return format_html(
                '<a href="{}">Focus: {}</a>', url, obj.focus.focus_title
            )
        if obj.task_id:
            url = reverse(
                "admin:content_unitwritingtask_change", args=[obj.task_id]
            )
            return format_html(
                '<a href="{}">Task: {}</a>', url, obj.task.task_title
            )
        return format_html('<span style="color:#dc3545;">⚠ Not linked</span>')
    linked_to.short_description = "Linked To"

    def has_keywords(self, obj):
        return bool(obj.expected_keywords)
    has_keywords.boolean = True
    has_keywords.short_description = "Keywords"

    def has_rubric(self, obj):
        return bool(obj.rubric)
    has_rubric.boolean = True
    has_rubric.short_description = "Rubric"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "focus", "focus__chunk", "task", "task__unit"
        )


# ═══════════════════════════════════════════════════════════════
#  WRITING PRACTICE ATTEMPT ADMIN  (read-only — student data)
# ═══════════════════════════════════════════════════════════════

@admin.register(WritingPracticeAttempt)
class WritingPracticeAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user_link", "focus_link", "prompt_link",
        "attempt_number", "cycle_number",
        "keyword_match_score", "is_passed", "created_at",
    )
    list_filter = ("is_passed", "attempt_number", "cycle_number", "created_at")
    search_fields = ("user__username", "focus__focus_title", "prompt__prompt_text")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = (
        "user", "focus", "prompt",
        "attempt_number", "cycle_number",
        "response_text", "keyword_match_score",
        "is_passed", "time_spent_seconds", "hints_used", "created_at",
    )

    fieldsets = (
        ("Student", {"fields": ("user", "focus", "prompt")}),
        ("Attempt Info", {
            "fields": ("attempt_number", "cycle_number", "created_at")
        }),
        ("Results", {
            "fields": ("keyword_match_score", "is_passed",
                       "time_spent_seconds", "hints_used")
        }),
        ("Response", {
            "fields": ("response_text",),
            "classes": ("collapse",),
        }),
    )

    def user_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def focus_link(self, obj):
        if not obj.focus_id:
            return "—"
        url = reverse("admin:content_chunkwritingfocus_change", args=[obj.focus_id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def prompt_link(self, obj):
        url = reverse("admin:content_writingprompt_change", args=[obj.prompt.id])
        return format_html(
            '<a href="{}">{}</a>', url, obj.prompt.prompt_text[:40]
        )
    prompt_link.short_description = "Prompt"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "user", "focus", "prompt"
        )


# ═══════════════════════════════════════════════════════════════
#  WRITING TEST ATTEMPT ADMIN  (read-only — student data)
# ═══════════════════════════════════════════════════════════════

@admin.register(WritingTestAttempt)
class WritingTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user_link", "context_link", "prompt_link",
        "attempt_number", "cycle_number",
        "overall_score", "is_mastered", "created_at",
    )
    list_filter = ("is_mastered", "attempt_number", "cycle_number", "created_at")
    search_fields = (
        "user__username", "focus__focus_title",
        "task__task_title", "prompt__prompt_text",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in WritingTestAttempt._meta.fields]

    fieldsets = (
        ("Student", {"fields": ("user", "focus", "task", "prompt")}),
        ("Attempt Info", {
            "fields": ("attempt_number", "cycle_number", "created_at")
        }),
        ("Results", {
            "fields": (
                "overall_score", "is_mastered",
                "rubric_scores", "feedback", "time_spent_seconds",
            )
        }),
        ("Response", {
            "fields": ("response_text",),
            "classes": ("collapse",),
        }),
    )

    def user_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def context_link(self, obj):
        """Shows either the focus or the task this attempt belongs to."""
        if obj.focus_id:
            url = reverse(
                "admin:content_chunkwritingfocus_change", args=[obj.focus_id]
            )
            return format_html(
                '<a href="{}">Focus: {}</a>', url, obj.focus.focus_title
            )
        if obj.task_id:
            url = reverse(
                "admin:content_unitwritingtask_change", args=[obj.task_id]
            )
            return format_html(
                '<a href="{}">Task: {}</a>', url, obj.task.task_title
            )
        return "—"
    context_link.short_description = "Focus / Task"

    def prompt_link(self, obj):
        url = reverse("admin:content_writingprompt_change", args=[obj.prompt.id])
        return format_html(
            '<a href="{}">{}</a>', url, obj.prompt.prompt_text[:40]
        )
    prompt_link.short_description = "Prompt"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "user", "focus", "task", "prompt"
        )


__all__ = [
    'ChunkWritingFocusAdmin',
    'UnitWritingTaskAdmin',
    'WritingPromptAdmin',
    'WritingPracticeAttemptAdmin',
    'WritingTestAttemptAdmin',
]