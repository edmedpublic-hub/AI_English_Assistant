from django.contrib import admin
from ..models.vocabulary import VocabularyItem


@admin.register(VocabularyItem)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ("word", "lesson", "part_of_speech")
    list_filter = ("part_of_speech", "lesson__unit__textbook")
    search_fields = ("word", "meaning", "urdu")
    ordering = ("lesson", "word")