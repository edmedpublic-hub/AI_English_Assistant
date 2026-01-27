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
    search_fields = ("word", "meaning", "urdu")
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


# -----------------------------
# Analytics (read-only)
# -----------------------------
@admin.register(VocabularyAttempt)
class VocabularyAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "vocab_item", "is_correct", "timestamp")
    ordering = ("-timestamp",)
    readonly_fields = [f.name for f in VocabularyAttempt._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentVocabMastery)
class StudentVocabMasteryAdmin(admin.ModelAdmin):
    list_display = ("student_id", "vocab_item", "mastery_level", "last_updated")
    ordering = ("-last_updated",)
    search_fields = ("student_id", "vocab_item__word")
    readonly_fields = [f.name for f in StudentVocabMastery._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False