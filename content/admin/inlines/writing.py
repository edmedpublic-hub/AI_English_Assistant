# content/admin/inlines/writing.py
#
# Complete replacement of the previous inlines file.
# All inlines reference the new writing models only.
# No references to ChunkWritingFocus, UnitWritingTask, or WritingPrompt.
#
# Inlines provided:
#   WritingStageContentInline  — appears inside Unit admin
#   WritingAttemptInline       — appears inside WritingStageContent admin
#   WritingInterventionInline  — appears inside WritingAttempt admin
#   WritingStageMasteryInline  — appears inside WritingStageContent admin

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from content.models.writing import (
    WritingStageContent,
    WritingAttempt,
    WritingIntervention,
    WritingStageMastery,
    STATUS_PENDING,
    STATUS_APPROVED,
    STATUS_REVISION,
    PHASE_PRODUCE,
    EVAL_TEACHER,
    EVAL_AI_TEACHER,
)


# ============================================================
# 1. WRITING STAGE CONTENT INLINE
#    Appears inside Unit admin.
#    Admin enters content per stage per unit here.
# ============================================================

class WritingStageContentInline(admin.StackedInline):
    """
    Nested inside Unit admin.
    One record per stage the admin has prepared for this unit.
    Admin adds a new record for each stage they want to activate.
    """
    model           = WritingStageContent
    extra           = 0
    min_num         = 0
    show_change_link = True
    ordering        = ["stage__number"]

    fields = (
        "stage",
        "is_complete",
        "content_summary",
    )
    readonly_fields = ("content_summary",)

    def content_summary(self, obj):
        """
        Quick health check — shows which fields are filled
        so admin can see at a glance what is missing.
        """
        if not obj.pk:
            return "Save first to see content summary."

        checks = {
            "Model sentence (original)":  bool(obj.model_sentence_original),
            "Model sentence (converted)": bool(obj.model_sentence_converted),
            "Conversion note":            bool(obj.conversion_note),
            "Dissect question":           bool(obj.dissect_question),
            "Dissect answer":             bool(obj.dissect_answer),
            "Imitate frame":              bool(obj.imitate_frame),
            "Produce prompt":             bool(obj.produce_prompt),
        }

        rows = ""
        all_filled = True
        for label, filled in checks.items():
            icon   = "✓" if filled else "✗"
            colour = "#28a745" if filled else "#dc3545"
            rows += (
                f"<tr>"
                f"<td style='padding:3px 8px;color:{colour};"
                f"font-weight:600;'>{icon}</td>"
                f"<td style='padding:3px 8px;font-size:0.85em;'>{label}</td>"
                f"</tr>"
            )
            if not filled:
                all_filled = False

        border_colour = "#28a745" if all_filled else "#fd7e14"
        status_text   = (
            "All content fields filled."
            if all_filled
            else "Some fields are missing — click to edit."
        )

        html = f"""
        <div style="border-left:4px solid {border_colour};
                    padding:8px 12px;background:#f8f9fa;
                    border-radius:0 4px 4px 0;">
            <p style="margin:0 0 6px;font-size:0.8em;
                      color:{border_colour};font-weight:600;">
                {status_text}
            </p>
            <table style="border-collapse:collapse;">
                {rows}
            </table>
        </div>
        """
        return format_html(html)
    content_summary.short_description = "Content Health"

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("stage")
        )

    def has_delete_permission(self, request, obj=None):
        # Prevent accidental deletion of content that
        # students may have already attempted
        if obj and obj.pk:
            has_attempts = WritingAttempt.objects.filter(
                content=obj
            ).exists()
            if has_attempts:
                return False
        return True


# ============================================================
# 2. WRITING ATTEMPT INLINE
#    Appears inside WritingStageContent admin (change view).
#    Read-only — shows student submissions for teacher review.
#    Teacher-evaluated and AI+Teacher stages show a Review button.
# ============================================================

