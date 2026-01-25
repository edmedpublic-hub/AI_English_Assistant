from rest_framework import serializers
from content.models.core import Textbook, Unit, Lesson, LessonChunk


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
        ]


# ============================================================
#  LESSONS
# ============================================================

class LessonSerializer(serializers.ModelSerializer):
    chunks = LessonChunkSerializer(many=True, read_only=True)

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
        ]


# ============================================================
#  UNITS
# ============================================================

class UnitSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Unit
        fields = [
            "id",
            "title",
            "number",
            "lessons",
        ]


# ============================================================
#  TEXTBOOKS
# ============================================================

class TextbookSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)

    class Meta:
        model = Textbook
        fields = [
            "id",
            "title",
            "class_level",
            "description",
            "units",
        ]
