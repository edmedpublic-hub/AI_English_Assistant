# PATH: content/admin/testing.py
# ACTION: Replace the entire existing file with this content.
#
# Models covered (all from content/models/testing.py):
#   UnitTestSession         — one test session per user per unit (max 3 attempts)
#   UnitTestQuestion        — questions belonging to a session, across all domains
#   UnitTestAnswer          — student answers to each question
#   VocabularyUnitTestAttempt — standalone chunk-level vocab test (optional session link)
#
# Registered admins (matches content/admin/__init__.py imports exactly):
#   UnitTestSessionAdmin, UnitTestQuestionAdmin, UnitTestAnswerAdmin,
#   VocabularyUnitTestAttemptAdmin

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models

from content.models.testing import (
    UnitTestSession,
    UnitTestQuestion,
    UnitTestAnswer,
    VocabularyUnitTestAttempt,
)


# ═══════════════════════════════════════════════════════════════
#  INLINES
# ═══════════════════════════════════════════════════════════════

class UnitTestQuestionInline(admin.TabularInline):
    """Questions nested inside UnitTestSessionAdmin."""
    model = UnitTestQuestion
    extra = 0
    fields = (
        "order", "domain", "question_type", "difficulty",
        "question_text_preview", "points",
    )
    readonly_fields = ("question_text_preview",)
    ordering = ("order",)
    show_change_link = True
    can_delete = False

    def question_text_preview(self, obj):
        if not obj.pk:
            return ""
        return format_html(
            '<span style="color:#666;">{}</span>',
            obj.question_text[:80]
        )
    question_text_preview.short_description = "Preview"

    def has_add_permission(self, request, obj=None):
        return False


class UnitTestAnswerInline(admin.TabularInline):
    """Answers nested inside UnitTestQuestionAdmin."""
    model = UnitTestAnswer
    extra = 0
    fields = ("student_answer", "is_correct", "time_taken_seconds", "answered_at")
    readonly_fields = ("student_answer", "is_correct", "time_taken_seconds", "answered_at")
    ordering = ("-answered_at",)
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════
#  UNIT TEST SESSION ADMIN  ★ top-level entry point for unit testing
# ═══════════════════════════════════════════════════════════════

@admin.register(UnitTestSession)
class UnitTestSessionAdmin(admin.ModelAdmin):
    list_display = (
        "user_link", "unit_link", "attempt_number",
        "score_badge", "passed", "question_summary",
        "started_at", "completed_at",
    )
    list_filter = ("passed", "attempt_number", "unit__textbook", "started_at")
    search_fields = ("user__username", "unit__title")
    ordering = ("-started_at",)
    date_hierarchy = "started_at"
    list_select_related = ("user", "unit", "unit__textbook")
    readonly_fields = (
        "user", "unit", "attempt_number",
        "started_at", "completed_at", "time_taken_seconds",
        "total_questions", "correct_answers", "score_percentage", "passed",
        "domain_scores_display", "test_data",
    )

    fieldsets = (
        ("Student & Unit", {
            "fields": ("user", "unit", "attempt_number"),
        }),
        ("Timing", {
            "fields": ("started_at", "completed_at", "time_taken_seconds"),
        }),
        ("Results", {
            "fields": (
                "total_questions", "correct_answers",
                "score_percentage", "passed",
            ),
        }),
        ("Domain Breakdown", {
            "fields": ("domain_scores_display",),
        }),
        ("Raw Data", {
            "fields": ("test_data",),
            "classes": ("collapse",),
        }),
    )

    inlines = [UnitTestQuestionInline]

    # ── list columns ──────────────────────────────────────────

    def user_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def unit_link(self, obj):
        url = reverse("admin:content_unit_change", args=[obj.unit.id])
        return format_html('<a href="{}">{}</a>', url, obj.unit)
    unit_link.short_description = "Unit"

    def score_badge(self, obj):
        pct = obj.score_percentage
        colour = (
            "#28a745" if pct >= 70
            else "#fd7e14" if pct >= 40
            else "#dc3545"
        )
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:9999px;font-size:0.8em;font-weight:600;">'
            '{:.1f}%</span>',
            colour, pct,
        )
    score_badge.short_description = "Score"
    score_badge.admin_order_field = "score_percentage"

    def question_summary(self, obj):
        return format_html(
            '{} / {}',
            obj.correct_answers, obj.total_questions,
        )
    question_summary.short_description = "Correct / Total"

    # ── change-form panels ────────────────────────────────────

    def domain_scores_display(self, obj):
        """Renders domain_scores JSON as a readable table."""
        if not obj.domain_scores:
            return "No domain breakdown available."

        rows = ""
        for domain, data in obj.domain_scores.items():
            # data may be a dict like {"correct": 3, "total": 5, "score": 60.0}
            # or a plain number — handle both gracefully
            if isinstance(data, dict):
                correct = data.get("correct", "—")
                total   = data.get("total", "—")
                score   = data.get("score", None)
                score_str = f"{score:.1f}%" if isinstance(score, (int, float)) else "—"
            else:
                correct, total, score_str = "—", "—", f"{data}"

            rows += (
                f"<tr style='border-bottom:1px solid #dee2e6;'>"
                f"<td style='padding:5px 10px;text-transform:capitalize;"
                f"font-weight:600;'>{domain}</td>"
                f"<td style='padding:5px 10px;'>{correct} / {total}</td>"
                f"<td style='padding:5px 10px;'>{score_str}</td>"
                f"</tr>"
            )

        html = (
            "<table style='border-collapse:collapse;width:100%;max-width:400px;'>"
            "<thead><tr style='background:#e9ecef;'>"
            "<th style='padding:5px 10px;text-align:left;font-size:0.8em;'>Domain</th>"
            "<th style='padding:5px 10px;text-align:left;font-size:0.8em;'>Correct / Total</th>"
            "<th style='padding:5px 10px;text-align:left;font-size:0.8em;'>Score</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>"
        )
        return format_html(html)
    domain_scores_display.short_description = "Domain Scores"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════
