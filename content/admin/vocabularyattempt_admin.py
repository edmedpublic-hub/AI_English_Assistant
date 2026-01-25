from django.contrib import admin
from ..models.vocabulary import VocabularyAttempt


@admin.register(VocabularyAttempt)
class VocabularyAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "vocab_item", "is_correct", "timestamp")
    list_filter = ("is_correct",)
    search_fields = ("student_id", "vocab_item__word")