from django.contrib import admin
from ..models.comprehension import ComprehensionQuestion


@admin.register(ComprehensionQuestion)
class ComprehensionAdmin(admin.ModelAdmin):
    list_display = ("lesson", "question")
    search_fields = ("question",)