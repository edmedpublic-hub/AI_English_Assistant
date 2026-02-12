from rest_framework import serializers
from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionQuestion,
    ComprehensionAttempt,
)


# ============================================================
# COMPREHENSION (CONTENT DELIVERY)
# ============================================================

class ComprehensionQuestionSerializer(serializers.ModelSerializer):
    parsed_options = serializers.ListField(
        source="parsed_options", read_only=True
    )

    class Meta:
        model = ComprehensionQuestion
        fields = [
            "id",
            "focus",
            "question_text",
            "question_type",
            "difficulty",
            "options",
            "parsed_options",
            "correct_answer",
            "explanation",
        ]
        depth = 1


class ChunkComprehensionFocusSerializer(serializers.ModelSerializer):
    questions = ComprehensionQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = ChunkComprehensionFocus
        fields = [
            "id",
            "chunk",
            "focus_title",
            "focus_description",
            "level",
            "sequence_order",
            "questions",
        ]
        depth = 1


# ============================================================
# COMPREHENSION (ANALYTICS / ATTEMPTS)
# ============================================================

class ComprehensionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComprehensionAttempt
        fields = [
            "id",
            "student",
            "question",
            "selected_answer",
            "open_ended_answer",
            "is_correct",
            "attempted_at",
        ]
        read_only_fields = ["attempted_at"]
        depth = 1