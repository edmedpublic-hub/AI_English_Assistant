from django.contrib import admin
from django.utils.html import format_html
from content.models.grammar import ChunkGrammarFocus, GrammarQuestion


class ChunkGrammarFocusInline(admin.StackedInline):
    """
    Appears inside LessonChunk.
    Primary grammar authoring surface.
    Shows grammar focuses with their questions.
    """
    model = ChunkGrammarFocus
    extra = 0
    min_num = 0
    max_num = 3  # Maximum 3 focuses per chunk
    show_change_link = True
    
    fieldsets = (
        ('Grammar Focus', {
            'fields': (
                'concept',
                'focus_title',
                'focus_description',
                'depth_level',
                'sequence_order',
                'focus_preview',
            )
        }),
    )
    
    readonly_fields = ('focus_preview',)
    ordering = ('sequence_order',)
    autocomplete_fields = ('concept',)
    
    def focus_preview(self, obj):
        """Show quick stats about this focus"""
        if not obj.pk:
            return "Not saved yet"
        
        # Count questions
        question_count = obj.questions.count()
        
        # Get concept info
        concept_name = obj.concept.name if obj.concept else "No concept"
        
        # Format the preview
        html = f"""
        <div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px;">
            <strong>Concept:</strong> {concept_name}<br>
            <strong>Questions:</strong> {question_count}
        </div>
        """
        
        if question_count > 0:
            # Add a link to view questions
            html += f'<div style="margin-top: 5px;">✓ Has {question_count} question(s)</div>'
        else:
            html += '<div style="color: #856404; background-color: #fff3cd; padding: 4px; margin-top: 5px; border-radius: 4px;">⚠️ No questions yet</div>'
        
        return format_html(html)
    focus_preview.short_description = "Focus Overview"


class GrammarQuestionInline(admin.TabularInline):
    """
    Questions are edited inside ChunkGrammarFocus admin.
    Now includes better validation and preview.
    """
    model = GrammarQuestion
    extra = 1
    min_num = 0
    max_num = 10  # Reasonable limit per focus
    
    fields = (
        'question_text',
        'question_type',
        'difficulty',
        'options',
        'correct_answer',
        'explanation',
        'question_preview',
    )
    
    readonly_fields = ('question_preview',)
    ordering = ('difficulty', 'id')
    
    def question_preview(self, obj):
        """Show a preview of the question with correct answer highlighted"""
        if not obj.pk:
            return "Preview available after saving"
        
        preview = f"<strong>Question:</strong> {obj.question_text[:100]}"
        if len(obj.question_text) > 100:
            preview += "..."
        
        preview += "<br>"
        
        if obj.question_type == 'mcq' and obj.options:
            options = obj.get_options_list()
            preview += "<strong>Options:</strong><br>"
            for opt in options:
                if opt == obj.correct_answer:
                    preview += f"✓ <span style='color: green;'>{opt}</span><br>"
                else:
                    preview += f"• {opt}<br>"
        else:
            preview += f"<strong>Correct Answer:</strong> {obj.correct_answer}"
        
        if obj.explanation:
            preview += f"<br><small><em>Explanation: {obj.explanation[:60]}</em></small>"
        
        return format_html(preview)
    question_preview.short_description = "Preview"
    
    def get_fields(self, request, obj=None):
        """Dynamically show/hide options field based on question type"""
        fields = list(super().get_fields(request, obj))
        
        # You could add JavaScript to hide/show options based on question_type
        # But that requires custom JS - keeping it simple for now
        
        return fields
    
    class Media:
        """Optional: Add JavaScript for dynamic form behavior"""
        js = ('admin/js/grammar_question_inline.js',)  # You'd create this file