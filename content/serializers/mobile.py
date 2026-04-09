# content/serializers/mobile.py

from rest_framework import serializers
from django.db import models
from django.utils import timezone

# Core models
from content.models.core import Textbook, Unit, Lesson, LessonChunk

# Domain models - Grammar
from content.models.grammar import (
    ChunkGrammarFocus, GrammarQuestion,
    GrammarPracticeAttempt, GrammarTestAttempt
)

# Domain models - Punctuation
from content.models.punctuation import (
    ChunkPunctuationFocus, PunctuationQuestion,
    PunctuationPracticeAttempt, PunctuationTestAttempt
)

# Domain models - Vocabulary
from content.models.vocabulary import (
    VocabularyItem, VocabularyAttempt, StudentVocabMastery
)

# Domain models - Comprehension
from content.models.comprehension import (
    ChunkComprehensionFocus, ComprehensionQuestion,
    ComprehensionPracticeAttempt, ComprehensionTestAttempt
)

# Domain models - Writing (new three-tier architecture)
from content.models.writing import (
    WritingStageContent,
    WritingAttempt,
    WritingStageMastery,
    WritingIntervention,
)

# Writing mobile serializers — imported from writing serializers
# These are defined in content/serializers/writing.py
from content.serializers.writing import (
    WritingStageContentMobileSerializer,
    WritingAttemptMobileSerializer,
    WritingStageMasteryMobileSerializer,
)

# Domain models - Pronunciation
from content.models.pronunciation import (
    PronunciationFocus, PronunciationAttempt, PronunciationMastery
)

# Domain models - Testing
from content.models.testing import (
    UnitTestSession, UnitTestQuestion, UnitTestAnswer
)


# ============================================================
# CORE MOBILE SERIALIZERS (Lightweight)
# ============================================================

class LessonChunkMobileSerializer(serializers.ModelSerializer):
    """Minimal chunk data for mobile - only essential fields"""

    class Meta:
        model  = LessonChunk
        fields = [
            "id",
            "order",
            "english_text",
            "translated_text",
            "audio_file",
            "translated_audio_file",
            "estimated_time_minutes",
        ]
        read_only_fields = ["id"]


class LessonMobileSerializer(serializers.ModelSerializer):
    """Lightweight lesson serializer for mobile - no nested chunks"""
    chunk_count = serializers.IntegerField(
        source='chunks.count', read_only=True
    )

    class Meta:
        model  = Lesson
        fields = [
            "id",
            "title",
            "number",
            "audio_file",
            "chunk_count",
        ]
        read_only_fields = ["id"]


class UnitMobileSerializer(serializers.ModelSerializer):
    """Lightweight unit serializer for mobile - no nested lessons"""
    lesson_count = serializers.IntegerField(
        source='lessons.count', read_only=True
    )

    class Meta:
        model  = Unit
        fields = [
            "id",
            "title",
            "number",
            "description",
            "lesson_count",
        ]
        read_only_fields = ["id"]


class TextbookMobileSerializer(serializers.ModelSerializer):
    """Lightweight textbook serializer for mobile"""
    unit_count = serializers.IntegerField(
        source='units.count', read_only=True
    )

    class Meta:
        model  = Textbook
        fields = [
            "id",
            "title",
            "class_level",
            "description",
            "unit_count",
        ]
        read_only_fields = ["id"]


# ============================================================
# CONTENT BROWSING MOBILE SERIALIZERS
# ============================================================

class UnitWithLessonsMobileSerializer(serializers.ModelSerializer):
    """Unit with basic lesson info for browsing"""
    lessons = LessonMobileSerializer(many=True, read_only=True)

    class Meta:
        model  = Unit
        fields = ["id", "title", "number", "description", "lessons"]


class LessonWithChunksMobileSerializer(serializers.ModelSerializer):
    """Lesson with chunks for offline storage"""
    chunks = LessonChunkMobileSerializer(many=True, read_only=True)

    class Meta:
        model  = Lesson
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
# GRAMMAR MOBILE SERIALIZERS
# ============================================================

class GrammarQuestionMobileSerializer(serializers.ModelSerializer):
    """Lightweight grammar question for mobile"""
    options_list = serializers.ListField(
        source='get_options_list', read_only=True
    )

    class Meta:
        model  = GrammarQuestion
        fields = [
            "id",
            "question_text",
            "options",
            "options_list",
            "question_type",
            "difficulty",
        ]


class ChunkGrammarFocusMobileSerializer(serializers.ModelSerializer):
    """Grammar focus with questions for practice"""
    questions = GrammarQuestionMobileSerializer(many=True, read_only=True)

    class Meta:
        model  = ChunkGrammarFocus
        fields = [
            "id",
            "focus_title",
            "focus_description",
            "depth_level",
            "sequence_order",
            "questions",
        ]


class GrammarPracticeAttemptMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = GrammarPracticeAttempt
        fields = [
            "id",
            "focus_id",
            "attempt_number",
            "cycle_number",
            "score_percent",
            "is_passed",
            "attempted_at",
        ]


class GrammarTestAttemptMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = GrammarTestAttempt
        fields = [
            "id",
            "focus_id",
            "attempt_number",
            "cycle_number",
            "score_percent",
            "is_mastered",
            "created_at",
        ]


# ============================================================
# PUNCTUATION MOBILE SERIALIZERS
# ============================================================

class PunctuationQuestionMobileSerializer(serializers.ModelSerializer):
    options_list = serializers.ListField(
        source='options_list', read_only=True
    )

    class Meta:
        model  = PunctuationQuestion
        fields = [
            "id",
            "question_text",
            "options",
            "options_list",
            "question_type",
            "difficulty",
        ]


class ChunkPunctuationFocusMobileSerializer(serializers.ModelSerializer):
    questions   = PunctuationQuestionMobileSerializer(many=True, read_only=True)
    mark_symbol = serializers.CharField(source='mark.symbol', read_only=True)

    class Meta:
        model  = ChunkPunctuationFocus
        fields = [
            "id",
            "focus_title",
            "focus_description",
            "mark_symbol",
            "depth_level",
            "sequence_order",
            "questions",
        ]


class PunctuationPracticeAttemptMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PunctuationPracticeAttempt
        fields = [
            "id",
            "focus_id",
            "attempt_number",
            "cycle_number",
            "score_percent",
            "is_passed",
            "created_at",
        ]


class PunctuationTestAttemptMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PunctuationTestAttempt
        fields = [
            "id",
            "focus_id",
            "attempt_number",
            "cycle_number",
            "score_percent",
            "is_mastered",
            "created_at",
        ]


# ============================================================
# VOCABULARY MOBILE SERIALIZERS
# ============================================================

class VocabularyItemMobileSerializer(serializers.ModelSerializer):
    part_of_speech_display = serializers.CharField(
        source='get_part_of_speech_display', read_only=True
    )

    class Meta:
        model  = VocabularyItem
        fields = [
            "id",
            "word",
            "urdu",
            "meaning",
            "part_of_speech",
            "part_of_speech_display",
            "example_sentence",
        ]


class VocabularyAttemptMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VocabularyAttempt
        fields = [
            "id",
            "vocab_item_id",
            "is_correct",
            "time_taken_seconds",
            "created_at",
        ]


class StudentVocabMasteryMobileSerializer(serializers.ModelSerializer):
    word = serializers.CharField(source='vocab_item.word', read_only=True)
    mastery_level_display = serializers.CharField(
        source='get_mastery_level_display', read_only=True
    )

    class Meta:
        model  = StudentVocabMastery
        fields = [
            "vocab_item_id",
            "word",
            "mastery_level",
            "mastery_level_display",
            "accuracy_percentage",
        ]


# ============================================================
# COMPREHENSION MOBILE SERIALIZERS
# ============================================================

class ComprehensionQuestionMobileSerializer(serializers.ModelSerializer):
    options_list = serializers.ListField(
        source='get_options_list', read_only=True
    )

    class Meta:
        model  = ComprehensionQuestion
        fields = [
            "id",
            "question_text",
            "options",
            "options_list",
            "question_type",
            "difficulty",
        ]


class ChunkComprehensionFocusMobileSerializer(serializers.ModelSerializer):
    questions     = ComprehensionQuestionMobileSerializer(many=True, read_only=True)
    level_display = serializers.CharField(
        source='get_level_display', read_only=True
    )

    class Meta:
        model  = ChunkComprehensionFocus
        fields = [
            "id",
            "focus_title",
            "focus_description",
            "level",
            "level_display",
            "depth_level",
            "sequence_order",
            "questions",
        ]


class ComprehensionPracticeAttemptMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ComprehensionPracticeAttempt
        fields = [
            "id",
            "focus_id",
            "attempt_number",
            "cycle_number",
            "score_percent",
            "is_passed",
            "attempted_at",
        ]


class ComprehensionTestAttemptMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ComprehensionTestAttempt
        fields = [
            "id",
            "focus_id",
            "attempt_number",
            "cycle_number",
            "score_percent",
            "is_mastered",
            "created_at",
        ]


