from django.contrib import admin
from ..models import GrammarPoint

@admin.register(GrammarPoint)
class GrammarPointAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson")
    search_fields = ("title",)