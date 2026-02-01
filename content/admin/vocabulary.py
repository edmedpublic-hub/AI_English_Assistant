from django.contrib import admin
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
    list_display = ("word", "part_of_speech", "lesson", "chunk")
    list_filter = ("part_of_speech", "lesson")
    search_fields = ("word", "meaning", "urdu", "example_sentence")
    ordering = ("lesson", "word")

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
    )

    autocomplete_fields = ("lesson", "chunk")  # ✅ ensures smooth linking


# -----------------------------
# Analytics (read-only)
# -----------------------------
@admin.register(VocabularyAttempt)
class VocabularyAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "vocab_item", "is_correct", "timestamp")
    list_filter = ("is_correct", "timestamp")
    search_fields = ("student_id", "vocab_item__word")
    ordering = ("-timestamp",)
    readonly_fields = [f.name for f in VocabularyAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentVocabMastery)
class StudentVocabMasteryAdmin(admin.ModelAdmin):
    list_display = ("student_id", "vocab_item", "mastery_level", "last_updated")
    list_filter = ("mastery_level", "last_updated")
    search_fields = ("student_id", "vocab_item__word")
    ordering = ("-last_updated",)
    readonly_fields = [f.name for f in StudentVocabMastery._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False