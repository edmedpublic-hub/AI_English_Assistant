from django.contrib import admin
from .models import (
    Textbook,
    Unit,
    Lesson,
    LessonChunk,
    VocabularyItem,
    VocabularyAttempt,
    WritingTask,
    SentenceAttempt,
    GrammarPoint,
    GrammarAttempt,
    ComprehensionQuestion,
    ComprehensionAttempt,
    PronunciationAttempt,
)

# -------------------------------
# INLINE SETUPS
# -------------------------------

class UnitInline(admin.TabularInline):
    model = Unit
    extra = 0
    ordering = ("number",)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    ordering = ("number",)


class LessonChunkInline(admin.TabularInline):
    model = LessonChunk
    extra = 0
    ordering = ("order",)
    fields = (
        "order",
        "english_text",
        "translated_text",
        "audio_file",
        "translated_audio_file",
    )


class VocabularyInline(admin.TabularInline):
    model = VocabularyItem
    extra = 0


class WritingTaskInline(admin.TabularInline):
    model = WritingTask
    extra = 0


class ComprehensionQuestionInline(admin.TabularInline):
    model = ComprehensionQuestion
    extra = 0


# -------------------------------
# ADMIN REGISTRATION
# -------------------------------

@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display = ("title", "class_level")
    search_fields = ("title", "class_level")
    inlines = [UnitInline]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("title", "number", "textbook")
    list_filter = ("textbook",)
    search_fields = ("title",)
    ordering = ("textbook", "number")
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "number", "unit")
    list_filter = ("unit",)
    search_fields = ("title", "english_text")
    ordering = ("unit", "number")
    inlines = [
        LessonChunkInline,
        VocabularyInline,
        ComprehensionQuestionInline,
        WritingTaskInline,
    ]


@admin.register(LessonChunk)
class LessonChunkAdmin(admin.ModelAdmin):
    list_display = ("lesson", "order")
    ordering = ("lesson", "order")
    search_fields = ("english_text", "translated_text")


@admin.register(VocabularyItem)
class VocabularyItemAdmin(admin.ModelAdmin):
    list_display = ("word", "part_of_speech", "lesson")
    list_filter = ("part_of_speech", "lesson")
    search_fields = ("word", "meaning")


@admin.register(VocabularyAttempt)
class VocabularyAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "vocab_item", "is_correct", "timestamp")
    list_filter = ("is_correct", "timestamp")
    search_fields = ("student_id", "vocab_item__word")


@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = ("lesson", "difficulty")
    search_fields = ("prompt",)
    list_filter = ("difficulty", "lesson")


@admin.register(SentenceAttempt)
class SentenceAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "writing_task", "ai_score", "timestamp")
    list_filter = ("writing_task", "timestamp")
    search_fields = ("student_id", "sentence")


@admin.register(GrammarPoint)
class GrammarPointAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson")
    search_fields = ("title", "explanation")
    list_filter = ("lesson",)


@admin.register(GrammarAttempt)
class GrammarAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "grammar_point", "is_correct", "timestamp")
    list_filter = ("is_correct", "timestamp")
    search_fields = ("student_id", "grammar_point__title")


@admin.register(ComprehensionQuestion)
class ComprehensionQuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "lesson")
    search_fields = ("question", "answer")
    list_filter = ("lesson",)


@admin.register(ComprehensionAttempt)
class ComprehensionAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "question", "is_correct", "timestamp")
    list_filter = ("is_correct", "timestamp")
    search_fields = ("student_id", "question__question")


@admin.register(PronunciationAttempt)
class PronunciationAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "chunk", "ai_score", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("student_id",)