#  UNIT TEST QUESTION ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(UnitTestQuestion)
class UnitTestQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "session_link", "order", "domain",
        "question_type", "difficulty", "points",
        "question_preview", "answer_count",
    )
    list_filter = ("domain", "question_type", "difficulty")
    search_fields = (
        "question_text",
        "session__user__username",
        "session__unit__title",
    )
    ordering = ("session", "order")
    list_select_related = ("session", "session__user", "session__unit")
    readonly_fields = (
        "session", "domain", "question_type", "difficulty",
        "order", "points", "question_text",
        "options", "correct_answer",
        "vocabulary_item", "grammar_concept",
        "punctuation_mark", "bloom_level",
    )

    fieldsets = (
        ("Session", {
            "fields": ("session", "order", "domain", "points"),
        }),
        ("Question", {
            "fields": (
                "question_type", "difficulty",
                "question_text", "options", "correct_answer",
            ),
        }),
        ("Domain Links", {
            "fields": (
                "vocabulary_item", "grammar_concept",
                "punctuation_mark", "bloom_level",
            ),
            "classes": ("collapse",),
            "description": "Which curriculum item this question tests.",
        }),
    )

    inlines = [UnitTestAnswerInline]

    def session_link(self, obj):
        url = reverse("admin:content_unittestsession_change", args=[obj.session.id])
        return format_html(
            '<a href="{}">{} — Attempt {}</a>',
            url,
            obj.session.user.username,
            obj.session.attempt_number,
        )
    session_link.short_description = "Session"

    def question_preview(self, obj):
        text = obj.question_text or ""
        return text[:60] + "…" if len(text) > 60 else text
    question_preview.short_description = "Question"

    def answer_count(self, obj):
        count = obj.answers.count()
        colour = "#28a745" if count > 0 else "#6c757d"
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            colour, count,
        )
    answer_count.short_description = "Answers"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════
#  UNIT TEST ANSWER ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(UnitTestAnswer)
class UnitTestAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "question_link", "answer_preview",
        "is_correct", "time_taken_seconds", "answered_at",
    )
    list_filter = ("is_correct", "answered_at")
    search_fields = (
        "student_answer",
        "question__question_text",
        "question__session__user__username",
    )
    ordering = ("-answered_at",)
    date_hierarchy = "answered_at"
    list_select_related = ("question", "question__session", "question__session__user")
    readonly_fields = (
        "question", "student_answer",
        "is_correct", "time_taken_seconds", "answered_at",
    )

    fieldsets = (
        ("Question", {"fields": ("question",)}),
        ("Answer", {
            "fields": (
                "student_answer", "is_correct",
                "time_taken_seconds", "answered_at",
            ),
        }),
    )

    def question_link(self, obj):
        url = reverse("admin:content_unittestquestion_change", args=[obj.question.id])
        return format_html(
            '<a href="{}">Q{} — {}</a>',
            url,
            obj.question.order,
            obj.question.session.user.username,
        )
    question_link.short_description = "Question"

    def answer_preview(self, obj):
        text = obj.student_answer or ""
        return text[:70] + "…" if len(text) > 70 else text
    answer_preview.short_description = "Answer"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════
#  VOCABULARY UNIT TEST ATTEMPT ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(VocabularyUnitTestAttempt)
class VocabularyUnitTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user_link", "context_link",
        "score_badge", "correct_answers", "total_questions",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "user__username",
        "lesson__title",
        "chunk__english_text",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("user", "lesson", "chunk", "unit_test_session")
    readonly_fields = (
        "user", "unit_test_session", "lesson", "chunk",
        "score_percent", "correct_answers", "total_questions",
        "questions_data", "answers_data", "created_at",
    )

    fieldsets = (
        ("Student", {
            "fields": ("user", "unit_test_session"),
        }),
        ("Context", {
            "fields": ("lesson", "chunk"),
            "description": (
                "Chunk-level vocab tests run independently of a full unit test. "
                "unit_test_session is optional."
            ),
        }),
        ("Results", {
            "fields": ("score_percent", "correct_answers", "total_questions"),
        }),
        ("Snapshot", {
            "fields": ("questions_data", "answers_data"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )

    # ── list columns ──────────────────────────────────────────

    def user_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def context_link(self, obj):
        """Shows chunk or lesson, whichever is set."""
        if obj.chunk_id:
            url = reverse("admin:content_lessonchunk_change", args=[obj.chunk_id])
            return format_html(
                '<a href="{}">Chunk {}</a>', url, obj.chunk_id
            )
        if obj.lesson_id:
            url = reverse("admin:content_lesson_change", args=[obj.lesson_id])
            return format_html(
                '<a href="{}">{}</a>', url, obj.lesson
            )
        return "—"
    context_link.short_description = "Chunk / Lesson"

    def score_badge(self, obj):
        pct = obj.score_percent
        colour = (
            "#28a745" if pct >= 80
            else "#fd7e14" if pct >= 50
            else "#dc3545"
        )
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:9999px;font-size:0.8em;font-weight:600;">'
            '{}%</span>',
            colour, pct,
        )
    score_badge.short_description = "Score"
    score_badge.admin_order_field = "score_percent"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "user", "lesson", "chunk", "unit_test_session"
        )


__all__ = [
    'UnitTestSessionAdmin',
    'UnitTestQuestionAdmin',
    'UnitTestAnswerAdmin',
    'VocabularyUnitTestAttemptAdmin',
]