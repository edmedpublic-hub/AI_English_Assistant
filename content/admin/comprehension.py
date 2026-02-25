# content/admin/comprehension.py

from django.contrib import admin
from django.utils.html import format_html
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


# ============================================================
# Focus-level authoring
# ============================================================

@admin.register(ChunkComprehensionFocus)
class ChunkComprehensionFocusAdmin(admin.ModelAdmin):
    """
    Authoring surface for comprehension pedagogy inside a chunk.
    """

    list_display = (
        "focus_title", 
        "chunk_link", 
        "level", 
        "depth_level",
        "sequence_order",
        "question_count",
        "mastery_rate"
    )
    list_filter = ("level", "depth_level", "chunk__lesson__unit__textbook")
    search_fields = ("focus_title", "focus_description", "chunk__english_text")
    ordering = ("chunk", "sequence_order")
    autocomplete_fields = ("chunk",)
    readonly_fields = (
        "created_at", 
        "updated_at",
        "question_count_display",
        "mastery_stats_display"
    )
    
    fieldsets = (
        ("Comprehension Focus", {
            "fields": ("chunk", "focus_title", "focus_description")
        }),
        ("Bloom's Taxonomy", {
            "fields": ("level", "depth_level", "sequence_order"),
            "description": "Level: Literal → Inferential → Evaluative | Depth: 1(Beginner)-5(Advanced)"
        }),
        ("Questions", {
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

    inlines = [ComprehensionQuestionInline]

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
            url = reverse('admin:content_comprehensionquestion_changelist') + f'?focus__id__exact={obj.id}'
            return format_html('<a href="{}">{} question{}</a>', url, count, 's' if count != 1 else '')
        return format_html('<span style="color: orange;">No questions yet</span>')
    question_count_display.short_description = "Questions"
    
    def mastery_rate(self, obj):
        """Show what percentage of students have mastered this focus"""
        total_attempts = ComprehensionTestAttempt.objects.filter(focus=obj).values('user').distinct().count()
        if total_attempts == 0:
            return format_html('<span style="color:gray;">No data</span>')
        
        mastered = ComprehensionTestAttempt.objects.filter(
            focus=obj, 
            is_mastered=True
        ).values('user').distinct().count()
        
        percentage = (mastered / total_attempts) * 100
        color = 'green' if percentage >= 80 else 'orange' if percentage >= 50 else 'red'
        
        return format_html(
            '<span style="color:{};">{}% ({} of {})</span>',
            color, int(percentage), mastered, total_attempts
        )
    mastery_rate.short_description = "Mastery Rate"
    
    def mastery_stats_display(self, obj):
        """Detailed mastery statistics"""
        attempts = ComprehensionTestAttempt.objects.filter(focus=obj)
        
        if not attempts.exists():
            return "No attempts yet"
        
        total_students = attempts.values('user').distinct().count()
        mastered_students = attempts.filter(is_mastered=True).values('user').distinct().count()
        
        avg_score = attempts.aggregate(models.Avg('score_percent'))['score_percent__avg'] or 0
        
        # Attempt distribution
        attempt_counts = {}
        for i in range(1, 4):
            attempt_counts[f'attempt_{i}'] = attempts.filter(attempt_number=i).count()
        
        # Performance by Bloom's level
        level_performance = {}
        for level in ['literal', 'inferential', 'evaluative']:
            level_attempts = ComprehensionQuestionAttempt.objects.filter(
                test_attempt__focus=obj,
                question__focus__level=level
            )
            if level_attempts.exists():
                correct = level_attempts.filter(is_correct=True).count()
                total = level_attempts.count()
                level_performance[level] = (correct / total) * 100 if total > 0 else 0
        
        html = f"""
        <table style="width:100%">
            <tr><td>Total Students:</td><td><b>{total_students}</b></td></tr>
            <tr><td>Mastered:</td><td><b style="color:green;">{mastered_students}</b></td></tr>
            <tr><td>Average Score:</td><td><b>{avg_score:.1f}%</b></td></tr>
            <tr><td colspan="2"><hr></td></tr>
            <tr><td>Attempt 1:</td><td>{attempt_counts.get('attempt_1', 0)}</td></tr>
            <tr><td>Attempt 2:</td><td>{attempt_counts.get('attempt_2', 0)}</td></tr>
            <tr><td>Attempt 3:</td><td>{attempt_counts.get('attempt_3', 0)}</td></tr>
        """
        
        if level_performance:
            html += '<tr><td colspan="2"><hr></td></tr>'
            html += '<tr><th colspan="2">Performance by Level</th></tr>'
            for level, score in level_performance.items():
                color = 'green' if score >= 80 else 'orange' if score >= 50 else 'red'
                html += f'<tr><td>{level.title()}:</td><td><span style="color:{color};">{score:.1f}%</span></td></tr>'
        
        html += "</table>"
        return format_html(html)
    mastery_stats_display.short_description = "Mastery Statistics"

    # Prevent accidental re-ordering that violates pedagogy
    def save_model(self, request, obj, form, change):
        obj.full_clean()  # enforce model.clean()
        super().save_model(request, obj, form, change)


# ============================================================
# Question authoring
# ============================================================

@admin.register(ComprehensionQuestion)
class ComprehensionQuestionAdmin(admin.ModelAdmin):
    """
    Direct question editing (rarely used; mostly inline-driven).
    """

    list_display = (
        "question_preview", 
        "focus_link", 
        "question_type", 
        "difficulty",
        "has_options"
    )
    list_filter = ("question_type", "difficulty", "focus__level")
    search_fields = ("question_text", "correct_answer", "focus__focus_title")
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
        html = "<ul>"
        for opt in options:
            if opt == obj.correct_answer:
                html += f"<li><span style='color:green;font-weight:bold'>✓ {opt}</span></li>"
            else:
                html += f"<li>{opt}</li>"
        html += "</ul>"
        return format_html(html)
    options_preview.short_description = "Options Preview"

    # Enforce validation before save
    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


# ============================================================
# Practice attempts (read-only)
# ============================================================

@admin.register(ComprehensionPracticeAttempt)
class ComprehensionPracticeAttemptAdmin(admin.ModelAdmin):
    """
    Immutable analytics log for practice attempts.
    """

    list_display = (
        "user_link",
        "focus_link",
        "attempt_number",
        "cycle_number",
        "score_percent",
        "is_passed",
        "attempted_at"
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


# ============================================================
# Test attempts (mastery-level analytics)
# ============================================================

@admin.register(ComprehensionTestAttempt)
class ComprehensionTestAttemptAdmin(admin.ModelAdmin):
    """
    Shows mastery progression across focuses.
    Critical for LMS analytics.
    """

    list_display = (
        "user_link",
        "focus_link",
        "attempt_number",
        "cycle_number",
        "score_percent",
        "is_mastered",
        "correct_answers",
        "total_questions",
        "created_at",
    )

    list_filter = (
        "is_mastered",
        "attempt_number",
        "cycle_number",
        "focus__level",
        "created_at",
    )

    search_fields = (
        "user__username",
        "focus__focus_title",
    )

    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in ComprehensionTestAttempt._meta.fields]
    
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
        url = reverse('admin:content_chunkcomprehensionfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = "Focus"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# Per-question analytics (read-only)
# ============================================================

@admin.register(ComprehensionQuestionAttempt)
class ComprehensionQuestionAttemptAdmin(admin.ModelAdmin):
    """
    Granular per-question analytics.
    """

    list_display = (
        "user_link",
        "question_link",
        "attempt_number",
        "cycle_number",
        "is_correct",
        "attempted_at"
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