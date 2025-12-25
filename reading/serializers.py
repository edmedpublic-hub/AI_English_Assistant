from rest_framework import serializers
from .models import ReadingLesson
from .models import PronunciationAttempt

class ReadingLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingLesson
        fields = [
            "id",
            "title",
            "content",      # plain text content
            "unit",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        
class PronunciationAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PronunciationAttempt
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
