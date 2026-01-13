from django.contrib import admin
from ..models import ComprehensionAttempt

@admin.register(ComprehensionAttempt)
class ComprehensionAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "question", "is_correct", "timestamp")