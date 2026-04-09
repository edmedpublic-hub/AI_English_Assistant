# content/admin/writing.py
#
# Complete replacement of the previous writing admin.
# Covers all new writing models:
#   WritingAcademicYear      — system setting, admin sets once per year
#   WritingStage             — 16 stages, seeded via migration, mostly read-only
#   WritingStageContent      — admin enters content per stage per unit
#   WritingAttempt           — student submissions, teacher review queue
#   WritingStageMastery      — mastery records, read-only
#   WritingIntervention      — sentence-level flags, read-only
#
# Teacher review workflow is the centrepiece of this admin.
# A teacher can open a pending Produce submission, read the
# student's writing, and Approve / Request Revision in one screen.

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db import models as db_models

from content.models.writing import (
    WritingAcademicYear,
    WritingStage,
    WritingStageContent,
    WritingAttempt,
    WritingStageMastery,
    WritingIntervention,
    EVAL_TEACHER,
    EVAL_AI_TEACHER,
    EVAL_AUTOMATIC,
    EVAL_KEYWORD,
    PHASE_PRODUCE,
    STATUS_PENDING,
    STATUS_APPROVED,
    STATUS_REVISION,
    STATUS_PASSED,
    STATUS_FAILED,
)

from content.admin.inlines.writing import (
    WritingAttemptInline,
    WritingInterventionInline,
    WritingStageMasteryInline,
)


# ============================================================
# 1. WRITING ACADEMIC YEAR ADMIN
# ============================================================

