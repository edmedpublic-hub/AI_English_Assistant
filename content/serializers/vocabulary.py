from rest_framework import serializers
from content.models.vocabulary import (
    VocabularyItem,
    VocabularyAttempt,
    StudentVocabMastery,
)


# ============================================================
#  VOCABULARY ITEMS
# ============================================================

class VocabularyItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyItem
        fields = [
            "id",
            "word",
            "part_of_speech",
            "urdu",
            "meaning",
            "synonyms",
            "antonyms",
            "example_sentence",
        ]


# ============================================================
#  VOCABULARY ATTEMPTS (Analytics-safe)
# ============================================================

class VocabularyAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyAttempt
        fields = [
            "id",
            "student_id",
            "vocab_item",
            "is_correct",
            "timestamp",
        ]
        read_only_fields = ["timestamp"]
        depth = 1


# ============================================================
#  VOCABULARY MASTERY TRACKING
# ============================================================

class StudentVocabMasterySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentVocabMastery
        fields = [
            "id",
            "student_id",
            "vocab_item",
            "mastery_level",
            "last_updated",
        ]
        read_only_fields = ["last_updated"]
        depth = 1
