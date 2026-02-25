# content/admin/grammar.py - TEMPORARY FIX for migrations

from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.urls import reverse

from content.models.grammar import (
    GrammarConcept,
    GrammarRule,
    GrammarExample,
    ChunkGrammarFocus,
    GrammarQuestion,
    GrammarPracticeAttempt,
    GrammarTestAttempt,
    GrammarQuestionAttempt,
)

from content.admin.inlines.grammar import GrammarQuestionInline


# ============================================================
# CURRICULUM LAYER (Global Grammar Knowledge)
# Rarely edited, protected from accidental deletion
# ============================================================

class GrammarExampleInline(admin.TabularInline):
    model = GrammarExample
    extra = 1
    fields = ['sentence', 'order']
    ordering = ['order']


class GrammarRuleInline(admin.TabularInline):
    model = GrammarRule
    extra = 1
    fields = ['rule_text', 'order']
    ordering = ['order']
    show_change_link = True
    # inlines = [GrammarExampleInline]  # Comment out nested inlines for now


@admin.register(GrammarConcept)
class GrammarConceptAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order_index', 'rule_count', 'usage_count')
    list_filter = ('category',)
    search_fields = ('name', 'description', 'category')
    ordering = ('order_index', 'name')
    readonly_fields = ('created_at', 'updated_at', 'rule_count_display', 'usage_count_display')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Curriculum Order', {
            'fields': ('order_index',)
        }),
        ('Statistics', {
            'fields': ('rule_count_display', 'usage_count_display'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [GrammarRuleInline]
    prepopulated_fields = {'slug': ('name',)}
    
    def rule_count(self, obj):
        return obj.rules.count()
    rule_count.short_description = 'Rules'
    
    def rule_count_display(self, obj):
        count = obj.rules.count()
        return format_html('<b>{}</b> rule{}', count, 's' if count != 1 else '')
    rule_count_display.short_description = 'Rules'
    
    def usage_count(self, obj):
        """Count how many chunks use this concept"""
        return obj.teaching_instances.count()
    usage_count.short_description = 'Used in'
    
    def usage_count_display(self, obj):
        count = obj.teaching_instances.count()
        if count > 0:
            url = reverse('admin:content_chunkgrammarfocus_changelist') + f'?concept__id__exact={obj.id}'
            return format_html('<a href="{}">{} chunk{}</a>', url, count, 's' if count != 1 else '')
        return 'Not used yet'
    usage_count_display.short_description = 'Used in'


@admin.register(GrammarRule)
class GrammarRuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'concept', 'rule_preview', 'order', 'example_count')
    list_filter = ('concept__category', 'concept')
    search_fields = ('rule_text', 'concept__name')
    ordering = ('concept', 'order')
    autocomplete_fields = ['concept']
    readonly_fields = ('created_at', 'updated_at', 'example_count_display')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('concept', 'rule_text', 'order')
        }),
        ('Statistics', {
            'fields': ('example_count_display',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [GrammarExampleInline]
    
    def rule_preview(self, obj):
        return obj.rule_text[:60] + '...' if len(obj.rule_text) > 60 else obj.rule_text
    rule_preview.short_description = 'Rule'
    
    def example_count(self, obj):
        return obj.examples.count()
    example_count.short_description = 'Examples'
    
    def example_count_display(self, obj):
        count = obj.examples.count()
        return format_html('<b>{}</b> example{}', count, 's' if count != 1 else '')
    example_count_display.short_description = 'Examples'


@admin.register(GrammarExample)
class GrammarExampleAdmin(admin.ModelAdmin):
    list_display = ('id', 'rule', 'sentence_preview', 'order')
    list_filter = ('rule__concept',)
    search_fields = ('sentence', 'rule__rule_text')
    ordering = ('rule', 'order')
    autocomplete_fields = ['rule']
    readonly_fields = ('created_at', 'updated_at')
    
    def sentence_preview(self, obj):
        return obj.sentence[:80] + '...' if len(obj.sentence) > 80 else obj.sentence
    sentence_preview.short_description = 'Sentence'


# ============================================================
# TEACHING LAYER (Chunk-level Focus)
# This is where content authors spend most time
# ============================================================

@admin.register(ChunkGrammarFocus)
class ChunkGrammarFocusAdmin(admin.ModelAdmin):
    list_display = (
        'focus_title', 
        'chunk_link', 
        'concept', 
        'depth_level', 
        'sequence_order',
        'question_count',
        'mastery_rate'
    )
    list_filter = ('concept', 'depth_level', 'sequence_order')
    search_fields = ('focus_title', 'focus_description', 'chunk__english_text')
    ordering = ('chunk', 'sequence_order')
    autocomplete_fields = ('concept', 'chunk')
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'question_count_display',
        'mastery_stats_display'
    )
    
    fieldsets = (
        ('Teaching Focus', {
            'fields': ('chunk', 'concept', 'focus_title', 'focus_description')
        }),
        ('Pedagogy', {
            'fields': ('depth_level', 'sequence_order'),
            'description': 'Depth: 1(Beginner) → 5(Advanced) | Sequence: Order within chunk'
        }),
        ('Questions', {
            'fields': ('question_count_display',),
        }),
        ('Mastery Statistics', {
            'fields': ('mastery_stats_display',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [GrammarQuestionInline]
    
    def chunk_link(self, obj):
        url = reverse('admin:content_lessonchunk_change', args=[obj.chunk.id])
        return format_html('<a href="{}">{}</a>', url, obj.chunk)
    chunk_link.short_description = 'Chunk'
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'
    
    def question_count_display(self, obj):
        count = obj.questions.count()
        if count > 0:
            url = reverse('admin:content_grammarquestion_changelist') + f'?focus__id__exact={obj.id}'
            return format_html('<a href="{}">{} question{}</a>', url, count, 's' if count != 1 else '')
        return 'No questions yet'
    question_count_display.short_description = 'Questions'
    
    def mastery_rate(self, obj):
        """Show what percentage of students have mastered this focus"""
        total_attempts = GrammarTestAttempt.objects.filter(focus=obj).values('user').distinct().count()
        if total_attempts == 0:
            return format_html('<span style="color:gray;">No data</span>')
        
        mastered = GrammarTestAttempt.objects.filter(
            focus=obj, 
            is_mastered=True
        ).values('user').distinct().count()
        
        percentage = (mastered / total_attempts) * 100
        color = 'green' if percentage >= 80 else 'orange' if percentage >= 50 else 'red'
        
        return format_html(
            '<span style="color:{};">{}% ({} of {})</span>',
            color, int(percentage), mastered, total_attempts
        )
    mastery_rate.short_description = 'Mastery Rate'
    
    def mastery_stats_display(self, obj):
        """Detailed mastery statistics"""
        attempts = GrammarTestAttempt.objects.filter(focus=obj)
        
        if not attempts.exists():
            return "No attempts yet"
        
        total_students = attempts.values('user').distinct().count()
        mastered_students = attempts.filter(is_mastered=True).values('user').distinct().count()
        
        avg_score = attempts.aggregate(models.Avg('score_percent'))['score_percent__avg'] or 0
        
        # Attempt distribution
        attempt_counts = {}
        for i in range(1, 4):
            attempt_counts[f'attempt_{i}'] = attempts.filter(attempt_number=i).count()
        
        html = f"""
        <table style="width:100%">
            <tr><td>Total Students:</td><td><b>{total_students}</b></td></tr>
            <tr><td>Mastered:</td><td><b style="color:green;">{mastered_students}</b></td></tr>
            <tr><td>Average Score:</td><td><b>{avg_score:.1f}%</b></td></tr>
            <tr><td colspan="2"><hr></td></tr>
            <tr><td>Attempt 1:</td><td>{attempt_counts.get('attempt_1', 0)}</td></tr>
            <tr><td>Attempt 2:</td><td>{attempt_counts.get('attempt_2', 0)}</td></tr>
            <tr><td>Attempt 3:</td><td>{attempt_counts.get('attempt_3', 0)}</td></tr>
        </table>
        """
        return format_html(html)
    mastery_stats_display.short_description = 'Mastery Statistics'


# ============================================================
# QUESTIONS
# ============================================================

@admin.register(GrammarQuestion)
class GrammarQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'focus_link', 
        'question_preview', 
        'question_type', 
        'difficulty',
        'has_options'
    )
    list_filter = ('question_type', 'difficulty', 'focus__concept')
    search_fields = ('question_text', 'correct_answer', 'explanation')
    ordering = ('focus', 'id')
    autocomplete_fields = ['focus']
    readonly_fields = ('created_at', 'updated_at', 'options_preview')
    
    fieldsets = (
        ('Question Details', {
            'fields': ('focus', 'question_type', 'difficulty', 'question_text')
        }),
        ('Answer', {
            'fields': ('options', 'options_preview', 'correct_answer', 'explanation'),
            'description': 'For MCQ: One option per line'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def focus_link(self, obj):
        url = reverse('admin:content_chunkgrammarfocus_change', args=[obj.focus.id])
        return format_html('<a href="{}">{}</a>', url, obj.focus.focus_title)
    focus_link.short_description = 'Focus'
    
    def question_preview(self, obj):
        return obj.question_text[:60] + '...' if len(obj.question_text) > 60 else obj.question_text
    question_preview.short_description = 'Question'
    
    def has_options(self, obj):
        return bool(obj.options)
    has_options.boolean = True
    has_options.short_description = 'Has Options'
    
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
    options_preview.short_description = 'Options Preview'


# ============================================================
# ANALYTICS (Read-only)
# ============================================================

@admin.register(GrammarPracticeAttempt)
class GrammarPracticeAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'focus', 
        'attempt_number', 
        'cycle_number',
        'score_percent', 
        'is_passed',
        'attempted_at'
    )
    list_filter = ('is_passed', 'attempt_number', 'cycle_number', 'attempted_at')
    search_fields = ('user__username', 'focus__focus_title')
    readonly_fields = [f.name for f in GrammarPracticeAttempt._meta.fields]
    date_hierarchy = 'attempted_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GrammarTestAttempt)
class GrammarTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'focus', 
        'attempt_number', 
        'cycle_number',
        'score_percent', 
        'is_mastered', 
        'created_at'
    )
    list_filter = ('is_mastered', 'attempt_number', 'cycle_number', 'created_at')
    search_fields = ('user__username', 'focus__focus_title')
    readonly_fields = [f.name for f in GrammarTestAttempt._meta.fields]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Student', {
            'fields': ('user', 'focus')
        }),
        ('Attempt Info', {
            'fields': ('attempt_number', 'cycle_number', 'created_at')
        }),
        ('Results', {
            'fields': ('score_percent', 'is_mastered', 'correct_answers', 'total_questions')
        }),
        ('Snapshot', {
            'fields': ('questions_snapshot',),
            'classes': ('collapse',),
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# TEMPORARILY COMMENT OUT to allow migrations
# @admin.register(GrammarQuestionAttempt)
# class GrammarQuestionAttemptAdmin(admin.ModelAdmin):
#     list_display = (
#         'user', 
#         'question_link', 
#         'is_correct', 
#         'attempt_number',
#         'cycle_number',
#         'attempted_at'
#     )
#     list_filter = ('is_correct', 'attempt_number', 'cycle_number', 'attempted_at')
#     search_fields = ('user__username', 'question__question_text')
#     readonly_fields = [f.name for f in GrammarQuestionAttempt._meta.fields]
#     date_hierarchy = 'attempted_at'
#     
#     def question_link(self, obj):
#         url = reverse('admin:content_grammarquestion_change', args=[obj.question.id])
#         return format_html('<a href="{}">Q{}</a>', url, obj.question.id)
#     question_link.short_description = 'Question'
#     
#     def has_add_permission(self, request):
#         return False
#     
#     def has_delete_permission(self, request, obj=None):
#         return False