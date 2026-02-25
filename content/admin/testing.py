# content/admin/testing.py

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


# ============================================================
# UNIT TEST SESSIONS (Comprehensive Assessments)
# ============================================================

@admin.register(UnitTestSession)
class UnitTestSessionAdmin(admin.ModelAdmin):
    """
    Complete unit test sessions covering all domains.
    """
    list_display = (
        "user_link",
        "unit_link",
        "attempt_number",
        "score_percentage",
        "passed",
        "total_questions",
        "correct_answers",
        "started_at",
        "completed_at",
    )

    list_filter = ("passed", "attempt_number", "started_at", "unit__textbook")
    search_fields = ("user__username", "unit__title", "unit__textbook__title")
    ordering = ("-started_at",)
    date_hierarchy = "started_at"
    
    readonly_fields = [
        "user",
        "unit",
        "attempt_number",
        "started_at",
        "completed_at",
        "time_taken_seconds",
        "total_questions",
        "correct_answers",
        "score_percentage",
        "passed",
        "domain_scores",
        "test_data",
        "domain_breakdown_display",
    ]
    
    fieldsets = (
        ("Student", {
            "fields": ("user", "unit")
        }),
        ("Attempt Info", {
            "fields": ("attempt_number", "started_at", "completed_at", "time_taken_seconds")
        }),
        ("Results", {
            "fields": ("score_percentage", "passed", "correct_answers", "total_questions")
        }),
        ("Domain Breakdown", {
            "fields": ("domain_breakdown_display",),
        }),
        ("Raw Data", {
            "fields": ("domain_scores", "test_data"),
            "classes": ("collapse",),
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def unit_link(self, obj):
        url = reverse('admin:content_unit_change', args=[obj.unit.id])
        return format_html('<a href="{}">{}</a>', url, obj.unit)
    unit_link.short_description = "Unit"
    
    def domain_breakdown_display(self, obj):
        """Display domain scores in a readable table"""
        if not obj.domain_scores:
            return "No domain data"
        
        html = "<table style='width:100%'>"
        html += "<tr><th>Domain</th><th>Score</th><th>Status</th></tr>"
        
        for domain, score in obj.domain_scores.items():
            # Determine color based on score
            if domain == 'vocabulary' or domain == 'grammar' or domain == 'punctuation' or domain == 'comprehension':
                # These require 100% for mastery
                color = 'green' if score == 100 else 'orange' if score >= 70 else 'red'
            else:
                # Writing and pronunciation have different thresholds
                color = 'green' if score >= 90 else 'orange' if score >= 70 else 'red'
            
            html += f"<tr><td>{domain.title()}</td><td>{score}%</td><td style='color:{color};'>●</td></tr>"
        
        html += "</table>"
        return format_html(html)
    domain_breakdown_display.short_description = "Domain Performance"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# UNIT TEST QUESTIONS
# ============================================================

@admin.register(UnitTestQuestion)
class UnitTestQuestionAdmin(admin.ModelAdmin):
    """
    Individual questions within unit tests.
    """
    list_display = (
        "session_link",
        "order",
        "domain",
        "question_preview",
        "question_type",
        "difficulty",
        "points",
    )

    list_filter = ("domain", "question_type", "difficulty", "session__unit")
    search_fields = ("question_text", "session__user__username")
    ordering = ("session", "order")
    
    readonly_fields = [
        "session",
        "domain",
        "question_type",
        "question_text",
        "options",
        "correct_answer",
        "difficulty",
        "order",
        "points",
        "vocabulary_item",
        "grammar_concept",
        "punctuation_mark",
        "bloom_level",
        "options_preview",
    ]
    
    fieldsets = (
        ("Session", {
            "fields": ("session", "order", "domain")
        }),
        ("Question", {
            "fields": ("question_text", "question_type", "difficulty", "points")
        }),
        ("Answer", {
            "fields": ("options_preview", "correct_answer"),
        }),
        ("Domain References", {
            "fields": ("vocabulary_item", "grammar_concept", "punctuation_mark", "bloom_level"),
            "classes": ("collapse",),
        }),
    )

    def session_link(self, obj):
        url = reverse('admin:content_unittestsession_change', args=[obj.session.id])
        return format_html('<a href="{}">Session {}</a>', url, obj.session.id)
    session_link.short_description = "Session"
    
    def question_preview(self, obj):
        return obj.question_text[:60] + "..." if len(obj.question_text) > 60 else obj.question_text
    question_preview.short_description = "Question"
    
    def options_preview(self, obj):
        """Preview options with correct answer highlighted"""
        if not obj.options:
            return "No options"
        
        html = "<ul style='margin:0;padding-left:15px;'>"
        for opt in obj.options:
            if opt == obj.correct_answer:
                html += f"<li><span style='color:green;font-weight:bold'>✓ {opt}</span></li>"
            else:
                html += f"<li>{opt}</li>"
        html += "</ul>"
        return format_html(html)
    options_preview.short_description = "Options"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# UNIT TEST ANSWERS
# ============================================================

@admin.register(UnitTestAnswer)
class UnitTestAnswerAdmin(admin.ModelAdmin):
    """
    Individual student answers to test questions.
    """
    list_display = (
        "question_link",
        "student_answer_preview",
        "is_correct",
        "time_taken_seconds",
        "answered_at",
    )

    list_filter = ("is_correct", "answered_at")
    search_fields = ("question__session__user__username", "student_answer")
    ordering = ("-answered_at",)
    date_hierarchy = "answered_at"
    
    readonly_fields = [f.name for f in UnitTestAnswer._meta.fields]
    
    fieldsets = (
        ("Question", {
            "fields": ("question",)
        }),
        ("Answer", {
            "fields": ("student_answer", "is_correct", "time_taken_seconds", "answered_at")
        }),
    )

    def question_link(self, obj):
        url = reverse('admin:content_unittestquestion_change', args=[obj.question.id])
        return format_html('<a href="{}">Q{}</a>', url, obj.question.order)
    question_link.short_description = "Question"
    
    def student_answer_preview(self, obj):
        return obj.student_answer[:50] + "..." if len(obj.student_answer) > 50 else obj.student_answer
    student_answer_preview.short_description = "Answer"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# VOCABULARY UNIT TEST ATTEMPTS (Domain-specific)
# ============================================================

@admin.register(VocabularyUnitTestAttempt)
class VocabularyUnitTestAttemptAdmin(admin.ModelAdmin):
    """
    Vocabulary-specific portion of unit tests.
    Maintained for detailed analytics.
    """
    list_display = (
        "user_link",
        "unit_test_session_link",
        "score_percent",
        "correct_answers",
        "total_questions",
        "created_at",
    )

    list_filter = ("score_percent", "created_at", "unit_test_session__unit")
    search_fields = ("user__username", "unit_test_session__unit__title")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    
    readonly_fields = [f.name for f in VocabularyUnitTestAttempt._meta.fields]
    
    fieldsets = (
        ("Student", {
            "fields": ("user", "unit_test_session")
        }),
        ("Results", {
            "fields": ("score_percent", "correct_answers", "total_questions", "created_at")
        }),
        ("Details", {
            "fields": ("lesson", "chunk", "questions_data"),
            "classes": ("collapse",),
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def unit_test_session_link(self, obj):
        url = reverse('admin:content_unittestsession_change', args=[obj.unit_test_session.id])
        return format_html('<a href="{}">Session {}</a>', url, obj.unit_test_session.id)
    unit_test_session_link.short_description = "Test Session"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# LEGACY MODELS (Deprecated - kept for reference only)
# ============================================================
# The following models have been replaced by the unified UnitTest system:
# - VocabularyTestSession → Use UnitTestSession
# - VocabularyTestQuestion → Use UnitTestQuestion  
# - VocabularyTestAnswer → Use UnitTestAnswer
# - VocabularyTestAttempt → Use VocabularyUnitTestAttempt
#
# They are no longer registered in admin to avoid confusion.