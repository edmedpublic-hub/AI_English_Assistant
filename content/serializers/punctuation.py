from rest_framework import serializers

from content.models.punctuation import (
    PunctuationMark,
    PunctuationRule,
    PunctuationExample,
    ChunkPunctuationFocus,
    PunctuationQuestion,
    PunctuationAttempt,
    PunctuationTestAttempt,
)


# ============================================================
# KNOWLEDGE LAYER SERIALIZERS
# ============================================================

class PunctuationExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PunctuationExample
        fields = ["id", "sentence"]


class PunctuationRuleSerializer(serializers.ModelSerializer):
    examples = PunctuationExampleSerializer(many=True, read_only=True)

    class Meta:
        model = PunctuationRule
        fields = ["id", "rule_text", "examples"]


class PunctuationMarkSerializer(serializers.ModelSerializer):
    rules = PunctuationRuleSerializer(many=True, read_only=True)

    class Meta:
        model = PunctuationMark
        fields = [
            "id",
            "name",
            "symbol",
            "description",
            "order_index",
            "rules",
        ]


# ============================================================
# TEACHING LAYER SERIALIZERS
# ============================================================

class ChunkPunctuationFocusSerializer(serializers.ModelSerializer):
    mark_detail = PunctuationMarkSerializer(source="mark", read_only=True)

    class Meta:
        model = ChunkPunctuationFocus
        fields = [
            "id",
            "chunk",
            "mark",
            "mark_detail",
            "focus_title",
            "focus_description",
            "depth_level",
            "sequence_order",
        ]


# ============================================================
# QUESTIONS
# ============================================================

class PunctuationQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PunctuationQuestion
        fields = [
            "id",
            "focus",
            "question_text",
            "options",
            "correct_answer",
            "question_type",
            "difficulty",
            "explanation",
        ]


# ============================================================
# ATTEMPTS & ANALYTICS
# ============================================================

class PunctuationAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PunctuationAttempt
        fields = [
            "id",
            "student",
            "question",
            "selected_answer",
            "is_correct",
            "attempted_at",
        ]
        read_only_fields = ["is_correct", "attempted_at"]


class PunctuationTestAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PunctuationTestAttempt
        fields = [
            "id",
            "student",
            "focus",
            "score_percent",
            "correct_answers",
            "total_questions",
            "questions_snapshot",
            "created_at",
        ]
        read_only_fields = ["created_at"]