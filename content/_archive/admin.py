from django.contrib import admin
from .models import (
    Textbook, Unit, Lesson, LessonChunk,
    VocabularyItem, VocabularyAttempt, StudentVocabMastery,
    WritingTask, SentenceAttempt,
    GrammarPoint, GrammarAttempt,
    ComprehensionQuestion, ComprehensionAttempt,
    PronunciationAttempt
)
import spacy

# ============================================================
# INLINE DEFINITIONS
# ============================================================

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
    
nlp = spacy.load("en_core_web_sm") 
def generate_vocab(modeladmin, request, queryset): 
    """ 
    Admin action: generate vocabulary for selected LessonChunks 
    """ 
    for chunk in queryset: 
        doc = nlp(chunk.english_text) 
        candidates = [t for t in doc if t.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]] 
        for token in candidates[:7]: 
            VocabularyItem.objects.get_or_create( 
                lesson=chunk.lesson, 
                chunk=chunk, 
                word=token.text, 
                part_of_speech=token.pos_.lower() 
                )
            modeladmin.message_user(request, "Vocabulary generated for selected chunks.") 
            generate_vocab.short_description = "Generate vocabulary for selected chunks"


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


# ============================================================
# ADMIN REGISTRATION
# ============================================================

@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display = ("title", "class_level")
    search_fields = ("title", "class_level")
    inlines = [UnitInline]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("title", "textbook", "number")
    list_filter = ("textbook",)
    search_fields = ("title",)
    ordering = ("textbook", "number")
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "unit", "number")
    list_filter = ("unit__textbook", "unit")
    search_fields = ("title", "english_text")
    ordering = ("unit", "number")
    inlines = [
        LessonChunkInline,
        VocabularyInline,
        WritingTaskInline,
        GrammarPointInline,
        ComprehensionInline,
    ]


@admin.register(LessonChunk)
class LessonChunkAdmin(admin.ModelAdmin):
    list_display = ("lesson", "order", "english_text")
    ordering = ("lesson", "order")
    actions = [generate_vocab]


@admin.register(VocabularyItem)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ("word", "lesson", "part_of_speech")
    list_filter = ("part_of_speech", "lesson__unit__textbook")
    search_fields = ("word", "meaning", "urdu")
    ordering = ("lesson", "word")


@admin.register(VocabularyAttempt)
class VocabularyAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "vocab_item", "is_correct", "timestamp")
    list_filter = ("is_correct",)
    search_fields = ("student_id", "vocab_item__word")


@admin.register(StudentVocabMastery)
class StudentVocabMasteryAdmin(admin.ModelAdmin):
    list_display = ("student_id", "vocab_item", "mastery_level", "last_updated")
    list_filter = ("mastery_level",)
    search_fields = ("student_id", "vocab_item__word")


@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = ("lesson", "difficulty")
    list_filter = ("difficulty",)


@admin.register(SentenceAttempt)
class SentenceAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "writing_task", "ai_score", "timestamp")
    search_fields = ("student_id", "sentence")


@admin.register(GrammarPoint)
class GrammarPointAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson")
    search_fields = ("title",)


@admin.register(GrammarAttempt)
class GrammarAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "grammar_point", "is_correct", "timestamp")


@admin.register(ComprehensionQuestion)
class ComprehensionAdmin(admin.ModelAdmin):
    list_display = ("lesson", "question")
    search_fields = ("question",)


@admin.register(ComprehensionAttempt)
class ComprehensionAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_id", "question", "is_correct", "timestamp")


@admin.register(PronunciationAttempt)
class PronunciationAdmin(admin.ModelAdmin):
    list_display = ("student_id", "chunk", "ai_score", "timestamp")
