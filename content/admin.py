from django.contrib import admin
from .models import (
    Textbook,
    Unit,
    Lesson,
    VocabularyItem,
    WritingTask,
    SentenceAttempt,
    GrammarPoint,
    ComprehensionQuestion,
    LessonChunk,   # ✅ new model
)

# -------------------------------
# INLINE SETUPS
# -------------------------------

class UnitInline(admin.TabularInline):
    model = Unit
    extra = 0


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


class VocabularyInline(admin.TabularInline):
    model = VocabularyItem
    extra = 0


class WritingTaskInline(admin.TabularInline):
    model = WritingTask
    extra = 0


class ComprehensionQuestionInline(admin.TabularInline):
    model = ComprehensionQuestion
    extra = 0


class LessonChunkInline(admin.TabularInline):   # ✅ new inline
    model = LessonChunk
    extra = 0
    fields = ("order", "english_text", "urdu_translation", "english_audio", "urdu_audio")


# -------------------------------
# ADMIN REGISTRATION
# -------------------------------

@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display = ("title", "class_level")
    inlines = [UnitInline]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("title", "number", "textbook")
    list_filter = ("textbook",)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "number", "unit")
    list_filter = ("unit",)
    search_fields = ("title", "english_text")
    inlines = [
        VocabularyInline,
        ComprehensionQuestionInline,
        WritingTaskInline,
        LessonChunkInline,   # ✅ chunks inline under lesson
    ]


@admin.register(VocabularyItem)
class VocabularyItemAdmin(admin.ModelAdmin):
    list_display = ("word", "lesson")
    list_filter = ("part_of_speech", "lesson")
    search_fields = ("word",)


@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = ("lesson", "difficulty")
    search_fields = ("prompt",)


@admin.register(SentenceAttempt)
class SentenceAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "writing_task", "ai_score", "timestamp")
    list_filter = ("writing_task",)
    search_fields = ("student_id", "sentence")


@admin.register(GrammarPoint)
class GrammarPointAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson")
    search_fields = ("title", "explanation")
    list_filter = ("lesson",)


@admin.register(ComprehensionQuestion)
class ComprehensionQuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "lesson")
    search_fields = ("question", "answer")
    list_filter = ("lesson",)