class WritingAttemptInline(admin.TabularInline):
    """
    Read-only inline for student attempts.
    Shown inside WritingStageContent change view.
    Teacher can see pending submissions at a glance.
    """
    model       = WritingAttempt
    extra       = 0
    can_delete  = False
    ordering    = ("-created_at",)
    show_change_link = True

    fields = (
        "user_link",
        "phase",
        "attempt_number",
        "status_badge",
        "effective_score_display",
        "created_at",
        "review_link",
    )
    readonly_fields = (
        "user_link",
        "phase",
        "attempt_number",
        "status_badge",
        "effective_score_display",
        "created_at",
        "review_link",
    )

    def user_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a>', url, obj.user.username
        )
    user_link.short_description = "Student"

    def status_badge(self, obj):
        colours = {
            "pending":       "#fd7e14",
            "passed":        "#28a745",
            "failed":        "#dc3545",
            "cooldown":      "#6c757d",
            "approved":      "#007bff",
            "needs_revision": "#ffc107",
        }
        colour = colours.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:9999px;font-size:0.75em;font-weight:600;">'
            '{}</span>',
            colour,
            obj.get_status_display(),
        )
    status_badge.short_description = "Status"

    def effective_score_display(self, obj):
        score = obj.effective_score()
        colour = (
            "#28a745" if score >= 70
            else "#fd7e14" if score >= 40
            else "#dc3545"
        )
        return format_html(
            '<span style="color:{};font-weight:600;">{}%</span>',
            colour, score
        )
    effective_score_display.short_description = "Score"

    def review_link(self, obj):
        """
        Show a Review link for teacher/AI+Teacher attempts
        that are pending or need revision.
        """
        eval_method = obj.content.stage.eval_method
        needs_review = (
            eval_method in (EVAL_TEACHER, EVAL_AI_TEACHER)
            and obj.phase == PHASE_PRODUCE
            and obj.status in (STATUS_PENDING, STATUS_REVISION)
        )
        if needs_review:
            url = reverse(
                "admin:content_writingattempt_change",
                args=[obj.id]
            )
            return format_html(
                '<a href="{}" style="color:#dc3545;font-weight:600;">'
                '⚑ Review</a>',
                url
            )
        return "—"
    review_link.short_description = "Action"

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("user", "content__stage")
            .order_by("-created_at")
        )


# ============================================================
# 3. WRITING INTERVENTION INLINE
#    Appears inside WritingAttempt admin (change view).
#    Shows sentence-level flags generated during evaluation.
#    Read-only — interventions are system-generated.
# ============================================================

class WritingInterventionInline(admin.TabularInline):
    """
    Read-only inline for sentence-level interventions.
    Shown inside WritingAttempt change view.
    """
    model      = WritingIntervention
    extra      = 0
    can_delete = False
    ordering   = ("id",)

    fields = (
        "sentence_preview",
        "issue_label",
        "is_resolved",
        "resolved_at",
    )
    readonly_fields = (
        "sentence_preview",
        "issue_label",
        "is_resolved",
        "resolved_at",
    )

    def sentence_preview(self, obj):
        text = obj.sentence_text or ""
        preview = text[:80] + "…" if len(text) > 80 else text
        return format_html(
            '<span style="font-style:italic;color:#495057;">'
            '"{}"</span>',
            preview
        )
    sentence_preview.short_description = "Sentence"

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("attempt")
        )


# ============================================================
# 4. WRITING STAGE MASTERY INLINE
#    Appears inside WritingStageContent admin (change view).
#    Read-only — shows which students have mastered this stage.
# ============================================================

class WritingStageMasteryInline(admin.TabularInline):
    """
    Read-only inline showing mastery records for a stage.
    Shown inside WritingStageContent change view.
    """
    model      = WritingStageMastery
    extra      = 0
    can_delete = False
    ordering   = ("mastered_at",)

    fields = (
        "user_link",
        "academic_year",
        "mastered_via",
        "mastered_at",
    )
    readonly_fields = (
        "user_link",
        "academic_year",
        "mastered_via",
        "mastered_at",
    )

    def user_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a>', url, obj.user.username
        )
    user_link.short_description = "Student"

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("user", "academic_year")
        )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "WritingStageContentInline",
    "WritingAttemptInline",
    "WritingInterventionInline",
    "WritingStageMasteryInline",
]