# content/serializers/core.py

from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from content.models.core import Textbook, Unit, Lesson, LessonChunk
from django.db import models


# ============================================================
#  LESSON CHUNKS
# ============================================================

class LessonChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonChunk
        fields = [
            "id",
            "order",
            "english_text",
            "translated_text",
            "audio_file",
            "translated_audio_file",
            "estimated_time_minutes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_estimated_time_minutes(self, value):
        if value and value < 0:
            raise serializers.ValidationError("Estimated time must be positive")
        return value


# ============================================================
#  LESSONS
# ============================================================

class LessonSerializer(serializers.ModelSerializer):
    chunks = LessonChunkSerializer(many=True, read_only=True)
    completion_status = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    chunk_count = serializers.IntegerField(source='chunks.count', read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "number",
            "english_text",
            "translated_text",
            "audio_file",
            "chunks",
            "chunk_count",
            "created_at",
            "updated_at",
            "completion_status",
            "total_duration",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_completion_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return {
                'completed': False,
                'percentage': 0,
                'last_accessed': None
            }
        return None

    def get_total_duration(self, obj):
        total = obj.chunks.aggregate(
            total=models.Sum('estimated_time_minutes')
        )['total']
        return total or 0


class LessonListMobileSerializer(serializers.ModelSerializer):
    """Lightweight serializer for mobile list views"""
    chunk_count = serializers.IntegerField(source='chunks.count', read_only=True)
    
    class Meta:
        model = Lesson
        fields = [
            "id", 
            "title", 
            "number", 
            "audio_file",
            "chunk_count"
        ]


# ============================================================
#  UNITS
# ============================================================

class UnitSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    progress_summary = serializers.SerializerMethodField()
    total_chunks = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Unit
        fields = [
            "id",
            "title",
            "number",
            "description",
            "lessons",
            "total_chunks",
            "created_at",
            "updated_at",
            "progress_summary",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "total_chunks"]

    def get_progress_summary(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return {
                'total_lessons': obj.lessons.count(),
                'completed_lessons': 0,
                'percentage': 0,
                'total_chunks': obj.total_chunks
            }
        return None


class UnitListMobileSerializer(serializers.ModelSerializer):
    """Lightweight serializer for mobile unit lists"""
    lesson_count = serializers.IntegerField(source='lessons.count', read_only=True)
    
    class Meta:
        model = Unit
        fields = [
            "id", 
            "title", 
            "number", 
            "lesson_count",
            "description"
        ]


# ============================================================
#  TEXTBOOKS
# ============================================================

class TextbookSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)
    unit_count = serializers.IntegerField(source='units.count', read_only=True)
    
    class Meta:
        model = Textbook
        fields = [
            "id",
            "title",
            "class_level",
            "description",
            "units",
            "unit_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TextbookListMobileSerializer(serializers.ModelSerializer):
    """Lightweight serializer for mobile textbook lists"""
    unit_count = serializers.IntegerField(source='units.count', read_only=True)
    
    class Meta:
        model = Textbook
        fields = [
            "id", 
            "title", 
            "class_level", 
            "description",
            "unit_count"
        ]


# ============================================================
#  MASTERY & PROGRESS SERIALIZERS
# ============================================================

class ChunkMasteryDetailsSerializer(serializers.Serializer):
    """Serializer for chunk mastery status"""
    domain = serializers.CharField()
    mastered = serializers.BooleanField()
    details = serializers.ListField(child=serializers.DictField())


class LessonChunkMasterySerializer(serializers.ModelSerializer):
    """Serializer that includes mastery status from chunk methods"""
    mastery_status = serializers.SerializerMethodField()
    is_mastered = serializers.SerializerMethodField()
    next_priority = serializers.SerializerMethodField()

    class Meta:
        model = LessonChunk
        fields = [
            "id",
            "order",
            "english_text",
            "translated_text",
            "estimated_time_minutes",
            "is_mastered",
            "mastery_status",
            "next_priority",
        ]

    def get_mastery_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_mastery_status(request.user)
        return None

    def get_is_mastered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_mastered_by(request.user)
        return False

    def get_next_priority(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj._next_priority_domain(request.user)
        return None


# ============================================================
#  EXPORTS
# ============================================================

__all__ = [
    'LessonChunkSerializer',
    'LessonSerializer',
    'LessonListMobileSerializer',
    'UnitSerializer',
    'UnitListMobileSerializer',
    'TextbookSerializer',
    'TextbookListMobileSerializer',
    'ChunkMasteryDetailsSerializer',
    'LessonChunkMasterySerializer',
]