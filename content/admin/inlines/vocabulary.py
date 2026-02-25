# content/admin/inlines/vocabulary.py

"""
Admin inline classes for the Vocabulary domain.
Provides nested editing interfaces for vocabulary items and mastery tracking.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from content.models.vocabulary import VocabularyItem
from content.models.vocabulary import StudentVocabMastery


# ============================================================
# CHUNK VOCABULARY INLINE (Main inline expected by core.py)
# ============================================================

class ChunkVocabularyInline(admin.TabularInline):
    """
    Appears inside LessonChunk admin.
    Main vocabulary authoring surface for chunks.
    This is the inline expected by content.admin.core.
    """
    model = VocabularyItem
    extra = 1
    min_num = 0
    max_num = 20  # Reasonable limit per chunk
    verbose_name = "Vocabulary Item"
    verbose_name_plural = "Vocabulary Items"
    
    fields = (
        "word",
        "part_of_speech",
        "urdu",
        "meaning",
        "synonyms",
        "antonyms",
        "example_sentence",
        "item_preview",
    )
    
    readonly_fields = ("item_preview",)
    autocomplete_fields = ("lesson", "chunk")
    ordering = ("word",)
    
    def item_preview(self, obj):
        """Show a preview of the vocabulary item with mastery stats"""
        if not obj.pk:
            return "Preview available after saving"
        
        html = f"""
        <div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 0.9em; border-left: 4px solid #6f42c1;">
            <p><strong>Word:</strong> {obj.word} <em>({obj.get_part_of_speech_display()})</em></p>
        """
        
        if obj.meaning:
            html += f"<p><strong>Meaning:</strong> {obj.meaning[:100]}</p>"
        
        if obj.urdu:
            html += f"<p><strong>اردو:</strong> {obj.urdu}</p>"
        
        if obj.synonyms:
            html += f"<p><strong>Synonyms:</strong> {obj.synonyms[:100]}</p>"
        
        if obj.antonyms:
            html += f"<p><strong>Antonyms:</strong> {obj.antonyms[:100]}</p>"
        
        if obj.example_sentence:
            html += f"<p><strong>Example:</strong> <em>“{obj.example_sentence[:100]}”</em></p>"
        
        # Add mastery stats if the item exists in database
        if obj.pk:
            mastery_count = StudentVocabMastery.objects.filter(
                vocab_item=obj,
                mastery_level='mastered'
            ).count()
            
            if mastery_count > 0:
                html += f'<p style="color: green;">✓ Mastered by {mastery_count} student(s)</p>'
        
        html += "</div>"
        
        return format_html(html)
    item_preview.short_description = "Preview"
    
    def get_fieldsets(self, request, obj=None):
        """Dynamically show/hide fields based on context"""
        fieldsets = super().get_fieldsets(request, obj)
        return fieldsets


# ============================================================
# VOCABULARY ITEM INLINE (Your existing inline)
# ============================================================

class VocabularyItemInline(admin.TabularInline):
    """
    Allows editing vocabulary directly inside LessonChunk.
    This is your main authoring UX.
    """
    model = VocabularyItem
    extra = 1
    min_num = 0
    max_num = 20  # Reasonable limit per chunk
    
    fields = (
        "word",
        "part_of_speech",
        "urdu",
        "meaning",
        "synonyms",
        "antonyms",
        "example_sentence",
        "item_preview",
    )
    
    readonly_fields = ("item_preview",)
    autocomplete_fields = ("lesson", "chunk")
    ordering = ("word",)
    
    def item_preview(self, obj):
        """Show a preview of the vocabulary item with mastery stats"""
        if not obj.pk:
            return "Preview available after saving"
        
        html = f"""
        <div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 0.9em;">
            <p><strong>Word:</strong> {obj.word} <em>({obj.get_part_of_speech_display()})</em></p>
        """
        
        if obj.meaning:
            html += f"<p><strong>Meaning:</strong> {obj.meaning[:100]}</p>"
        
        if obj.urdu:
            html += f"<p><strong>اردو:</strong> {obj.urdu}</p>"
        
        if obj.synonyms:
            html += f"<p><strong>Synonyms:</strong> {obj.synonyms[:100]}</p>"
        
        if obj.antonyms:
            html += f"<p><strong>Antonyms:</strong> {obj.antonyms[:100]}</p>"
        
        if obj.example_sentence:
            html += f"<p><strong>Example:</strong> <em>“{obj.example_sentence[:100]}”</em></p>"
        
        # Add mastery stats if the item exists in database
        if obj.pk:
            mastery_count = StudentVocabMastery.objects.filter(
                vocab_item=obj,
                mastery_level='mastered'
            ).count()
            
            if mastery_count > 0:
                html += f'<p style="color: green;">✓ Mastered by {mastery_count} student(s)</p>'
        
        html += "</div>"
        
        return format_html(html)
    item_preview.short_description = "Preview"
    
    def get_fieldsets(self, request, obj=None):
        """Dynamically show/hide fields based on context"""
        fieldsets = super().get_fieldsets(request, obj)
        return fieldsets


# ============================================================
# VOCABULARY ITEM QUICK INLINE (Your existing quick inline)
# ============================================================

class VocabularyItemQuickInline(admin.TabularInline):
    """
    Simplified inline for quick vocabulary entry.
    Use this when you want a minimal interface.
    """
    model = VocabularyItem
    extra = 1
    min_num = 0
    max_num = 20
    
    fields = (
        "word",
        "part_of_speech",
        "urdu",
        "quick_preview",
    )
    
    readonly_fields = ("quick_preview",)
    autocomplete_fields = ("lesson", "chunk")
    ordering = ("word",)
    
    def quick_preview(self, obj):
        """Minimal preview for quick entry mode"""
        if not obj.pk:
            return ""
        
        preview = f"<span style='color: #666;'>{obj.word}"
        if obj.urdu:
            preview += f" | اردو: {obj.urdu}"
        preview += "</span>"
        
        return format_html(preview)
    quick_preview.short_description = "Preview"


# ============================================================
# STUDENT MASTERY INLINE (Read-only analytics)
# ============================================================

class StudentVocabMasteryInline(admin.TabularInline):
    """
    Read-only inline for student mastery records within VocabularyItem admin.
    Shows which students have mastered this item.
    """
    model = StudentVocabMastery
    extra = 0
    readonly_fields = ['user', 'mastery_level', 'accuracy_percentage', 'total_attempts', 'correct_attempts', 'last_practiced']
    fields = ['user', 'mastery_level', 'accuracy_percentage', 'total_attempts', 'last_practiced']
    ordering = ['-last_practiced']
    can_delete = False
    verbose_name = "Student Mastery Record"
    verbose_name_plural = "Student Mastery Records"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def accuracy_percentage(self, obj):
        """Display accuracy with color coding"""
        accuracy = obj.accuracy_percentage
        color = '#28a745' if accuracy >= 80 else '#fd7e14' if accuracy >= 50 else '#dc3545'
        return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, accuracy)
    accuracy_percentage.short_description = "Accuracy"


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'ChunkVocabularyInline',        # Added this - fixes the import error
    'VocabularyItemInline',
    'VocabularyItemQuickInline',
    'StudentVocabMasteryInline',
]