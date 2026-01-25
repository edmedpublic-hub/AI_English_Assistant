from django.contrib import admin
from ..models.writing import WritingTask


@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = ("lesson", "difficulty")
    list_filter = ("difficulty",)