# ============================================================
# WRITING MOBILE SERIALIZERS
# New three-tier architecture.
# Serializer classes are defined in content/serializers/writing.py
# and imported at the top of this file.
# They are re-exported here so mobile.py consumers
# can import from a single place.
# ============================================================

# WritingStageContentMobileSerializer  — imported above
# WritingAttemptMobileSerializer       — imported above
# WritingStageMasteryMobileSerializer  — imported above


# ============================================================
# PRONUNCIATION MOBILE SERIALIZERS
# ============================================================

class PronunciationFocusMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PronunciationFocus
        fields = [
            "id",
            "focus_title",
            "focus_description",
            "sequence_order",
        ]


class PronunciationAttemptMobileSerializer(serializers.ModelSerializer):
    is_passed = serializers.BooleanField(read_only=True)

    class Meta:
        model  = PronunciationAttempt
        fields = [
            "id",
            "focus_id",
            "attempt_number",
            "cycle_number",
            "ai_score",
            "is_passed",
            "attempt_type",
            "created_at",
        ]


class PronunciationMasteryMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PronunciationMastery
        fields = [
            "focus_id",
            "is_mastered",
            "best_score",
            "last_score",
            "total_attempts",
        ]


# ============================================================
# TESTING MOBILE SERIALIZERS
# ============================================================

class UnitTestQuestionMobileSerializer(serializers.ModelSerializer):
    domain_display = serializers.CharField(
        source='get_domain_display', read_only=True
    )

    class Meta:
        model  = UnitTestQuestion
        fields = [
            "id",
            "domain",
            "domain_display",
            "question_type",
            "question_text",
            "options",
            "difficulty",
            "order",
            "points",
        ]


class UnitTestSessionMobileSerializer(serializers.ModelSerializer):
    unit_title          = serializers.CharField(
        source='unit.title', read_only=True
    )
    progress_percentage = serializers.SerializerMethodField()
    time_remaining      = serializers.SerializerMethodField()

    class Meta:
        model  = UnitTestSession
        fields = [
            "id",
            "unit_id",
            "unit_title",
            "attempt_number",
            "started_at",
            "time_remaining",
            "total_questions",
            "correct_answers",
            "score_percentage",
            "passed",
            "progress_percentage",
        ]

    def get_progress_percentage(self, obj):
        if obj.total_questions == 0:
            return 0
        answered = UnitTestAnswer.objects.filter(
            question__session=obj
        ).count()
        return int((answered / obj.total_questions) * 100)

    def get_time_remaining(self, obj):
        if obj.completed_at:
            return 0
        time_limit = 60 * 60
        elapsed    = (timezone.now() - obj.started_at).total_seconds()
        return max(0, int(time_limit - elapsed))


class UnitTestSessionActiveMobileSerializer(serializers.ModelSerializer):
    questions = UnitTestQuestionMobileSerializer(many=True, read_only=True)

    class Meta:
        model  = UnitTestSession
        fields = [
            "id",
            "attempt_number",
            "started_at",
            "total_questions",
            "questions",
        ]


class UnitTestAnswerMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UnitTestAnswer
        fields = [
            "question_id",
            "student_answer",
            "is_correct",
            "time_taken_seconds",
        ]


class UnitTestHistoryMobileSerializer(serializers.Serializer):
    unit_id    = serializers.IntegerField()
    unit_title = serializers.CharField()
    attempts   = serializers.ListField(child=serializers.DictField())
    best_score = serializers.FloatField()
    passed     = serializers.BooleanField()


# ============================================================
# DASHBOARD MOBILE SERIALIZERS
# ============================================================

class DomainProgressMobileSerializer(serializers.Serializer):
    mastery_percentage = serializers.FloatField()
    needs_review_count = serializers.IntegerField()
    last_activity      = serializers.DateTimeField(allow_null=True)


class DashboardMobileSerializer(serializers.Serializer):
    streak_days     = serializers.IntegerField()
    overall_mastery = serializers.FloatField()

    grammar       = DomainProgressMobileSerializer()
    punctuation   = DomainProgressMobileSerializer()
    vocabulary    = DomainProgressMobileSerializer()
    comprehension = DomainProgressMobileSerializer()
    writing       = DomainProgressMobileSerializer()
    pronunciation = DomainProgressMobileSerializer()

    recent_activity = serializers.ListField(child=serializers.DictField())
    next_steps      = serializers.ListField(child=serializers.DictField())
    in_progress     = serializers.ListField(child=serializers.DictField())


# ============================================================
# SUBMISSION SERIALIZERS FOR MOBILE
# ============================================================

