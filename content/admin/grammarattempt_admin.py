from django.contrib import admin
from ..models import GrammarAttempt

@admin.register(GrammarAttempt)
class GrammarAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "grammar_point", "is_correct", "timestamp")