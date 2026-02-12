from rest_framework import serializers
from content.models.punctuation import (
    PunctuationMark,
    PunctuationRule,
    PunctuationExample,
    ChunkPunctuationFocus,
    PunctuationQuestion,
    # PunctuationAttempt removed - now handled via TestAttempt analytics
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
        fields = ["id", "name", "symbol", "description", "order_index", "rules"]


# ============================================================
# TEACHING LAYER SERIALIZERS
# ============================================================

class ChunkPunctuationFocusSerializer(serializers.ModelSerializer):
    mark_detail = PunctuationMarkSerializer(source="mark", read_only=True)

    class Meta:
        model = ChunkPunctuationFocus
        fields = [
            "id", "chunk", "mark", "mark_detail", 
            "focus_title", "focus_description", 
            "depth_level", "sequence_order"
        ]


# ============================================================
# QUESTIONS (Student-safe)
# ============================================================

class PunctuationQuestionSerializer(serializers.ModelSerializer):
    """Student-facing: uses get_options_list property from model."""
    options_list = serializers.ReadOnlyField(source='get_options_list')

    class Meta:
        model = PunctuationQuestion
        fields = [
            "id", "question_text", "options_list", 
            "question_type", "explanation"
        ]


# ============================================================
# SUBMISSION & ANALYTICS
# ============================================================

class PunctuationAnswerSubmitSerializer(serializers.Serializer):
    """Handles the logic of checking a single answer submission."""
    question_id = serializers.IntegerField()
    selected_answer = serializers.CharField(allow_blank=True)

    def validate(self, data):
        try:
            question = PunctuationQuestion.objects.get(id=data["question_id"])
        except PunctuationQuestion.DoesNotExist:
            raise serializers.ValidationError("Invalid question ID.")

        data["question"] = question
        # Exact match logic for production grade accuracy
        data["is_correct"] = (data["selected_answer"].strip() == question.correct_answer.strip())
        return data


class PunctuationTestAttemptSerializer(serializers.ModelSerializer):
    """Detailed results for the Progress Dashboard."""
    class Meta:
        model = PunctuationTestAttempt
        fields = [
            "id", "student", "focus", "score_percent", 
            "correct_answers", "total_questions", 
            "attempt_number", "is_mastered", "created_at"
        ]
        read_only_fields = ["is_mastered", "created_at"]