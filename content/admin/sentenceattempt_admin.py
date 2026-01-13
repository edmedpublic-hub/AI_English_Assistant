from django.contrib import admin
from ..models import SentenceAttempt

@admin.register(SentenceAttempt)
class SentenceAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "writing_task", "ai_score", "timestamp")
    search_fields = ("student_id", "sentence")