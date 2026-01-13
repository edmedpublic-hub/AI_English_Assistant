from django.contrib import admin
from ..models import WritingTask

@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = ("lesson", "difficulty")
    list_filter = ("difficulty",)