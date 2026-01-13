from django.contrib import admin
from ..models import StudentVocabMastery

@admin.register(StudentVocabMastery)
class StudentVocabMasteryAdmin(admin.ModelAdmin):
    list_display = ("student_id", "vocab_item", "mastery_level", "last_updated")
    list_filter = ("mastery_level",)
    search_fields = ("student_id", "vocab_item__word")