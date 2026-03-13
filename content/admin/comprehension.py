# PATH: content/admin/comprehension.py
# ACTION: Replace the entire existing file with this content.
# CHANGES FROM ORIGINAL:
#   - ChunkComprehensionFocusAdmin:
#       • list_display: added completeness_badge column
#       • fieldsets: replaced question_count_display with content_health panel
#         (shows live question table with type/difficulty, matching punctuation pattern)
#       • mastery_stats_display: added practice vs test side-by-side layout
#       • get_queryset: added select_related for performance
#   - mastery_stats_display: fixed format_html(f-string) unsafe pattern
#   - All other admins: UNCHANGED.

from django.contrib import admin
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db import models
from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionQuestion,
    ComprehensionPracticeAttempt,
    ComprehensionTestAttempt,
    ComprehensionQuestionAttempt,
)
from content.admin.inlines.comprehension import ComprehensionQuestionInline


# ═══════════════════════════════════════════════════════════════
#  CHUNK COMPREHENSION FOCUS ADMIN  ★ main domain editor
# ═══════════════════════════════════════════════════════════════

@admin.register(ChunkComprehensionFocus)
class ChunkComprehensionFocusAdmin(admin.ModelAdmin):

    list_display = (
        "focus_title",
        "chunk_link",
        "level_badge",          # NEW: coloured Bloom's level pill
        "depth_level",
        "sequence_order",
        "completeness_badge",   # NEW: Ready / Partial / Empty
        "mastery_rate",
    )
    list_filter = ("level", "depth_level", "chunk__lesson__unit__textbook")
    search_fields = ("focus_title", "focus_description", "chunk__english_text")
    ordering = ("chunk", "sequence_order")
    autocomplete_fields = ("chunk",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "content_health",           # NEW: replaces question_count_display
        "mastery_stats_display",
    )

    fieldsets = (
        ("Comprehension Focus", {
            "fields": ("chunk", "focus_title", "focus_description"),
        }),
        ("Bloom's Taxonomy", {
            "fields": ("level", "depth_level", "sequence_order"),
            "description": (
                "Literal → sequence 1 | Inferential → sequence 2 | "
                "Evaluative → sequence 3. The system enforces this order."
            ),
        }),
        ("Content Health — Questions", {
            "fields": ("content_health",),
            "description": "Questions are added via the section below.",
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

    inlines = [ComprehensionQuestionInline]

    # ── list columns ──────────────────────────────────────────

    def chunk_link(self, obj):
        url = reverse('admin:content_lessonchunk_change', args=[obj.chunk.id])
        return format_html('<a href="{}">{}</a>', url, obj.chunk)
    chunk_link.short_description = "Chunk"

    def level_badge(self, obj):
        colours = {
            'literal':     '#28a745',
            'inferential': '#fd7e14',
            'evaluative':  '#dc3545',
        }
        colour = colours.get(obj.level, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:9999px;font-size:0.8em;font-weight:600;">{}</span>',
            colour, obj.get_level_display(),
        )
    level_badge.short_description = "Level"
    level_badge.admin_order_field = "level"

    def completeness_badge(self, obj):
        q = obj.questions.count()
        if q >= 3:
            colour, label = "#28a745", "✓ Ready"
        elif q >= 1:
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
            ComprehensionTestAttempt.objects
            .filter(focus=obj)
            .values('user').distinct().count()
        )
        if total == 0:
            return format_html('<span style="color:gray;">No data</span>')
        mastered = (
            ComprehensionTestAttempt.objects
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

    # ── change-form panels ────────────────────────────────────

    def content_health(self, obj):
        if not obj.pk:
            return "Save first."

        questions  = list(obj.questions.order_by('difficulty', 'id'))
        q_count    = len(questions)

        diff_map = {
            1: "★☆☆☆☆", 2: "★★☆☆☆", 3: "★★★☆☆",
            4: "★★★★☆", 5: "★★★★★",
        }

        if questions:
            rows = ""
            for q in questions:
                rows += (
                    f"<tr style='border-bottom:1px solid #dee2e6;'>"
                    f"<td style='padding:4px 8px;'>"
                    f"<code style='font-size:0.8em;'>{escape(q.question_type)}</code></td>"
                    f"<td style='padding:4px 8px;color:#6c757d;font-size:0.85em;'>"
                    f"{diff_map.get(q.difficulty, q.difficulty)}</td>"
                    f"<td style='padding:4px 8px;'>{escape(q.question_text[:70])}</td>"
                    f"</tr>"
                )
            questions_html = (
                "<table style='border-collapse:collapse;width:100%;'>"
                "<thead><tr style='background:#e9ecef;'>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Type</th>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Difficulty</th>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.8em;'>Question</th>"
                f"</tr></thead><tbody>{rows}</tbody></table>"
            )
        else:
            questions_html = (
                "<p style='color:#dc3545;margin:0;'>"
                "✗ No questions yet — add them in the section below.</p>"
            )

        if q_count >= 3:
            status_colour = "#28a745"
            status_text   = f"✓ Ready — {q_count} question{'s' if q_count != 1 else ''}"
        elif q_count >= 1:
            status_colour = "#fd7e14"
            status_text   = f"~ Partial — {q_count} question{'s' if q_count != 1 else ''}, need ≥ 3"
        else:
            status_colour = "#dc3545"
            status_text   = "✗ Empty — add questions below"

        html = (
            f'<div style="border:1px solid #dee2e6;border-radius:6px;overflow:hidden;">'
            f'<div style="background:{status_colour};color:#fff;padding:6px 12px;'
            f'font-weight:600;font-size:0.85em;">{status_text}</div>'
            f'<div style="padding:10px 12px;">'
            f'<p style="font-weight:600;margin:0 0 6px;font-size:0.85em;'
            f'text-transform:uppercase;color:#6c757d;letter-spacing:.05em;">Questions</p>'
            f'{questions_html}'
            f'</div>'
            f'</div>'
        )
        return mark_safe(html)
    content_health.short_description = "Questions"

    def mastery_stats_display(self, obj):
        if not obj.pk:
            return "Save first."

        practice = ComprehensionPracticeAttempt.objects.filter(focus=obj)
        tests    = ComprehensionTestAttempt.objects.filter(focus=obj)

        if not practice.exists() and not tests.exists():
            return "No attempts yet."

        p_students = practice.values('user').distinct().count()
        p_passed   = practice.filter(is_passed=True).values('user').distinct().count()
        p_avg      = practice.aggregate(
            models.Avg('score_percent'))['score_percent__avg'] or 0

        t_students = tests.values('user').distinct().count()
        t_mastered = tests.filter(is_mastered=True).values('user').distinct().count()
        t_avg      = tests.aggregate(
            models.Avg('score_percent'))['score_percent__avg'] or 0

        # Attempt distribution
        attempt_dist = ""
        for i in range(1, 4):
            c = tests.filter(attempt_number=i).count()
            attempt_dist += (
                f"<tr><td style='padding:2px 8px;'>Attempt {i}</td>"
                f"<td style='padding:2px 8px;'><b>{c}</b></td></tr>"
            )

        html = (
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">'

            # Practice panel
            '<div style="background:#f8f9fa;padding:12px;border-radius:6px;'
            'border-left:4px solid #007bff;">'
            '<p style="font-weight:700;margin:0 0 8px;color:#007bff;">Practice Attempts</p>'
            '<table style="width:100%;font-size:0.9em;">'
            f'<tr><td>Students attempted</td><td><b>{p_students}</b></td></tr>'
            f'<tr><td>Passed (100%)</td>'
            f'<td><b style="color:#28a745;">{p_passed}</b></td></tr>'
            f'<tr><td>Average score</td><td><b>{p_avg:.1f}%</b></td></tr>'
            '</table>'
            '</div>'

            # Test panel
            '<div style="background:#f8f9fa;padding:12px;border-radius:6px;'
            'border-left:4px solid #28a745;">'
            '<p style="font-weight:700;margin:0 0 8px;color:#28a745;">Mastery Tests</p>'
            '<table style="width:100%;font-size:0.9em;">'
            f'<tr><td>Students tested</td><td><b>{t_students}</b></td></tr>'
            f'<tr><td>Mastered</td>'
            f'<td><b style="color:#28a745;">{t_mastered}</b></td></tr>'
            f'<tr><td>Average score</td><td><b>{t_avg:.1f}%</b></td></tr>'
            f'{attempt_dist}'
            '</table>'
            '</div>'

            '</div>'
        )
        return mark_safe(html)
    mastery_stats_display.short_description = "Practice vs Test Statistics"

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("chunk", "chunk__lesson")


# ═══════════════════════════════════════════════════════════════
#  COMPREHENSION QUESTION ADMIN  (unchanged)
# ═══════════════════════════════════════════════════════════════

@admin.register(ComprehensionQuestion)
class ComprehensionQuestionAdmin(admin.ModelAdmin):

    list_display = (
        "question_preview", "focus_link",
        "question_type", "difficulty", "has_options",
    )
    list_filter = ("question_type", "difficulty", "focus__level")
    search_fields = ("question_text", "correct_answer", "focus__focus_title")
    ordering = ("focus", "id")
    autocomplete_fields = ("focus",)
    readonly_fields = ("created_at", "updated_at", "options_preview")

    fieldsets = (
        ("Question Details", {
            "fields": ("focus", "question_type", "difficulty", "question_text"),
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
        text = obj.question_text or ""
        return text[:60] + "..." if len(text) > 60 else text
    question_preview.short_description = "Question"

    def focus_link(self, obj):
        url = reverse('admin:content_chunkcomprehensionfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def has_options(self, obj):
        return bool(obj.options)
    has_options.boolean = True
    has_options.short_description = "Has Options"

    def options_preview(self, obj):
        if not obj.options:
            return "No options"
        options = obj.get_options_list()
        parts = ["<ul>"]
        for opt in options:
            if opt == obj.correct_answer:
                parts.append(
                    f"<li><span style='color:green;font-weight:bold'>"
                    f"✓ {escape(opt)}</span></li>"
                )
            else:
                parts.append(f"<li>{escape(opt)}</li>")
        parts.append("</ul>")
        return mark_safe("".join(parts))
    options_preview.short_description = "Options Preview"

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


# ═══════════════════════════════════════════════════════════════
#  ATTEMPT ADMINS  (unchanged)
# ═══════════════════════════════════════════════════════════════

@admin.register(ComprehensionPracticeAttempt)
class ComprehensionPracticeAttemptAdmin(admin.ModelAdmin):

    list_display = (
        "user_link", "focus_link", "attempt_number",
        "cycle_number", "score_percent", "is_passed", "attempted_at",
    )
    list_filter = ("is_passed", "attempt_number", "cycle_number", "attempted_at")
    search_fields = ("user__username", "focus__focus_title")
    ordering = ("-attempted_at",)
    date_hierarchy = "attempted_at"
    readonly_fields = [f.name for f in ComprehensionPracticeAttempt._meta.fields]

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def focus_link(self, obj):
        url = reverse('admin:content_chunkcomprehensionfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ComprehensionTestAttempt)
class ComprehensionTestAttemptAdmin(admin.ModelAdmin):

    list_display = (
        "user_link", "focus_link", "attempt_number", "cycle_number",
        "score_percent", "is_mastered", "correct_answers",
        "total_questions", "created_at",
    )
    list_filter = (
        "is_mastered", "attempt_number", "cycle_number",
        "focus__level", "created_at",
    )
    search_fields = ("user__username", "focus__focus_title")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in ComprehensionTestAttempt._meta.fields]

    fieldsets = (
        ("Student",      {"fields": ("user", "focus")}),
        ("Attempt Info", {"fields": ("attempt_number", "cycle_number", "created_at")}),
        ("Results",      {"fields": ("score_percent", "is_mastered",
                                     "correct_answers", "total_questions")}),
        ("Snapshot",     {"fields": ("questions_data",), "classes": ("collapse",)}),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def focus_link(self, obj):
        url = reverse('admin:content_chunkcomprehensionfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ComprehensionQuestionAttempt)
class ComprehensionQuestionAttemptAdmin(admin.ModelAdmin):

    list_display = (
        "user_link", "question_link", "attempt_number",
        "cycle_number", "is_correct", "attempted_at",
    )
    list_filter = ("is_correct", "attempt_number", "cycle_number", "attempted_at")
    search_fields = ("user__username", "question__question_text")
    ordering = ("-attempted_at",)
    date_hierarchy = "attempted_at"
    readonly_fields = [f.name for f in ComprehensionQuestionAttempt._meta.fields]

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def question_link(self, obj):
        url = reverse('admin:content_comprehensionquestion_change', args=[obj.question.id])
        return format_html('<a href="{}">Q{}</a>', url, obj.question.id)
    question_link.short_description = "Question"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


__all__ = [
    'ChunkComprehensionFocusAdmin',
    'ComprehensionQuestionAdmin',
    'ComprehensionPracticeAttemptAdmin',
    'ComprehensionTestAttemptAdmin',
    'ComprehensionQuestionAttemptAdmin',
]