@admin.register(WritingAcademicYear)
class WritingAcademicYearAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "start_date",
        "is_current_badge",
        "attempt_count",
        "mastery_count",
    )
    list_filter  = ("is_current",)
    ordering     = ("-start_date",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "year_stats",
    )

    fieldsets = (
        ("Academic Year", {
            "fields": ("label", "start_date", "is_current"),
            "description": (
                "Set exactly one academic year as current. "
                "All writing mastery is scoped to the current year. "
                "When a new year starts, mark the new year as current — "
                "previous year records are preserved but inactive."
            ),
        }),
        ("Statistics", {
            "fields": ("year_stats",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ── list columns ──────────────────────────────────────

    def is_current_badge(self, obj):
        if obj.is_current:
            return format_html(
                '<span style="background:#28a745;color:#fff;'
                'padding:2px 10px;border-radius:9999px;'
                'font-size:0.8em;font-weight:600;">✓ Current</span>'
            )
        return format_html(
            '<span style="color:#6c757d;font-size:0.85em;">Past</span>'
        )
    is_current_badge.short_description = "Status"

    def attempt_count(self, obj):
        count = WritingAttempt.objects.filter(
            academic_year=obj
        ).count()
        return format_html(
            '<span style="font-weight:600;">{}</span>', count
        )
    attempt_count.short_description = "Attempts"

    def mastery_count(self, obj):
        count = WritingStageMastery.objects.filter(
            academic_year=obj
        ).count()
        return format_html(
            '<span style="color:#28a745;font-weight:600;">{}</span>',
            count
        )
    mastery_count.short_description = "Masteries"

    # ── change form ───────────────────────────────────────

    def year_stats(self, obj):
        if not obj.pk:
            return "Save first."

        attempts  = WritingAttempt.objects.filter(academic_year=obj)
        masteries = WritingStageMastery.objects.filter(academic_year=obj)

        total_attempts  = attempts.count()
        total_students  = attempts.values("user").distinct().count()
        total_masteries = masteries.count()
        pending_review  = attempts.filter(
            status=STATUS_PENDING,
            phase=PHASE_PRODUCE,
            content__stage__eval_method__in=(EVAL_TEACHER, EVAL_AI_TEACHER)
        ).count()

        pending_colour = "#dc3545" if pending_review > 0 else "#28a745"

        html = f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);
                    gap:12px;max-width:700px;">
            <div style="background:#f8f9fa;padding:12px;border-radius:6px;
                        border-top:3px solid #007bff;text-align:center;">
                <div style="font-size:1.6em;font-weight:700;color:#007bff;">
                    {total_students}
                </div>
                <div style="font-size:0.8em;color:#6c757d;">Students</div>
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:6px;
                        border-top:3px solid #6c757d;text-align:center;">
                <div style="font-size:1.6em;font-weight:700;color:#6c757d;">
                    {total_attempts}
                </div>
                <div style="font-size:0.8em;color:#6c757d;">Attempts</div>
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:6px;
                        border-top:3px solid #28a745;text-align:center;">
                <div style="font-size:1.6em;font-weight:700;color:#28a745;">
                    {total_masteries}
                </div>
                <div style="font-size:0.8em;color:#6c757d;">Masteries</div>
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:6px;
                        border-top:3px solid {pending_colour};text-align:center;">
                <div style="font-size:1.6em;font-weight:700;
                            color:{pending_colour};">
                    {pending_review}
                </div>
                <div style="font-size:0.8em;color:#6c757d;">Pending Review</div>
            </div>
        </div>
        """
        return format_html(html)
    year_stats.short_description = "Year Overview"


# ============================================================
# 2. WRITING STAGE ADMIN
#    16 stages — seeded via migration.
#    Admin can read and edit descriptions and word counts.
#    Cannot add or delete stages.
# ============================================================

@admin.register(WritingStage)
class WritingStageAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "name",
        "tier_badge",
        "eval_badge",
        "word_counts_display",
        "content_coverage",
    )
    list_filter  = ("tier", "eval_method")
    ordering     = ("number",)
    search_fields = ("name", "description")
    readonly_fields = (
        "number",
        "created_at",
        "updated_at",
        "content_coverage_detail",
    )

    fieldsets = (
        ("Stage Identity", {
            "fields": ("number", "name", "tier", "eval_method", "description"),
            "description": (
                "Stage number and tier are set by the system. "
                "Edit the description to update what students see."
            ),
        }),
        ("Minimum Word Counts by Class Level", {
            "fields": (
                "min_words_class_9",
                "min_words_class_10",
                "min_words_class_11",
                "min_words_class_12",
            ),
            "description": (
                "These are defaults. "
                "Individual unit content can override these."
            ),
        }),
        ("Content Coverage", {
            "fields": ("content_coverage_detail",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ── list columns ──────────────────────────────────────

    def tier_badge(self, obj):
        colours = {
            "sentence":  "#007bff",
            "paragraph": "#fd7e14",
            "genre":     "#6f42c1",
        }
        colour = colours.get(obj.tier, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:9999px;font-size:0.75em;font-weight:600;">'
            '{}</span>',
            colour,
            obj.get_tier_display(),
        )
    tier_badge.short_description = "Tier"

    def eval_badge(self, obj):
        colours = {
            "automatic":  "#28a745",
            "keyword":    "#17a2b8",
            "teacher":    "#fd7e14",
            "ai_teacher": "#6f42c1",
        }
        colour = colours.get(obj.eval_method, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:9999px;font-size:0.75em;font-weight:600;">'
            '{}</span>',
            colour,
            obj.get_eval_method_display(),
        )
    eval_badge.short_description = "Evaluation"

    def word_counts_display(self, obj):
        return format_html(
            '<span style="font-size:0.85em;color:#495057;">'
            '9:{} · 10:{} · 11:{} · 12:{}'
            '</span>',
            obj.min_words_class_9,
            obj.min_words_class_10,
            obj.min_words_class_11,
            obj.min_words_class_12,
        )
    word_counts_display.short_description = "Min Words (9/10/11/12)"

    def content_coverage(self, obj):
        total    = obj.stage_contents.count()
        complete = obj.stage_contents.filter(is_complete=True).count()
        if total == 0:
            return format_html(
                '<span style="color:#dc3545;">No content yet</span>'
            )
        colour = "#28a745" if complete == total else "#fd7e14"
        return format_html(
            '<span style="color:{};font-weight:600;">{}/{}</span>',
            colour, complete, total
        )
    content_coverage.short_description = "Content (complete/total)"

    def content_coverage_detail(self, obj):
        if not obj.pk:
            return "Save first."
        contents = (
            obj.stage_contents
            .select_related("unit__textbook")
            .order_by("unit__textbook__class_level", "unit__number")
        )
        if not contents.exists():
            return "No content records yet for this stage."

        rows = ""
        for c in contents:
            status_colour = "#28a745" if c.is_complete else "#fd7e14"
            status_label  = "Complete" if c.is_complete else "Incomplete"
            url = reverse(
                "admin:content_writingstagecontent_change",
                args=[c.id]
            )
            rows += (
                f"<tr style='border-bottom:1px solid #dee2e6;'>"
                f"<td style='padding:4px 8px;font-size:0.85em;'>"
                f"{c.unit.textbook.class_level}</td>"
                f"<td style='padding:4px 8px;font-size:0.85em;'>"
                f"<a href='{url}'>Unit {c.unit.number}: "
                f"{c.unit.title}</a></td>"
                f"<td style='padding:4px 8px;'>"
                f"<span style='color:{status_colour};"
                f"font-size:0.8em;font-weight:600;'>"
                f"{status_label}</span></td>"
                f"</tr>"
            )

        html = f"""
        <table style="border-collapse:collapse;width:100%;">
            <thead>
                <tr style="background:#e9ecef;">
                    <th style="padding:4px 8px;text-align:left;
                               font-size:0.8em;">Class</th>
                    <th style="padding:4px 8px;text-align:left;
                               font-size:0.8em;">Unit</th>
                    <th style="padding:4px 8px;text-align:left;
                               font-size:0.8em;">Status</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """
        return format_html(html)
    content_coverage_detail.short_description = "Content per Unit"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# 3. WRITING STAGE CONTENT ADMIN
#    The main content authoring surface.
#    Admin enters all three phases of content here.
# ============================================================

@admin.register(WritingStageContent)
class WritingStageContentAdmin(admin.ModelAdmin):
    list_display = (
        "stage_number",
        "stage_name",
        "unit_link",
        "class_level",
        "is_complete_badge",
        "attempt_count",
        "mastery_count",
        "pending_review_count",
    )
    list_filter  = (
        "stage__tier",
        "stage__eval_method",
        "is_complete",
        "unit__textbook",
    )
    search_fields = (
        "stage__name",
        "unit__title",
        "unit__textbook__title",
        "produce_prompt",
    )
    ordering     = ("unit__textbook__class_level", "unit__number", "stage__number")
    autocomplete_fields = ("unit",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "class_level_display",
        "eval_method_display",
        "mastery_stats",
        "pending_review_panel",
    )

    fieldsets = (
        ("Stage & Unit", {
            "fields": (
                "stage",
                "unit",
                "class_level_display",
                "eval_method_display",
                "is_complete",
            ),
        }),
        ("Dissect Phase — Model Sentences", {
            "fields": (
                "model_sentence_original",
                "model_sentence_converted",
                "conversion_note",
                "dissect_question",
                "dissect_answer",
            ),
            "description": (
                "Show the student a model sentence from the unit text. "
                "Provide a converted version alongside it. "
                "The student studies the difference, "
                "then answers the dissect question."
            ),
        }),
        ("Imitate Phase — Sentence Frame", {
            "fields": (
                "imitate_frame",
                "imitate_instruction",
            ),
            "description": (
                "Provide a frame the student fills with their own words. "
                "Use ___ for blanks. "
                "Example: ___ walked slowly toward ___."
            ),
        }),
        ("Produce Phase — Writing Prompt", {
            "fields": (
                "produce_prompt",
                "produce_instruction",
                "min_word_count",
            ),
            "description": (
                "No frame is given. Student writes independently. "
                "Prompt should relate directly to unit content."
            ),
        }),
        ("Evaluation — Keywords & AI Rubric", {
            "fields": (
                "required_keywords",
                "ai_rubric",
            ),
            "classes": ("collapse",),
            "description": (
                "Required keywords: for keyword-evaluated stages only. "
                "AI rubric: for AI+Teacher evaluated stages only."
            ),
        }),
        ("Pending Teacher Review", {
            "fields": ("pending_review_panel",),
            "description": (
                "Student submissions waiting for your review."
            ),
        }),
        ("Mastery Statistics", {
            "fields": ("mastery_stats",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    inlines = [WritingAttemptInline, WritingStageMasteryInline]

    # ── list columns ──────────────────────────────────────

    def stage_number(self, obj):
        return format_html(
            '<span style="font-weight:700;color:#495057;">'
            'Stage {}</span>',
            obj.stage.number
        )
    stage_number.short_description = "#"
    stage_number.admin_order_field = "stage__number"

    def stage_name(self, obj):
        return obj.stage.name
    stage_name.short_description = "Stage"
    stage_name.admin_order_field = "stage__name"

    def unit_link(self, obj):
        url = reverse("admin:content_unit_change", args=[obj.unit.id])
        return format_html(
            '<a href="{}">Unit {}: {}</a>',
            url,
            obj.unit.number,
            obj.unit.title,
        )
    unit_link.short_description = "Unit"

    def class_level(self, obj):
        return obj.unit.textbook.class_level
    class_level.short_description = "Class"
    class_level.admin_order_field = "unit__textbook__class_level"

    def is_complete_badge(self, obj):
        if obj.is_complete:
            return format_html(
                '<span style="background:#28a745;color:#fff;'
                'padding:2px 10px;border-radius:9999px;'
                'font-size:0.8em;font-weight:600;">✓ Ready</span>'
            )
        return format_html(
            '<span style="background:#fd7e14;color:#fff;'
            'padding:2px 10px;border-radius:9999px;'
            'font-size:0.8em;font-weight:600;">~ Incomplete</span>'
        )
    is_complete_badge.short_description = "Status"

    def attempt_count(self, obj):
        count = WritingAttempt.objects.filter(content=obj).count()
        return format_html(
            '<span style="font-weight:600;">{}</span>', count
        )
    attempt_count.short_description = "Attempts"

    def mastery_count(self, obj):
        count = WritingStageMastery.objects.filter(content=obj).count()
        colour = "#28a745" if count > 0 else "#6c757d"
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            colour, count
        )
    mastery_count.short_description = "Masteries"

    def pending_review_count(self, obj):
        count = WritingAttempt.objects.filter(
            content=obj,
            phase=PHASE_PRODUCE,
            status=STATUS_PENDING,
            content__stage__eval_method__in=(EVAL_TEACHER, EVAL_AI_TEACHER),
        ).count()
        if count == 0:
            return "—"
        return format_html(
            '<span style="background:#dc3545;color:#fff;'
            'padding:2px 8px;border-radius:9999px;'
            'font-size:0.8em;font-weight:600;">⚑ {}</span>',
            count
        )
    pending_review_count.short_description = "Pending"

    # ── change form panels ────────────────────────────────

    def class_level_display(self, obj):
        if not obj.pk:
            return "—"
        return format_html(
            '<strong>{}</strong> — {}',
            obj.unit.textbook.class_level,
            obj.unit.textbook.title,
        )
    class_level_display.short_description = "Class Level"

    def eval_method_display(self, obj):
        if not obj.pk:
            return "—"
        colours = {
            "automatic":  "#28a745",
            "keyword":    "#17a2b8",
            "teacher":    "#fd7e14",
            "ai_teacher": "#6f42c1",
        }
        colour = colours.get(obj.stage.eval_method, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 12px;'
            'border-radius:9999px;font-weight:600;">{}</span>',
            colour,
            obj.stage.get_eval_method_display(),
        )
    eval_method_display.short_description = "Evaluation Method"

    def pending_review_panel(self, obj):
        if not obj.pk:
            return "Save first."

        pending = WritingAttempt.objects.filter(
            content=obj,
            phase=PHASE_PRODUCE,
            status=STATUS_PENDING,
        ).select_related("user").order_by("created_at")

        if not pending.exists():
            return format_html(
                '<span style="color:#28a745;">✓ No pending submissions.</span>'
            )

        rows = ""
        for attempt in pending:
            url = reverse(
                "admin:content_writingattempt_change",
                args=[attempt.id]
            )
            rows += (
                f"<tr style='border-bottom:1px solid #dee2e6;'>"
                f"<td style='padding:6px 8px;'>"
                f"<strong>{attempt.user.username}</strong></td>"
                f"<td style='padding:6px 8px;font-size:0.85em;"
                f"color:#6c757d;'>"
                f"{attempt.created_at.strftime('%d %b %Y, %H:%M')}</td>"
                f"<td style='padding:6px 8px;'>"
                f"<a href='{url}' style='color:#dc3545;"
                f"font-weight:600;'>⚑ Review</a></td>"
                f"</tr>"
            )

        html = f"""
        <div style="border:1px solid #dee2e6;border-radius:6px;
                    overflow:hidden;">
            <div style="background:#dc3545;color:#fff;
                        padding:6px 12px;font-weight:600;
                        font-size:0.85em;">
                {pending.count()} submission(s) waiting for review
            </div>
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="background:#f8f9fa;">
                        <th style="padding:6px 8px;text-align:left;
                                   font-size:0.8em;">Student</th>
                        <th style="padding:6px 8px;text-align:left;
                                   font-size:0.8em;">Submitted</th>
                        <th style="padding:6px 8px;text-align:left;
                                   font-size:0.8em;">Action</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """
        return format_html(html)
    pending_review_panel.short_description = "Pending Review"

    def mastery_stats(self, obj):
        if not obj.pk:
            return "Save first."

        attempts  = WritingAttempt.objects.filter(content=obj)
        masteries = WritingStageMastery.objects.filter(content=obj)

        if not attempts.exists():
            return "No attempts yet."

        total_students  = attempts.values("user").distinct().count()
        total_attempts  = attempts.count()
        total_masteries = masteries.count()

        by_phase = {}
        for phase in ("dissect", "imitate", "produce"):
            by_phase[phase] = attempts.filter(phase=phase).count()

        html = f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;
                    gap:12px;max-width:500px;">
            <div style="background:#f8f9fa;padding:12px;
                        border-radius:6px;
                        border-left:4px solid #007bff;">
                <p style="font-weight:700;margin:0 0 8px;
                           color:#007bff;">Attempts</p>
                <table style="width:100%;font-size:0.9em;">
                    <tr><td>Students</td>
                        <td><b>{total_students}</b></td></tr>
                    <tr><td>Total attempts</td>
                        <td><b>{total_attempts}</b></td></tr>
                    <tr><td>Dissect attempts</td>
                        <td><b>{by_phase['dissect']}</b></td></tr>
                    <tr><td>Imitate attempts</td>
                        <td><b>{by_phase['imitate']}</b></td></tr>
                    <tr><td>Produce attempts</td>
                        <td><b>{by_phase['produce']}</b></td></tr>
                </table>
            </div>
            <div style="background:#f8f9fa;padding:12px;
                        border-radius:6px;
                        border-left:4px solid #28a745;">
                <p style="font-weight:700;margin:0 0 8px;
                           color:#28a745;">Mastery</p>
                <table style="width:100%;font-size:0.9em;">
                    <tr><td>Students mastered</td>
                        <td><b style="color:#28a745;">
                        {total_masteries}</b></td></tr>
                    <tr><td>Mastery rate</td>
                        <td><b>{
                            int((total_masteries/total_students)*100)
                            if total_students else 0
                        }%</b></td></tr>
                </table>
            </div>
        </div>
        """
        return format_html(html)
    mastery_stats.short_description = "Statistics"

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related(
                "stage",
                "unit",
                "unit__textbook",
            )
        )


# ============================================================
# 4. WRITING ATTEMPT ADMIN
#    The teacher review screen.
#    Teacher opens a pending submission, reads the writing,
#    and clicks Approve or Request Revision.
#    Custom actions handle the approval workflow.
# ============================================================

@admin.register(WritingAttempt)
class WritingAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "stage_display",
        "phase_badge",
        "status_badge",
        "effective_score_display",
        "created_at",
        "review_action",
    )
    list_filter  = (
        "status",
        "phase",
        "content__stage__tier",
        "content__stage__eval_method",
        "academic_year",
        "created_at",
    )
    search_fields = (
        "user__username",
        "content__stage__name",
        "content__unit__title",
        "response_text",
    )
    ordering     = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = (
        "user",
        "content",
        "academic_year",
        "phase",
        "attempt_number",
        "created_at",
        "updated_at",
        "auto_checks_display",
        "intervention_summary",
        "response_display",
        "ai_feedback_display",
        "cooldown_display",
    )

    fieldsets = (
        ("Student & Stage", {
            "fields": (
                "user",
                "content",
                "academic_year",
                "phase",
                "attempt_number",
                "created_at",
            ),
        }),
        ("Student's Writing", {
            "fields": ("response_display",),
            "description": (
                "Read the student's writing carefully before reviewing."
            ),
        }),
        ("Automatic Evaluation Results", {
            "fields": (
                "auto_checks_display",
                "auto_score",
                "intervention_summary",
            ),
            "classes": ("collapse",),
        }),
        ("AI Evaluation", {
            "fields": (
                "ai_feedback_display",
                "ai_score",
                "ai_rubric_scores",
            ),
            "classes": ("collapse",),
        }),
        ("Teacher Review", {
            "fields": (
                "status",
                "teacher_score",
                "teacher_feedback",
            ),
            "description": (
                "Set status to Approved to grant mastery. "
                "Set to Needs Revision to send back with feedback. "
                "Your feedback is shown directly to the student."
            ),
        }),
        ("Cooldown", {
            "fields": ("cooldown_display", "next_attempt_allowed_at"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("updated_at",),
            "classes": ("collapse",),
        }),
    )

    inlines = [WritingInterventionInline]

    # ── list columns ──────────────────────────────────────

    def student_name(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a>', url, obj.user.username
        )
    student_name.short_description = "Student"

    def stage_display(self, obj):
        return format_html(
            'Stage {} · {} · Unit {}',
            obj.content.stage.number,
            obj.content.stage.name,
            obj.content.unit.number,
        )
    stage_display.short_description = "Stage"

    def phase_badge(self, obj):
        colours = {
            "dissect": "#17a2b8",
            "imitate": "#fd7e14",
            "produce": "#6f42c1",
        }
        colour = colours.get(obj.phase, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:9999px;font-size:0.75em;font-weight:600;">'
            '{}</span>',
            colour,
            obj.get_phase_display(),
        )
    phase_badge.short_description = "Phase"

    def status_badge(self, obj):
        colours = {
            "pending":        "#fd7e14",
            "passed":         "#28a745",
            "failed":         "#dc3545",
            "cooldown":       "#6c757d",
            "approved":       "#007bff",
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
        score  = obj.effective_score()
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

    def review_action(self, obj):
        if (
            obj.phase == PHASE_PRODUCE
            and obj.status == STATUS_PENDING
            and obj.content.stage.eval_method in (EVAL_TEACHER, EVAL_AI_TEACHER)
        ):
            url = reverse(
                "admin:content_writingattempt_change",
                args=[obj.id]
            )
            return format_html(
                '<a href="{}" style="background:#dc3545;color:#fff;'
                'padding:3px 10px;border-radius:4px;font-size:0.8em;'
                'font-weight:600;text-decoration:none;">⚑ Review</a>',
                url
            )
        return "—"
    review_action.short_description = "Action"

    # ── change form panels ────────────────────────────────

    def response_display(self, obj):
        if not obj.response_text:
            return "No response recorded."
        return format_html(
            '<div style="background:#fff;border:1px solid #dee2e6;'
            'border-radius:6px;padding:16px;font-size:1em;'
            'line-height:1.7;max-width:700px;white-space:pre-wrap;">'
            '{}</div>',
            obj.response_text,
        )
    response_display.short_description = "Student's Writing"

    def auto_checks_display(self, obj):
        if not obj.auto_checks:
            return "No automatic checks recorded."

        checks = obj.auto_checks
        rows   = ""
        for key, value in checks.items():
            if isinstance(value, bool):
                icon   = "✓" if value else "✗"
                colour = "#28a745" if value else "#dc3545"
                label  = key.replace("_", " ").title()
                rows += (
                    f"<tr>"
                    f"<td style='padding:3px 8px;color:{colour};"
                    f"font-weight:600;'>{icon}</td>"
                    f"<td style='padding:3px 8px;font-size:0.85em;'>"
                    f"{label}</td>"
                    f"</tr>"
                )
            elif isinstance(value, list) and value:
                label = key.replace("_", " ").title()
                rows += (
                    f"<tr>"
                    f"<td style='padding:3px 8px;'></td>"
                    f"<td style='padding:3px 8px;font-size:0.85em;"
                    f"color:#495057;'>{label}: "
                    f"{', '.join(str(v) for v in value)}</td>"
                    f"</tr>"
                )

        return format_html(
            '<table style="border-collapse:collapse;">{}</table>',
            rows
        )
    auto_checks_display.short_description = "Automatic Checks"

    def ai_feedback_display(self, obj):
        if not obj.ai_feedback:
            return "No AI feedback recorded."
        return format_html(
            '<div style="background:#f8f9fa;border-left:4px solid #6f42c1;'
            'padding:12px 16px;border-radius:0 6px 6px 0;'
            'font-size:0.9em;line-height:1.6;max-width:700px;">'
            '{}</div>',
            obj.ai_feedback,
        )
    ai_feedback_display.short_description = "AI Feedback"

    def intervention_summary(self, obj):
        interventions = obj.interventions.all()
        if not interventions.exists():
            return "No sentence-level interventions."

        total    = interventions.count()
        resolved = interventions.filter(is_resolved=True).count()
        colour   = "#28a745" if resolved == total else "#fd7e14"

        rows = ""
        for iv in interventions:
            status = (
                '<span style="color:#28a745;">✓ Resolved</span>'
                if iv.is_resolved
                else '<span style="color:#dc3545;">✗ Pending</span>'
            )
            rows += (
                f"<tr style='border-bottom:1px solid #dee2e6;'>"
                f"<td style='padding:4px 8px;font-style:italic;"
                f"font-size:0.85em;color:#495057;'>"
                f'"{iv.sentence_text[:60]}"</td>'
                f"<td style='padding:4px 8px;font-size:0.85em;'>"
                f"{iv.issue_label}</td>"
                f"<td style='padding:4px 8px;'>{status}</td>"
                f"</tr>"
            )

        html = f"""
        <div style="border:1px solid #dee2e6;border-radius:6px;
                    overflow:hidden;">
            <div style="background:{colour};color:#fff;
                        padding:6px 12px;font-weight:600;
                        font-size:0.85em;">
                {resolved}/{total} interventions resolved
            </div>
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="background:#f8f9fa;">
                        <th style="padding:4px 8px;text-align:left;
                                   font-size:0.8em;">Sentence</th>
                        <th style="padding:4px 8px;text-align:left;
                                   font-size:0.8em;">Issue</th>
                        <th style="padding:4px 8px;text-align:left;
                                   font-size:0.8em;">Status</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """
        return format_html(html)
    intervention_summary.short_description = "Sentence Interventions"

    def cooldown_display(self, obj):
        if not obj.next_attempt_allowed_at:
            return "No cooldown active."
        if obj.is_in_cooldown():
            remaining = obj.cooldown_remaining()
            hours     = int(remaining.total_seconds() // 3600)
            minutes   = int((remaining.total_seconds() % 3600) // 60)
            return format_html(
                '<span style="color:#fd7e14;font-weight:600;">'
                'In cooldown — {} hours {} minutes remaining</span>',
                hours, minutes,
            )
        return format_html(
            '<span style="color:#28a745;">Cooldown complete.</span>'
        )
    cooldown_display.short_description = "Cooldown Status"

    def save_model(self, request, obj, form, change):
        """
        On save, if teacher has set status to Approved or Needs Revision:
        - Record who reviewed and when
        - If Approved, create WritingStageMastery record
        """
        if change and obj.status in (STATUS_APPROVED, STATUS_REVISION):
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()

        super().save_model(request, obj, form, change)

        # Grant mastery on approval
        if obj.status == STATUS_APPROVED and obj.phase == PHASE_PRODUCE:
            WritingStageMastery.objects.get_or_create(
                user=obj.user,
                content=obj.content,
                academic_year=obj.academic_year,
                defaults={
                    "mastered_at":      timezone.now(),
                    "mastered_via":     obj.content.stage.eval_method,
                    "mastery_attempt":  obj,
                },
            )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related(
                "user",
                "content__stage",
                "content__unit",
                "academic_year",
                "reviewed_by",
            )
        )


# ============================================================
# 5. WRITING STAGE MASTERY ADMIN  — read-only record
# ============================================================

@admin.register(WritingStageMastery)
class WritingStageMasteryAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "stage_display",
        "academic_year",
        "mastered_via_badge",
        "mastered_at",
    )
    list_filter  = (
        "academic_year",
        "mastered_via",
        "content__stage__tier",
    )
    search_fields = (
        "user__username",
        "content__stage__name",
        "content__unit__title",
    )
    ordering     = ("-mastered_at",)
    date_hierarchy = "mastered_at"
    readonly_fields = [
        f.name for f in WritingStageMastery._meta.fields
    ]

    def student_name(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a>', url, obj.user.username
        )
    student_name.short_description = "Student"

    def stage_display(self, obj):
        return format_html(
            'Stage {} · {} · Unit {} · {}',
            obj.content.stage.number,
            obj.content.stage.name,
            obj.content.unit.number,
            obj.content.unit.textbook.class_level,
        )
    stage_display.short_description = "Stage"

    def mastered_via_badge(self, obj):
        colours = {
            "automatic":  "#28a745",
            "keyword":    "#17a2b8",
            "teacher":    "#fd7e14",
            "ai_teacher": "#6f42c1",
        }
        colour = colours.get(obj.mastered_via, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:9999px;font-size:0.75em;font-weight:600;">'
            '{}</span>',
            colour,
            obj.get_mastered_via_display(),
        )
    mastered_via_badge.short_description = "Via"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related(
                "user",
                "content__stage",
                "content__unit__textbook",
                "academic_year",
            )
        )


# ============================================================
# 6. WRITING INTERVENTION ADMIN  — read-only record
# ============================================================

@admin.register(WritingIntervention)
class WritingInterventionAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "sentence_preview",
        "issue_label",
        "is_resolved_badge",
        "created_at",
    )
    list_filter  = ("is_resolved", "created_at")
    search_fields = (
        "attempt__user__username",
        "sentence_text",
        "issue_label",
    )
    ordering     = ("-created_at",)
    readonly_fields = [
        f.name for f in WritingIntervention._meta.fields
    ]

    def student_name(self, obj):
        url = reverse(
            "admin:auth_user_change",
            args=[obj.attempt.user.id]
        )
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.attempt.user.username,
        )
    student_name.short_description = "Student"

    def sentence_preview(self, obj):
        text = obj.sentence_text or ""
        preview = text[:60] + "…" if len(text) > 60 else text
        return format_html(
            '<span style="font-style:italic;">"{}"</span>', preview
        )
    sentence_preview.short_description = "Sentence"

    def is_resolved_badge(self, obj):
        if obj.is_resolved:
            return format_html(
                '<span style="color:#28a745;font-weight:600;">'
                '✓ Resolved</span>'
            )
        return format_html(
            '<span style="color:#dc3545;font-weight:600;">'
            '✗ Pending</span>'
        )
    is_resolved_badge.short_description = "Resolved"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("attempt__user", "attempt__content__stage")
        )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "WritingAcademicYearAdmin",
    "WritingStageAdmin",
    "WritingStageContentAdmin",
    "WritingAttemptAdmin",
    "WritingStageMasteryAdmin",
    "WritingInterventionAdmin",
]