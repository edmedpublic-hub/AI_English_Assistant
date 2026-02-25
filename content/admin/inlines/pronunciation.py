# content/admin/inlines/pronunciation.py

"""
Admin inline classes for the Pronunciation domain.
Provides nested editing interfaces for pronunciation focuses and attempt tracking.
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from content.models.pronunciation import (
    PronunciationFocus, PronunciationAttempt, PronunciationMastery
)


# ============================================================
# CHUNK PRONUNCIATION FOCUS INLINE (Main inline expected by core.py)
# ============================================================

class ChunkPronunciationFocusInline(admin.TabularInline):
    """
    Appears inside LessonChunk admin.
    Primary pronunciation authoring surface for chunk-level pronunciation focuses.
    This is the inline expected by content.admin.core.
    """
    model = PronunciationFocus
    extra = 0
    min_num = 0
    max_num = 3  # Maximum 3 focuses per chunk
    verbose_name = "Pronunciation Focus"
    verbose_name_plural = "Pronunciation Focuses"
    
    fields = [
        'focus_title',
        'focus_description',
        'sequence_order',
        'focus_preview',
    ]
    
    readonly_fields = ['focus_preview']
    
    def focus_preview(self, obj):
        """Show number of attempts and mastery stats if any exist"""
        if not obj.pk:  # New object
            return "Not saved yet"
        
        # Count attempts
        attempt_count = obj.attempts.count()
        
        # Count mastered students (if any)
        mastered_count = PronunciationMastery.objects.filter(
            focus=obj,
            is_mastered=True
        ).count()
        
        return format_html(
            '<span style="color: {};">{} attempts • {} mastered</span>',
            'green' if mastered_count > 0 else 'gray',
            attempt_count,
            mastered_count
        )
    focus_preview.short_description = "Statistics"


# ============================================================
# PRONUNCIATION FOCUS INLINE (Your existing inline - kept for backward compatibility)
# ============================================================

class PronunciationFocusInline(admin.TabularInline):
    """
    Inline admin for PronunciationFocus within LessonChunk admin.
    """
    model = PronunciationFocus
    extra = 0
    min_num = 0
    max_num = 3  # Maximum 3 focuses per chunk
    
    fields = [
        'focus_title',
        'focus_description',
        'sequence_order',
        'focus_preview',
    ]
    
    readonly_fields = ['focus_preview']
    
    def focus_preview(self, obj):
        """Show number of attempts and mastery stats if any exist"""
        if not obj.pk:  # New object
            return "Not saved yet"
        
        # Count attempts
        attempt_count = obj.attempts.count()
        
        # Count mastered students (if any)
        mastered_count = PronunciationMastery.objects.filter(
            focus=obj,
            is_mastered=True
        ).count()
        
        return format_html(
            '<span style="color: {};">{} attempts • {} mastered</span>',
            'green' if mastered_count > 0 else 'gray',
            attempt_count,
            mastered_count
        )
    focus_preview.short_description = "Statistics"


# ============================================================
# PRONUNCIATION ATTEMPTS INLINE (Your existing inline)
# ============================================================

class PronunciationAttemptInline(admin.TabularInline):
    """
    Inline admin for PronunciationAttempt within PronunciationFocus admin.
    """
    model = PronunciationAttempt
    extra = 0
    readonly_fields = [
        'user',
        'attempt_number',
        'cycle_number',
        'ai_score',
        'ai_feedback',
        'attempt_type',
        'created_at',
        'recording_link',
    ]
    
    fields = [
        'user',
        'attempt_number',
        'cycle_number',
        'ai_score',
        'attempt_type',
        'recording_link',
        'created_at',
    ]
    
    def recording_link(self, obj):
        """Link to download the recording if it exists"""
        if obj.recording:
            return format_html(
                '<a href="{}" target="_blank">Download</a>',
                obj.recording.url
            )
        return "No recording"
    recording_link.short_description = "Recording"
    
    def has_add_permission(self, request, obj=None):
        """Prevent adding attempts manually through admin"""
        return False


# ============================================================
# PRONUNCIATION MASTERY INLINE (Your existing inline)
# ============================================================

class PronunciationMasteryInline(admin.TabularInline):
    """
    Inline admin for PronunciationMastery within PronunciationFocus admin.
    """
    model = PronunciationMastery
    extra = 0
    readonly_fields = [
        'user',
        'total_attempts',
        'best_score',
        'last_score',
        'is_mastered',
        'last_attempted',
        'mastered_at',
    ]
    
    fields = [
        'user',
        'is_mastered',
        'best_score',
        'last_score',
        'total_attempts',
        'last_attempted',
    ]
    
    def has_add_permission(self, request, obj=None):
        """Prevent adding mastery records manually"""
        return False


# ============================================================
# DETAILED ATTEMPT INLINE (Stacked layout for more detail)
# ============================================================

class PronunciationAttemptDetailInline(admin.StackedInline):
    """
    Detailed view of pronunciation attempts with AI feedback.
    Best used in PronunciationFocus admin.
    """
    model = PronunciationAttempt
    extra = 0
    fields = [
        'user_link',
        'attempt_number',
        'cycle_number',
        'ai_score',
        'is_passed',
        'attempt_type',
        'ai_feedback',
        'recording_link',
        'created_at'
    ]
    readonly_fields = [
        'user_link',
        'attempt_number',
        'cycle_number',
        'ai_score',
        'is_passed',
        'attempt_type',
        'ai_feedback',
        'recording_link',
        'created_at'
    ]
    ordering = ['-created_at']
    can_delete = False
    
    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def recording_link(self, obj):
        """Link to download the recording if it exists"""
        if obj.recording:
            return format_html(
                '<a href="{}" target="_blank">🎤 Listen</a>',
                obj.recording.url
            )
        return "No recording"
    recording_link.short_description = "Recording"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'ChunkPronunciationFocusInline',     # Added this - fixes the import error
    'PronunciationFocusInline',          # Your existing inline
    'PronunciationAttemptInline',
    'PronunciationMasteryInline',
    'PronunciationAttemptDetailInline',
]