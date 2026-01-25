from rest_framework import serializers

from content.models.comprehension import (
    ComprehensionQuestion,
    ComprehensionAttempt,
)


# ============================================================
# COMPREHENSION (CONTENT DELIVERY)
# ============================================================

class ComprehensionQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComprehensionQuestion
        fields = [
            "id",
            "question",
            "answer",
        ]


# ============================================================
# COMPREHENSION (ANALYTICS / ATTEMPTS)
# ============================================================

class ComprehensionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComprehensionAttempt
        fields = [
            "id",
            "student_id",
            "question",
            "answer",
            "is_correct",
            "timestamp",
        ]
        read_only_fields = ["timestamp"]
        depth = 1
