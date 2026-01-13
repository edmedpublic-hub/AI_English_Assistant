from django.contrib import admin
from ..models import PronunciationAttempt

@admin.register(PronunciationAttempt)
class PronunciationAdmin(admin.ModelAdmin):
    list_display = ("student_id", "chunk", "ai_score", "timestamp")