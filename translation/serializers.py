from rest_framework import serializers
from .models import TranslationTextbook, TranslationUnit, TranslationLesson


class TranslationLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationLesson
        fields = [
            'id',
            'lesson_number',
            'title',
            'english_chunk',
            'urdu_chunk',
            'source_language',
            'target_language',
            'published',
            'is_active',
        ]


class TranslationUnitSerializer(serializers.ModelSerializer):
    lessons = TranslationLessonSerializer(many=True, read_only=True)

    class Meta:
        model = TranslationUnit
        fields = [
            'id',
            'unit_number',
            'title',
            'description',
            'lessons',
        ]


class TranslationTextbookSerializer(serializers.ModelSerializer):
    units = TranslationUnitSerializer(many=True, read_only=True)

    class Meta:
        model = TranslationTextbook
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'language',
            'published',
            'is_active',
            'units',
        ]
