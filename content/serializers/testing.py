from rest_framework import serializers

from content.models.testing import (
    VocabularyTestSession,
    VocabularyTestQuestion,
    VocabularyTestAnswer,
    VocabularyTestAttempt,
)


# ============================================================
# VOCABULARY TEST SESSION
# ============================================================

class VocabularyTestSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyTestSession
        fields = [
            "id",
            "student_id",
            "chunk",
            "started_at",
            "completed_at",
            "total_questions",
            "correct_answers",
            "score_percentage",
            "passed",
        ]
        read_only_fields = [
            "started_at",
            "completed_at",
            "correct_answers",
            "score_percentage",
            "passed",
        ]


# ============================================================
# TEST QUESTIONS (GENERATED PER SESSION)
# ============================================================

class VocabularyTestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyTestQuestion
        fields = [
            "id",
            "session",
            "vocab_item",
            "question_type",
            "question_text",
            "options",
            "correct_answer",
            "order",
        ]


# ============================================================
# STUDENT ANSWERS
# ============================================================

class VocabularyTestAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyTestAnswer
        fields = [
            "id",
            "question",
            "selected_option",
            "is_correct",
            "answered_at",
            "time_taken_seconds",
        ]
        read_only_fields = ["is_correct", "answered_at"]


# ============================================================
# LEGACY / AGGREGATE ATTEMPT MODEL
# ============================================================

class VocabularyTestAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyTestAttempt
        fields = [
            "id",
            "user",
            "lesson",
            "chunk",
            "score_percent",
            "correct_answers",
            "total_questions",
            "questions_data",
            "created_at",
        ]
        read_only_fields = ["created_at"]