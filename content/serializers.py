from rest_framework import serializers
from .models import (
    Textbook,
    Unit,
    Lesson,
    VocabularyItem,
    WritingTask,
    SentenceAttempt,
    GrammarPoint,
    ComprehensionQuestion
)

# -------------------------------
# TEXTBOOK
# -------------------------------
class TextbookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Textbook
        fields = '__all__'


# -------------------------------
# UNIT
# -------------------------------
class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'


# -------------------------------
# LESSON
# -------------------------------
class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'


# -------------------------------
# VOCABULARY ITEMS
# -------------------------------
class VocabularyItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyItem
        fields = '__all__'


# -------------------------------
# COMPREHENSION QUESTIONS
# -------------------------------
class ComprehensionQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComprehensionQuestion
        fields = '__all__'


# -------------------------------
# GRAMMAR POINT
# -------------------------------
class GrammarPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarPoint
        fields = '__all__'


# -------------------------------
# WRITING TASK
# -------------------------------
class WritingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingTask
        fields = '__all__'


# -------------------------------
# SENTENCE ATTEMPTS
# -------------------------------
class SentenceAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentenceAttempt
        fields = '__all__'
