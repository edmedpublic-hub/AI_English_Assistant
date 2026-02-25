# content/admin/inlines/testing.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from content.models.testing import (
    UnitTestQuestion,
    UnitTestAnswer,
    VocabularyUnitTestAttempt,
)


class UnitTestQuestionInline(admin.TabularInline):
    """
    Inline for viewing questions within a UnitTestSession.
    Read-only to maintain data integrity.
    """
    model = UnitTestQuestion
    extra = 0
    fields = (
        "order",
        "domain",
        "question_preview",
        "question_type",
        "difficulty",
        "correct_answer_preview",
    )
    readonly_fields = (
        "order",
        "domain",
        "question_preview",
        "question_type",
        "difficulty",
        "correct_answer_preview",
    )
    ordering = ("order",)
    can_delete = False
    
    def question_preview(self, obj):
        """Short preview of the question"""
        return obj.question_text[:60] + "..." if len(obj.question_text) > 60 else obj.question_text
    question_preview.short_description = "Question"
    
    def correct_answer_preview(self, obj):
        """Show correct answer with visual indicator"""
        if obj.question_type == 'mcq' and obj.options:
            for opt in obj.options:
                if opt == obj.correct_answer:
                    return format_html('<span style="color:green;">✓ {}</span>', opt)
        return obj.correct_answer
    correct_answer_preview.short_description = "Correct Answer"
    
    def has_add_permission(self, request, obj=None):
        return False


class UnitTestQuestionStackedInline(admin.StackedInline):
    """
    Stacked inline for more detailed question view.
    """
    model = UnitTestQuestion
    extra = 0
    fieldsets = (
        ('Question Info', {
            'fields': ('order', 'domain', 'question_type', 'difficulty')
        }),
        ('Question Text', {
            'fields': ('question_text',)
        }),
        ('Answer', {
            'fields': ('options_preview', 'correct_answer'),
        }),
        ('Domain References', {
            'fields': ('vocabulary_item', 'grammar_concept', 'punctuation_mark', 'bloom_level'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = (
        'order',
        'domain',
        'question_type',
        'difficulty',
        'question_text',
        'correct_answer',
        'vocabulary_item',
        'grammar_concept',
        'punctuation_mark',
        'bloom_level',
        'options_preview',
    )
    ordering = ("order",)
    can_delete = False
    
    def options_preview(self, obj):
        """Display options with correct answer highlighted"""
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
    
    def has_add_permission(self, request, obj=None):
        return False


class UnitTestAnswerInline(admin.TabularInline):
    """
    Inline for viewing answers within a UnitTestQuestion.
    Read-only to maintain data integrity.
    """
    model = UnitTestAnswer
    extra = 0
    fields = (
        "user_link",
        "student_answer_preview",
        "is_correct",
        "time_taken_seconds",
        "answered_at",
    )
    readonly_fields = (
        "user_link",
        "student_answer_preview",
        "is_correct",
        "time_taken_seconds",
        "answered_at",
    )
    ordering = ("-answered_at",)
    can_delete = False
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.question.session.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.question.session.user.username)
    user_link.short_description = "User"
    
    def student_answer_preview(self, obj):
        return obj.student_answer[:50] + "..." if len(obj.student_answer) > 50 else obj.student_answer
    student_answer_preview.short_description = "Answer"
    
    def has_add_permission(self, request, obj=None):
        return False


class VocabularyUnitTestAttemptInline(admin.TabularInline):
    """
    Inline for viewing vocabulary-specific test attempts within a UnitTestSession.
    """
    model = VocabularyUnitTestAttempt
    extra = 0
    fields = (
        "user_link",
        "score_percent",
        "correct_answers",
        "total_questions",
        "created_at",
    )
    readonly_fields = (
        "user_link",
        "score_percent",
        "correct_answers",
        "total_questions",
        "created_at",
    )
    ordering = ("-created_at",)
    can_delete = False
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def has_add_permission(self, request, obj=None):
        return False


class VocabularyUnitTestAttemptDetailInline(admin.StackedInline):
    """
    Detailed inline for vocabulary test attempts with question data.
    """
    model = VocabularyUnitTestAttempt
    extra = 0
    fieldsets = (
        ('Student', {
            'fields': ('user_link',)
        }),
        ('Results', {
            'fields': ('score_percent', 'correct_answers', 'total_questions', 'created_at')
        }),
        ('Question Data', {
            'fields': ('questions_data_preview',),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = (
        'user_link',
        'score_percent',
        'correct_answers',
        'total_questions',
        'created_at',
        'questions_data_preview',
    )
    ordering = ("-created_at",)
    can_delete = False
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def questions_data_preview(self, obj):
        """Display questions data in a readable format"""
        if not obj.questions_data:
            return "No question data available"
        
        html = "<table style='width:100%'>"
        html += "<tr><th>#</th><th>Question</th><th>Correct?</th></tr>"
        
        for i, q in enumerate(obj.questions_data.get('questions', []), 1):
            is_correct = q.get('is_correct', False)
            color = 'green' if is_correct else 'red'
            check = '✓' if is_correct else '✗'
            html += f"<tr><td>{i}</td><td>{q.get('question_text', '')[:50]}...</td><td style='color:{color};'>{check}</td></tr>"
        
        html += "</table>"
        return format_html(html)
    questions_data_preview.short_description = "Question Details"
    
    def has_add_permission(self, request, obj=None):
        return False