class MobilePracticeSubmitSerializer(serializers.Serializer):
    domain     = serializers.ChoiceField(choices=[
        'grammar', 'punctuation', 'vocabulary',
        'comprehension', 'writing', 'pronunciation'
    ])
    focus_id   = serializers.IntegerField(required=False, allow_null=True)
    item_id    = serializers.IntegerField(required=False, allow_null=True)
    answers    = serializers.ListField(child=serializers.DictField())
    time_spent_seconds = serializers.IntegerField(min_value=0, required=False)

    def validate(self, data):
        domain = data.get('domain')
        if domain == 'vocabulary':
            if not data.get('item_id'):
                raise serializers.ValidationError(
                    "vocabulary practice requires item_id"
                )
        else:
            if not data.get('focus_id'):
                raise serializers.ValidationError(
                    f"{domain} practice requires focus_id"
                )
        return data


class MobileTestSubmitSerializer(serializers.Serializer):
    domain     = serializers.ChoiceField(choices=[
        'grammar', 'punctuation', 'comprehension',
        'writing', 'pronunciation', 'unit_test'
    ])
    focus_id   = serializers.IntegerField(required=False, allow_null=True)
    content_id = serializers.IntegerField(required=False, allow_null=True)
    session_id = serializers.IntegerField(required=False, allow_null=True)
    answers    = serializers.ListField(child=serializers.DictField())
    time_spent_seconds = serializers.IntegerField(min_value=0)

    def validate(self, data):
        domain = data.get('domain')
        if domain == 'unit_test':
            if not data.get('session_id'):
                raise serializers.ValidationError(
                    "unit_test submission requires session_id"
                )
        elif domain == 'writing':
            if not data.get('content_id'):
                raise serializers.ValidationError(
                    "writing test requires content_id"
                )
        else:
            if not data.get('focus_id'):
                raise serializers.ValidationError(
                    f"{domain} test requires focus_id"
                )
        return data


# ============================================================
# OFFLINE SYNC SERIALIZERS
# ============================================================

class SyncPayloadSerializer(serializers.Serializer):
    pending_practices   = serializers.ListField(
        child=MobilePracticeSubmitSerializer(),
        required=False,
        default=list
    )
    pending_tests       = serializers.ListField(
        child=MobileTestSubmitSerializer(),
        required=False,
        default=list
    )
    last_sync_timestamp = serializers.DateTimeField(required=False)


class SyncResponseSerializer(serializers.Serializer):
    synced_practices = serializers.ListField(child=serializers.DictField())
    synced_tests     = serializers.ListField(child=serializers.DictField())
    updated_content  = serializers.DictField(child=serializers.ListField())
    server_timestamp = serializers.DateTimeField()


# ============================================================
# BATCH OPERATION SERIALIZERS FOR MOBILE
# ============================================================

class MobileBatchContentSerializer(serializers.Serializer):
    textbook_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    unit_ids     = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    lesson_ids   = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    chunk_ids    = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )

    def validate(self, data):
        if not any([
            data.get('textbook_ids'),
            data.get('unit_ids'),
            data.get('lesson_ids'),
            data.get('chunk_ids'),
        ]):
            raise serializers.ValidationError(
                "At least one ID list must be provided"
            )
        return data


class MobileBatchContentResponseSerializer(serializers.Serializer):
    textbooks  = TextbookMobileSerializer(many=True)
    units      = UnitMobileSerializer(many=True)
    lessons    = LessonMobileSerializer(many=True)
    chunks     = LessonChunkMobileSerializer(many=True)

    # Domain focuses
    grammar_focuses       = ChunkGrammarFocusMobileSerializer(many=True)
    punctuation_focuses   = ChunkPunctuationFocusMobileSerializer(many=True)
    vocabulary_items      = VocabularyItemMobileSerializer(many=True)
    comprehension_focuses = ChunkComprehensionFocusMobileSerializer(many=True)
    pronunciation_focuses = PronunciationFocusMobileSerializer(many=True)

    # Writing — new three-tier architecture
    writing_stage_contents = WritingStageContentMobileSerializer(many=True)
    writing_attempts       = WritingAttemptMobileSerializer(many=True)
    writing_masteries      = WritingStageMasteryMobileSerializer(many=True)


# ============================================================
# PUSH NOTIFICATION SERIALIZERS
# ============================================================

class MobileNotificationSerializer(serializers.Serializer):
    notification_type = serializers.ChoiceField(choices=[
        'practice_reminder',
        'test_available',
        'mastery_achieved',
        'streak_milestone',
        'content_updated',
    ])
    title    = serializers.CharField()
    body     = serializers.CharField()
    data     = serializers.DictField(required=False, default=dict)
    priority = serializers.ChoiceField(
        choices=['high', 'normal', 'low'],
        default='normal'
    )