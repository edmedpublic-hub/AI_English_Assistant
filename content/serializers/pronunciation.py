from rest_framework import serializers

from content.models.pronunciation import PronunciationAttempt


# ============================================================
# PRONUNCIATION (ATTEMPTS / AI EVALUATION)
# ============================================================

class PronunciationAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PronunciationAttempt
        fields = [
            "id",
            "student_id",
            "chunk",
            "recording",
            "ai_feedback",
            "ai_score",
            "timestamp",
        ]
        read_only_fields = ["ai_feedback", "ai_score", "timestamp"]
        depth = 1

    def validate_ai_score(self, value):
        """
        Optional safety validation for AI scoring.
        Allows null (before evaluation), otherwise enforces 0–100.
        """
        if value is not None and not (0 <= value <= 100):
            raise serializers.ValidationError("AI score must be between 0 and 100.")
        return value