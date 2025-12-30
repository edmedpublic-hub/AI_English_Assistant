from rest_framework import serializers
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
#  LESSON CHUNKS
# -------------------------------
class LessonChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonChunk
        fields = [
            "id",
            "order",
            "english_text",
            "translated_text",
            "audio_file",
            "translated_audio_file",
        ]


# -------------------------------
#  VOCABULARY
# -------------------------------
class VocabularyItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyItem
        fields = [
            "id",
            "word",
            "part_of_speech",
            "urdu",
            "meaning",
            "synonyms",
            "antonyms",
            "example_sentence",
        ]


# -------------------------------
#  COMPREHENSION QUESTIONS
# -------------------------------
class ComprehensionQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComprehensionQuestion
        fields = ["id", "question", "answer"]


# -------------------------------
#  GRAMMAR POINTS
# -------------------------------
class GrammarPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarPoint
        fields = ["id", "title", "explanation", "examples"]


# -------------------------------
#  WRITING TASKS
# -------------------------------
class WritingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingTask
        fields = ["id", "prompt", "difficulty"]


# -------------------------------
#  LESSON (NESTED)
# -------------------------------
class LessonSerializer(serializers.ModelSerializer):
    chunks = LessonChunkSerializer(many=True, read_only=True)
    vocab_items = VocabularyItemSerializer(many=True, read_only=True)
    comprehension_questions = ComprehensionQuestionSerializer(many=True, read_only=True)
    grammar_points = GrammarPointSerializer(many=True, read_only=True)
    writing_tasks = WritingTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "number",
            "english_text",
            "translated_text",
            "audio_file",
            "chunks",
            "vocab_items",
            "comprehension_questions",
            "grammar_points",
            "writing_tasks",
        ]


# -------------------------------
#  UNITS (OPTIONAL NESTED LESSONS)
# -------------------------------
class UnitSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Unit
        fields = ["id", "title", "number", "lessons"]


# -------------------------------
#  TEXTBOOK (OPTIONAL NESTED UNITS)
# -------------------------------
class TextbookSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)

    class Meta:
        model = Textbook
        fields = ["id", "title", "class_level", "description", "units"]


# =====================================================
#  ATTEMPTS  (WRITE ONLY FOR STUDENTS, READ SAFE)
# =====================================================

class VocabularyAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyAttempt
        fields = ["id", "student_id", "vocab_item", "is_correct", "timestamp"]
        read_only_fields = ["timestamp"]


class SentenceAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentenceAttempt
        fields = ["id", "student_id", "writing_task", "sentence", "ai_score", "feedback", "timestamp"]
        read_only_fields = ["ai_score", "feedback", "timestamp"]


class GrammarAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarAttempt
        fields = ["id", "student_id", "grammar_point", "is_correct", "timestamp"]
        read_only_fields = ["timestamp"]


class ComprehensionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComprehensionAttempt
        fields = ["id", "student_id", "question", "answer", "is_correct", "timestamp"]
        read_only_fields = ["timestamp"]


class PronunciationAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PronunciationAttempt
        fields = ["id", "student_id", "chunk", "recording", "ai_feedback", "ai_score", "timestamp"]
        read_only_fields = ["ai_feedback", "ai_score", "timestamp"]
