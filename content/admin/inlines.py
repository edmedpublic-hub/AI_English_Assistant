from django.contrib import admin
from ..models.core import Unit, Lesson, LessonChunk
from ..models.vocabulary import VocabularyItem
from ..models.writing import WritingTask


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