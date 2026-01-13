from django.contrib import admin
from ..models import Unit, Lesson, LessonChunk, VocabularyItem, WritingTask, GrammarPoint, ComprehensionQuestion

class UnitInline(admin.TabularInline):
    model = Unit
    extra = 1

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1

class LessonChunkInline(admin.TabularInline):
    model = LessonChunk
    extra = 1
    fields = ("order", "english_text", "translated_text")
    ordering = ("order",)

class VocabularyInline(admin.TabularInline):
    model = VocabularyItem
    extra = 1
    fields = ("word", "part_of_speech", "meaning", "urdu")

class WritingTaskInline(admin.TabularInline):
    model = WritingTask
    extra = 1

class GrammarPointInline(admin.TabularInline):
    model = GrammarPoint
    extra = 1

class ComprehensionInline(admin.TabularInline):
    model = ComprehensionQuestion
    extra = 1