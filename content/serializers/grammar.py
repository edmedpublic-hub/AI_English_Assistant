from rest_framework import serializers

from content.models.grammar import (
    GrammarConcept,
    GrammarRule,
    GrammarExample,
    ChunkGrammarFocus,
    GrammarQuestion,
    GrammarAttempt,
    GrammarTestAttempt,
)


# ============================================================
# KNOWLEDGE LAYER SERIALIZERS
# ============================================================

class GrammarExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarExample
        fields = [
            "id",
            "sentence",
        ]


class GrammarRuleSerializer(serializers.ModelSerializer):
    examples = GrammarExampleSerializer(many=True, read_only=True)

    class Meta:
        model = GrammarRule
        fields = [
            "id",
            "rule_text",
            "examples",
        ]


class GrammarConceptSerializer(serializers.ModelSerializer):
    rules = GrammarRuleSerializer(many=True, read_only=True)

    class Meta:
        model = GrammarConcept
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "category",
            "order_index",
            "rules",
        ]


# ============================================================
# TEACHING LAYER SERIALIZERS
# ============================================================

class ChunkGrammarFocusSerializer(serializers.ModelSerializer):
    concept = GrammarConceptSerializer(read_only=True)

    class Meta:
        model = ChunkGrammarFocus
        fields = [
            "id",
            "focus_title",
            "focus_description",
            "depth_level",
            "sequence_order",
            "concept",
        ]


# ============================================================
# QUESTIONS
# ============================================================

class GrammarQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarQuestion
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
# ANALYTICS / ATTEMPTS
# ============================================================

class GrammarAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarAttempt
        fields = [
            "id",
            "student",
            "question",
            "selected_answer",
            "is_correct",
            "attempted_at",
        ]
        read_only_fields = ["attempted_at"]
        depth = 1


class GrammarTestAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarTestAttempt
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
        depth = 1
