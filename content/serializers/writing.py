from rest_framework import serializers

from content.models.writing import (
    WritingTask,
    SentenceAttempt,
)


# ============================================================
# WRITING (CONTENT DELIVERY)
# ============================================================

class WritingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingTask
        fields = [
            "id",
            "prompt",
            "difficulty",
        ]


# ============================================================
# WRITING (ATTEMPTS / ANALYTICS)
# ============================================================

class SentenceAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentenceAttempt
        fields = [
            "id",
            "student_id",
            "writing_task",
            "sentence",
            "ai_score",
            "feedback",
            "timestamp",
        ]
        read_only_fields = ["ai_score", "feedback", "timestamp"]
        depth = 1

    def validate_ai_score(self, value):
        """
        Safety validation for AI scoring range.
        """
        if value is not None and not (0 <= value <= 100):
            raise serializers.ValidationError("AI score must be between 0 and 100.")
        return value
