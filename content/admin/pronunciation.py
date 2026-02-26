# content/admin/pronunciation.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from content.models.pronunciation import (
    PronunciationFocus,
    PronunciationAttempt,
    PronunciationMastery,
)
from content.admin.inlines.pronunciation import (
    PronunciationAttemptInline,
    PronunciationMasteryInline,
)


# ============================================================
# PRONUNCIATION FOCUS (Teaching Layer)
# ============================================================

@admin.register(PronunciationFocus)
class PronunciationFocusAdmin(admin.ModelAdmin):
    """
    Admin for pronunciation focuses linked to chunks.
    """
    list_display = (
        "focus_title",
        "chunk_link",
        "sequence_order",
        "attempt_count",
        "mastery_count",
        "created_at"
    )
    list_filter = ("sequence_order",)
    search_fields = ("focus_title", "focus_description", "chunk__english_text")
    ordering = ("chunk", "sequence_order")
    autocomplete_fields = ("chunk",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "attempt_count_display",
        "mastery_stats_display"
    )

    fieldsets = (
        ("Pronunciation Focus", {
            "fields": ("chunk", "focus_title", "focus_description", "sequence_order")
        }),
        ("Statistics", {
            "fields": ("attempt_count_display", "mastery_stats_display"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    inlines = [PronunciationAttemptInline, PronunciationMasteryInline]

    def chunk_link(self, obj):
        url = reverse('admin:content_lessonchunk_change', args=[obj.chunk.id])
        return format_html('<a href="{}">{}</a>', url, obj.chunk)
    chunk_link.short_description = "Chunk"

    def attempt_count(self, obj):
        return obj.attempts.count()
    attempt_count.short_description = "Attempts"

    def attempt_count_display(self, obj):
        count = obj.attempts.count()
        if count > 0:
            url = reverse('admin:content_pronunciationattempt_changelist') + f'?focus__id__exact={obj.id}'
            return format_html('<a href="{}">{} attempt{}</a>', url, count, 's' if count != 1 else '')
        return "No attempts yet"
    attempt_count_display.short_description = "Attempts"

    def mastery_count(self, obj):
        return PronunciationMastery.objects.filter(focus=obj, is_mastered=True).count()
    mastery_count.short_description = "Mastered"

    def mastery_stats_display(self, obj):
        from django.db.models import Avg

        total_students = PronunciationMastery.objects.filter(focus=obj).count()
        mastered = PronunciationMastery.objects.filter(focus=obj, is_mastered=True).count()

        avg_best = PronunciationMastery.objects.filter(
            focus=obj,
            best_score__isnull=False
        ).aggregate(Avg('best_score'))['best_score__avg']

        html = f"""
        <table style="width:100%">
            <tr><td>Students Attempted:</td><td><b>{total_students}</b></td></tr>
            <tr><td>Mastered (90%+):</td><td><b style="color:green;">{mastered}</b></td></tr>
        """

        if avg_best:
            html += f'<tr><td>Average Best Score:</td><td><b>{avg_best:.1f}%</b></td></tr>'

        if mastered > 0 and total_students > 0:
            percentage = (mastered / total_students) * 100
            color = 'green' if percentage >= 80 else 'orange' if percentage >= 50 else 'red'
            html += f'<tr><td>Mastery Rate:</td><td><b style="color:{color};">{percentage:.1f}%</b></td></tr>'

        html += "</table>"
        return format_html(html)
    mastery_stats_display.short_description = "Mastery Statistics"


# ============================================================
# PRONUNCIATION ATTEMPTS
# Teachers can score attempts manually here until AI is ready.
# When AI scoring is live, this becomes read-only analytics.
# ============================================================

@admin.register(PronunciationAttempt)
class PronunciationAttemptAdmin(admin.ModelAdmin):
    """
    Scoring interface for pronunciation attempts.

    Teachers use this to:
    1. Download student recordings
    2. Enter a score (0-100) — 90+ = passed
    3. Enter written feedback
    4. Save — mastery is updated automatically via save_model()
    """
    list_display = (
        "user_link",
        "focus_link",
        "attempt_number",
        "cycle_number",
        "ai_score",
        "is_passed_display",
        "attempt_type",
        "pending_review",
        "created_at",
    )

    list_filter = (
        "attempt_type",
        "attempt_number",
        "cycle_number",
        "created_at",
    )
    search_fields = ("user__username", "focus__focus_title", "ai_feedback")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    # Structural fields are read-only — only score/feedback are editable
    readonly_fields = (
        "user",
        "focus",
        "attempt_number",
        "cycle_number",
        "attempt_type",
        "created_at",
        "recording_link",
        "is_passed_display",
        "pending_review",
    )

    fieldsets = (
        ("Student", {
            "fields": ("user", "focus")
        }),
        ("Attempt Info", {
            "fields": ("attempt_number", "cycle_number", "attempt_type", "created_at")
        }),
        ("Recording", {
            "fields": ("recording_link", "recording"),
        }),
        ("Scoring — Enter score and feedback here", {
            "fields": ("ai_score", "is_passed_display", "ai_feedback"),
            "description": (
                "Enter a score from 0 to 100. "
                "90 or above = passed. "
                "Mastery is updated automatically when you save."
            ),
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def focus_link(self, obj):
        url = reverse('admin:content_pronunciationfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def is_passed_display(self, obj):
        if obj.ai_score is None:
            return format_html('<span style="color:gray;">⏳ Pending</span>')
        if obj.is_passed:
            return format_html('<span style="color:green;font-weight:bold;">✓ Passed</span>')
        return format_html('<span style="color:red;">✗ Failed ({}/100)</span>', obj.ai_score)
    is_passed_display.short_description = "Result"

    def pending_review(self, obj):
        if obj.ai_score is None:
            return format_html('<span style="color:orange;font-weight:bold;">⚠ Needs Scoring</span>')
        return format_html('<span style="color:green;">✓ Scored</span>')
    pending_review.short_description = "Review Status"

    def recording_link(self, obj):
        if obj.recording:
            return format_html(
                '<a href="{}" target="_blank" style="font-weight:bold;">▶ Download & Listen</a>',
                obj.recording.url
            )
        return format_html('<span style="color:gray;">No recording</span>')
    recording_link.short_description = "Recording"

    def save_model(self, request, obj, form, change):
        """
        After saving a score, automatically update PronunciationMastery.
        This is the bridge between manual scoring and the mastery system.
        """
        super().save_model(request, obj, form, change)

        if obj.ai_score is not None:
            mastery, _ = PronunciationMastery.objects.get_or_create(
                user=obj.user,
                focus=obj.focus,
            )

            # Update statistics
            mastery.last_score = obj.ai_score
            mastery.last_attempted = obj.created_at

            if mastery.best_score is None or obj.ai_score > mastery.best_score:
                mastery.best_score = obj.ai_score

            # Recalculate total attempts
            mastery.total_attempts = PronunciationAttempt.objects.filter(
                user=obj.user,
                focus=obj.focus,
                ai_score__isnull=False,
            ).count()

            # Check mastery
            if obj.is_passed and not mastery.is_mastered:
                mastery.is_mastered = True
                mastery.mastered_at = timezone.now()

            mastery.save()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# PRONUNCIATION MASTERY (Read-only Analytics)
# ============================================================

@admin.register(PronunciationMastery)
class PronunciationMasteryAdmin(admin.ModelAdmin):
    """
    Read-only view of pronunciation mastery status.
    Updated automatically when teacher scores an attempt.
    """
    list_display = (
        "user_link",
        "focus_link",
        "is_mastered",
        "best_score",
        "last_score",
        "total_attempts",
        "last_attempted",
    )

    list_filter = ("is_mastered", "last_attempted")
    search_fields = ("user__username", "focus__focus_title")
    ordering = ("-last_attempted",)
    readonly_fields = [f.name for f in PronunciationMastery._meta.fields]

    fieldsets = (
        ("Student", {
            "fields": ("user", "focus")
        }),
        ("Mastery Status", {
            "fields": ("is_mastered", "mastered_at", "best_score", "last_score")
        }),
        ("Attempt Statistics", {
            "fields": ("total_attempts", "last_attempted"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"

    def focus_link(self, obj):
        url = reverse('admin:content_pronunciationfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False