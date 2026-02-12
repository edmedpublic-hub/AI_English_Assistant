# content/admin/serializers/writing.py

from rest_framework import serializers
from content.models.writing import (
    ChunkWritingFocus,
    UnitWritingTask,
    WritingPrompt,
    WritingResponse,
    WritingAttempt,
    WritingTestAttempt,
)

# ============================================================
# TEACHING LAYER SERIALIZERS
# ============================================================

class ChunkWritingFocusAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkWritingFocus
        fields = [
            "id", "chunk", "focus_title", "focus_description",
            "depth_level", "sequence_order"
        ]


class UnitWritingTaskAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitWritingTask
        fields = [
            "id", "unit", "task_title", "task_description",
            "stage", "difficulty_level", "order"
        ]


# ============================================================
# PROMPTS
# ============================================================

class WritingPromptAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingPrompt
        fields = [
            "id", "prompt_text", "expected_keywords", "rubric",
            "focus", "task"
        ]


# ============================================================
# RESPONSES
# ============================================================

class WritingResponseAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingResponse
        fields = [
            "id", "prompt", "student", "response_text",
            "submitted_at", "score", "feedback"
        ]
        read_only_fields = ["submitted_at"]


# ============================================================
# ATTEMPTS & ANALYTICS
# ============================================================

class WritingAttemptAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingAttempt
        fields = [
            "id", "response", "attempt_number",
            "time_spent", "hints_used"
        ]


class WritingTestAttemptAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingTestAttempt
        fields = [
            "id", "student", "prompt", "rubric_scores",
            "overall_score", "created_at"
        ]
        read_only_fields = ["created_at"]