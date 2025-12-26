from rest_framework import serializers
from .models import TranslationTextbook, TranslationUnit, TranslationLesson


# ---------- LESSON SERIALIZERS ----------

class TranslationLessonSerializer(serializers.ModelSerializer):
    """
    Full detail serializer for Lesson detail endpoints.
    """

    class Meta:
        model = TranslationLesson
        fields = [
            "id",
            "lesson_number",
            "title",
            "english_chunk",
            "urdu_chunk",
            "source_language",
            "target_language",
            "published",
            "is_active",
        ]
        read_only_fields = ["published"]

    def validate_lesson_number(self, value):
        if value < 1:
            raise serializers.ValidationError("Lesson number must be 1 or greater.")
        return value

    def validate(self, attrs):
        # Normalize language codes
        if "source_language" in attrs and attrs["source_language"]:
            attrs["source_language"] = attrs["source_language"].lower()

        if "target_language" in attrs and attrs["target_language"]:
            attrs["target_language"] = attrs["target_language"].lower()

        return attrs


class TranslationLessonNestedSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for embedding lessons inside units.
    """

    class Meta:
        model = TranslationLesson
        fields = [
            "id",
            "lesson_number",
            "title",
            "published",
        ]
        read_only_fields = fields


# ---------- UNIT SERIALIZERS ----------

class TranslationUnitSerializer(serializers.ModelSerializer):
    """
    Full unit serializer for unit detail endpoints,
    with lightweight nested lessons (read-only).
    """

    lessons = TranslationLessonNestedSerializer(many=True, read_only=True)

    class Meta:
        model = TranslationUnit
        fields = [
            "id",
            "unit_number",
            "title",
            "description",
            "lessons",
        ]

    def validate_unit_number(self, value):
        if value < 1:
            raise serializers.ValidationError("Unit number must be 1 or greater.")
        return value


class TranslationUnitNestedSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for embedding units inside textbooks.
    """

    class Meta:
        model = TranslationUnit
        fields = [
            "id",
            "unit_number",
            "title",
        ]
        read_only_fields = fields


# ---------- TEXTBOOK SERIALIZERS ----------

class TranslationTextbookSerializer(serializers.ModelSerializer):
    """
    Textbook serializer with lightweight nested units (read-only).
    """

    units = TranslationUnitNestedSerializer(many=True, read_only=True)

    class Meta:
        model = TranslationTextbook
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "language",
            "published",
            "is_active",
            "units",
        ]
