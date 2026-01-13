from django.contrib import admin
from ..models import Unit
from .inlines import LessonInline

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("title", "textbook", "number")
    list_filter = ("textbook",)
    search_fields = ("title",)
    ordering = ("textbook", "number")
    inlines = [LessonInline]