from django.contrib import admin
from .models import TranslationTextbook, TranslationUnit, TranslationLesson

@admin.register(TranslationTextbook)
class TranslationTextbookAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'is_active', 'published', 'created_at', 'updated_at')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title', 'description')
    list_filter = ('language', 'is_active', 'published')


@admin.register(TranslationUnit)
class TranslationUnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit_number', 'textbook', 'created_at', 'updated_at')
    list_filter = ('textbook',)
    search_fields = ('title',)
    ordering = ('textbook', 'unit_number')


@admin.register(TranslationLesson)
class TranslationLessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson_number', 'unit', 'published', 'is_active', 'created_at', 'updated_at')
    list_filter = ('unit', 'published', 'is_active')
    search_fields = ('title', 'english_chunk', 'urdu_chunk')
    ordering = ('unit', 'lesson_number')
