# content/admin/vocabulary.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from content.models.vocabulary import (
    VocabularyItem,
    VocabularyAttempt,
    StudentVocabMastery,
)


# -----------------------------
# Vocabulary authoring
# -----------------------------
@admin.register(VocabularyItem)
class VocabularyItemAdmin(admin.ModelAdmin):
    list_display = (
        "word", 
        "part_of_speech", 
        "lesson_link", 
        "chunk_link",
        "mastery_count"
    )
    list_filter = ("part_of_speech", "lesson__unit__textbook")
    search_fields = ("word", "meaning", "urdu", "example_sentence")
    ordering = ("lesson", "word")
    autocomplete_fields = ("lesson", "chunk")
    readonly_fields = ("created_at", "updated_at", "mastery_stats")

    fieldsets = (
        ("Core", {
            "fields": ("lesson", "chunk", "word", "part_of_speech")
        }),
        ("Meaning", {
            "fields": ("meaning", "urdu")
        }),
        ("Lexical Relations", {
            "fields": ("synonyms", "antonyms")
        }),
        ("Usage", {
            "fields": ("example_sentence",)
        }),
        ("Statistics", {
            "fields": ("mastery_stats",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def lesson_link(self, obj):
        if obj.lesson:
            url = reverse('admin:content_lesson_change', args=[obj.lesson.id])
            return format_html('<a href="{}">{}</a>', url, obj.lesson)
        return "-"
    lesson_link.short_description = "Lesson"
    
    def chunk_link(self, obj):
        if obj.chunk:
            url = reverse('admin:content_lessonchunk_change', args=[obj.chunk.id])
            return format_html('<a href="{}">{}</a>', url, obj.chunk)
        return "-"
    chunk_link.short_description = "Chunk"
    
    def mastery_count(self, obj):
        """Count how many students have mastered this item"""
        count = StudentVocabMastery.objects.filter(
            vocab_item=obj, 
            mastery_level='mastered'
        ).count()
        return count
    mastery_count.short_description = "Mastered by"
    
    def mastery_stats(self, obj):
        """Show detailed mastery statistics"""
        total = StudentVocabMastery.objects.filter(vocab_item=obj).count()
        if total == 0:
            return "No mastery data yet"
        
        levels = {}
        for level, _ in StudentVocabMastery.MASTERY_LEVELS:
            levels[level] = StudentVocabMastery.objects.filter(
                vocab_item=obj, 
                mastery_level=level
            ).count()
        
        html = f"""
        <table style="width:100%">
            <tr><td><strong>Total Students:</strong></td><td>{total}</td></tr>
            <tr><td style="color:green;">✓ Mastered:</td><td>{levels.get('mastered', 0)}</td></tr>
            <tr><td style="color:orange;">⟲ Review:</td><td>{levels.get('review', 0)}</td></tr>
            <tr><td style="color:blue;">📚 Learning:</td><td>{levels.get('learning', 0)}</td></tr>
            <tr><td style="color:gray;">🆕 New:</td><td>{levels.get('new', 0)}</td></tr>
        </table>
        """
        return format_html(html)
    mastery_stats.short_description = "Mastery Distribution"


# -----------------------------
# Analytics (read-only)
# -----------------------------
@admin.register(VocabularyAttempt)
class VocabularyAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user_link", 
        "vocab_item_link", 
        "cycle_number",  # Now uncommented - exists in model
        "is_correct", 
        "session_id",
        "created_at"
    )
    list_filter = ("is_correct", "cycle_number", "created_at")  # Added cycle_number back
    search_fields = ("user__username", "vocab_item__word", "session_id")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in VocabularyAttempt._meta.fields]
    
    fieldsets = (
        ("Student", {
            "fields": ("user", "vocab_item")
        }),
        ("Attempt Details", {
            "fields": ("cycle_number", "session_id", "created_at")  # Added cycle_number back
        }),
        ("Result", {
            "fields": ("is_correct", "time_taken_seconds")
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    
    def vocab_item_link(self, obj):
        url = reverse('admin:content_vocabularyitem_change', args=[obj.vocab_item.id])
        return format_html('<a href="{}">{}</a>', url, obj.vocab_item.word)
    vocab_item_link.short_description = "Word"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentVocabMastery)
class StudentVocabMasteryAdmin(admin.ModelAdmin):
    list_display = (
        "user_link", 
        "vocab_item_link", 
        "mastery_level", 
        "accuracy_display",
        "total_attempts",
        "last_practiced",
        "updated_at"  # Using updated_at (exists in model)
    )
    list_filter = ("mastery_level", "updated_at", "last_practiced")
    search_fields = ("user__username", "vocab_item__word")
    ordering = ("-updated_at",)
    date_hierarchy = "updated_at"  # Now uncommented - exists in model
    readonly_fields = [
        "user", 
        "vocab_item", 
        "mastery_level", 
        "total_attempts",
        "correct_attempts",
        "accuracy_display",
        "last_practiced",
        "created_at",
        "updated_at",
    ]
    
    fieldsets = (
        ("Student", {
            "fields": ("user", "vocab_item")
        }),
        ("Mastery Status", {
            "fields": ("mastery_level", "accuracy_display")
        }),
        ("Attempt Statistics", {
            "fields": ("total_attempts", "correct_attempts", "last_practiced")
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
    
    def vocab_item_link(self, obj):
        url = reverse('admin:content_vocabularyitem_change', args=[obj.vocab_item.id])
        return format_html('<a href="{}">{}</a>', url, obj.vocab_item.word)
    vocab_item_link.short_description = "Word"
    
    def accuracy_display(self, obj):
        accuracy = obj.accuracy_percentage
        color = 'green' if accuracy >= 80 else 'orange' if accuracy >= 50 else 'red'
        return format_html(
            '<span style="color:{};font-weight:bold;">{}%</span>',
            color, accuracy
        )
    accuracy_display.short_description = "Accuracy"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False