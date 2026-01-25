from django.contrib import admin
from ..models.core import Textbook
from .inlines import UnitInline


@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display = ("title", "class_level")
    search_fields = ("title", "class_level")
    inlines = [UnitInline]