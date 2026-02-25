from rest_framework import serializers
from content.models.testing import (
    UnitTestSession, UnitTestQuestion, UnitTestAnswer,
    VocabularyUnitTestAttempt,
)
from content.models.core import Unit, Lesson, LessonChunk
from content.models.vocabulary import VocabularyItem
from content.models.grammar import GrammarConcept
from content.models.punctuation import PunctuationMark
from content.models.comprehension import BloomLevel
from django.db import models
from django.utils import timezone

# Try to import legacy models, but don't fail if they don't exist
try:
    from content.models.testing import (
        VocabularyTestSession, VocabularyTestQuestion, 
        VocabularyTestAnswer, VocabularyTestAttempt
    )
    LEGACY_MODELS_AVAILABLE = True
except ImportError:
    LEGACY_MODELS_AVAILABLE = False
    # Create dummy classes for type hints if needed
    VocabularyTestSession = None
    VocabularyTestQuestion = None
    VocabularyTestAnswer = None
    VocabularyTestAttempt = None


# ============================================================
# TEST QUESTION SERIALIZERS
# ============================================================

class UnitTestQuestionSerializer(serializers.ModelSerializer):
    domain_display = serializers.CharField(source='get_domain_display', read_only=True)
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    bloom_level_display = serializers.CharField(source='get_bloom_level_display', read_only=True)
    
    # Source details for analytics
    vocabulary_item_word = serializers.CharField(
        source='vocabulary_item.word', 
        read_only=True,
        default=None
    )
    grammar_concept_name = serializers.CharField(
        source='grammar_concept.name', 
        read_only=True,
        default=None
    )
    punctuation_mark_symbol = serializers.CharField(
        source='punctuation_mark.symbol', 
        read_only=True,
        default=None
    )

    class Meta:
        model = UnitTestQuestion
        fields = [
            "id",
            "session_id",
            "domain",
            "domain_display",
            "question_type",
            "question_type_display",
            "question_text",
            "options",
            "correct_answer",
            "difficulty",
            "order",
            "points",
            "vocabulary_item_id",
            "vocabulary_item_word",
            "grammar_concept_id",
            "grammar_concept_name",
            "punctuation_mark_id",
            "punctuation_mark_symbol",
            "bloom_level",
            "bloom_level_display",
        ]
        read_only_fields = ["id"]


class UnitTestQuestionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for question listings"""
    class Meta:
        model = UnitTestQuestion
        fields = [
            "id",
            "order",
            "domain",
            "question_type",
            "difficulty",
            "points",
        ]


# ============================================================
# MOBILE-OPTIMIZED SERIALIZERS
# ============================================================

class UnitTestQuestionMobileSerializer(serializers.ModelSerializer):
    """Mobile-optimized test question serializer"""
    domain_display = serializers.CharField(source='get_domain_display', read_only=True)
    
    class Meta:
        model = UnitTestQuestion
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


class UnitTestAnswerMobileSerializer(serializers.ModelSerializer):
    """Mobile-optimized answer serializer"""
    
    class Meta:
        model = UnitTestAnswer
        fields = [
            "question_id",
            "student_answer",
            "is_correct",
            "time_taken_seconds",
        ]


class UnitTestSessionMobileSerializer(serializers.ModelSerializer):
    """Mobile-optimized test session serializer"""
    unit_title = serializers.CharField(source='unit.title', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UnitTestSession
        fields = [
            "id",
            "unit_id",
            "unit_title",
            "attempt_number",
            "started_at",
            "completed_at",
            "score_percentage",
            "passed",
            "total_questions",
            "correct_answers",
            "progress_percentage",
        ]
    
    def get_progress_percentage(self, obj):
        if obj.total_questions == 0:
            return 0
        answered = UnitTestAnswer.objects.filter(question__session=obj).count()
        return int((answered / obj.total_questions) * 100)


class UnitTestSessionActiveMobileSerializer(serializers.ModelSerializer):
    """Mobile-optimized active test session with questions"""
    questions = UnitTestQuestionMobileSerializer(many=True, read_only=True)
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = UnitTestSession
        fields = [
            "id",
            "attempt_number",
            "started_at",
            "total_questions",
            "questions",
            "time_remaining",
        ]
    
    def get_time_remaining(self, obj):
        if obj.completed_at:
            return 0
        # Default 60 minute time limit
        time_limit = 60 * 60
        elapsed = (timezone.now() - obj.started_at).total_seconds()
        return max(0, int(time_limit - elapsed))


class UnitTestHistoryMobileSerializer(serializers.Serializer):
    """Mobile-optimized test history serializer"""
    unit_id = serializers.IntegerField()
    unit_title = serializers.CharField()
    unit_number = serializers.IntegerField()
    attempts = serializers.IntegerField()
    best_score = serializers.FloatField()
    passed = serializers.BooleanField()
    last_attempted = serializers.DateTimeField()


# ============================================================
# TEST ANSWER SERIALIZERS
# ============================================================

class UnitTestAnswerSerializer(serializers.ModelSerializer):
    question_details = UnitTestQuestionListSerializer(source='question', read_only=True)
    
    class Meta:
        model = UnitTestAnswer
        fields = [
            "id",
            "question_id",
            "question_details",
            "student_answer",
            "is_correct",
            "answered_at",
            "time_taken_seconds",
        ]
        read_only_fields = ["id", "answered_at", "is_correct"]


class UnitTestAnswerSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a single answer during test"""
    question_id = serializers.IntegerField()
    student_answer = serializers.CharField(allow_blank=True)
    time_taken_seconds = serializers.IntegerField(min_value=0, required=False)

    def validate_question_id(self, value):
        try:
            question = UnitTestQuestion.objects.get(id=value)
            # Check if question belongs to an active session
            if question.session.completed_at:
                raise serializers.ValidationError("Test session already completed")
        except UnitTestQuestion.DoesNotExist:
            raise serializers.ValidationError("Invalid question ID")
        return value


# ============================================================
# TEST SESSION SERIALIZERS
# ============================================================

class UnitTestSessionSerializer(serializers.ModelSerializer):
    questions = UnitTestQuestionSerializer(many=True, read_only=True)
    answers = serializers.SerializerMethodField()
    unit_title = serializers.CharField(source='unit.title', read_only=True)
    unit_number = serializers.IntegerField(source='unit.number', read_only=True)
    time_remaining = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UnitTestSession
        fields = [
            "id",
            "user_id",
            "unit_id",
            "unit_title",
            "unit_number",
            "attempt_number",
            "started_at",
            "completed_at",
            "time_taken_seconds",
            "time_remaining",
            "total_questions",
            "correct_answers",
            "score_percentage",
            "passed",
            "domain_scores",
            "test_data",
            "questions",
            "answers",
            "progress_percentage",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "started_at",
            "completed_at",
            "total_questions",
            "correct_answers",
            "score_percentage",
            "passed",
            "domain_scores",
            "test_data",
        ]

    def get_answers(self, obj):
        """Get all answers for this session"""
        answers = UnitTestAnswer.objects.filter(question__session=obj)
        return UnitTestAnswerSerializer(answers, many=True).data

    def get_time_remaining(self, obj):
        """Calculate time remaining if session is active"""
        if obj.completed_at:
            return 0
        
        # Default time limit: 60 minutes per test
        time_limit = 60 * 60  # 60 minutes in seconds
        elapsed = (timezone.now() - obj.started_at).total_seconds()
        remaining = max(0, time_limit - elapsed)
        return int(remaining)

    def get_progress_percentage(self, obj):
        """Calculate test completion percentage"""
        if obj.total_questions == 0:
            return 0
        answered = UnitTestAnswer.objects.filter(question__session=obj).count()
        return int((answered / obj.total_questions) * 100)


class UnitTestSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for test session listings"""
    unit_title = serializers.CharField(source='unit.title', read_only=True)
    
    class Meta:
        model = UnitTestSession
        fields = [
            "id",
            "unit_id",
            "unit_title",
            "attempt_number",
            "started_at",
            "completed_at",
            "score_percentage",
            "passed",
            "total_questions",
            "correct_answers",
        ]


class UnitTestSessionCreateSerializer(serializers.Serializer):
    """Serializer for starting a new test session"""
    unit_id = serializers.IntegerField()
    
    def validate_unit_id(self, value):
        try:
            unit = Unit.objects.get(id=value)
        except Unit.DoesNotExist:
            raise serializers.ValidationError("Invalid unit ID")
        
        # Check if user has already used all 3 attempts
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts_count = UnitTestSession.objects.filter(
                user=request.user,
                unit_id=value
            ).count()
            
            if attempts_count >= 3:
                raise serializers.ValidationError(
                    "Maximum 3 attempts reached for this unit"
                )
        
        return value


class UnitTestSessionSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a complete test"""
    session_id = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField()
    )
    time_taken_seconds = serializers.IntegerField(min_value=0)

    def validate_session_id(self, value):
        try:
            session = UnitTestSession.objects.get(id=value)
            if session.completed_at:
                raise serializers.ValidationError("Test already completed")
        except UnitTestSession.DoesNotExist:
            raise serializers.ValidationError("Invalid session ID")
        return value

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Answers cannot be empty")
        
        # Validate each answer has required fields
        for idx, answer in enumerate(value):
            if 'question_id' not in answer:
                raise serializers.ValidationError(f"Answer {idx} missing question_id")
            if 'student_answer' not in answer:
                raise serializers.ValidationError(f"Answer {idx} missing student_answer")
        
        return value


# ============================================================
# DOMAIN-SPECIFIC TEST ATTEMPT SERIALIZERS
# ============================================================

class VocabularyUnitTestAttemptSerializer(serializers.ModelSerializer):
    """Serializer for vocabulary-specific unit test attempts"""
    unit_test_session_info = serializers.SerializerMethodField()
    lesson_title = serializers.CharField(source='lesson.title', read_only=True, default=None)
    chunk_order = serializers.IntegerField(source='chunk.order', read_only=True, default=None)

    class Meta:
        model = VocabularyUnitTestAttempt
        fields = [
            "id",
            "user_id",
            "unit_test_session_id",
            "unit_test_session_info",
            "lesson_id",
            "lesson_title",
            "chunk_id",
            "chunk_order",
            "score_percent",
            "correct_answers",
            "total_questions",
            "questions_data",
            "created_at",
        ]
        read_only_fields = ["id", "user_id", "created_at"]

    def get_unit_test_session_info(self, obj):
        """Get basic info about the parent test session"""
        if obj.unit_test_session:
            return {
                'id': obj.unit_test_session.id,
                'attempt_number': obj.unit_test_session.attempt_number,
                'passed': obj.unit_test_session.passed,
                'completed_at': obj.unit_test_session.completed_at,
            }
        return None


# ============================================================
# PROGRESS & ANALYTICS SERIALIZERS
# ============================================================

class UnitTestDomainBreakdownSerializer(serializers.Serializer):
    """Breakdown of performance by domain for a test"""
    domain = serializers.CharField()
    correct = serializers.IntegerField()
    total = serializers.IntegerField()
    percentage = serializers.FloatField()
    questions = serializers.ListField(
        child=serializers.DictField()
    )


class UnitTestHistorySerializer(serializers.Serializer):
    """Complete test history for a user/unit"""
    unit_id = serializers.IntegerField()
    unit_title = serializers.CharField()
    
    # All attempts
    attempts = UnitTestSessionListSerializer(many=True)
    
    # Best attempt
    best_score = serializers.FloatField()
    best_attempt_number = serializers.IntegerField()
    
    # Latest attempt
    latest_score = serializers.FloatField()
    latest_passed = serializers.BooleanField()
    
    # Statistics
    average_score = serializers.FloatField()
    attempts_remaining = serializers.IntegerField()
    has_passed = serializers.BooleanField()
    
    # Domain mastery across attempts
    domain_mastery = serializers.DictField(
        child=serializers.FloatField()
    )


class UnitTestPerformanceSerializer(serializers.Serializer):
    """Detailed performance analytics for a test"""
    session_id = serializers.IntegerField()
    attempt_number = serializers.IntegerField()
    
    # Overall stats
    overall_score = serializers.FloatField()
    passed = serializers.BooleanField()
    time_spent_minutes = serializers.FloatField()
    
    # Domain breakdown
    by_domain = UnitTestDomainBreakdownSerializer(many=True)
    
    # Difficulty breakdown
    by_difficulty = serializers.DictField(
        child=serializers.DictField()
    )
    
    # Question-level analysis
    incorrect_questions = serializers.ListField(
        child=serializers.DictField()
    )
    slowest_questions = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Recommendations
    recommended_review = serializers.ListField(
        child=serializers.CharField()
    )


# ============================================================
# BULK OPERATION SERIALIZERS
# ============================================================

class UnitTestBulkQuestionCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating test questions"""
    session_id = serializers.IntegerField()
    questions = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_session_id(self, value):
        try:
            session = UnitTestSession.objects.get(id=value)
            if session.completed_at:
                raise serializers.ValidationError("Cannot add questions to completed test")
        except UnitTestSession.DoesNotExist:
            raise serializers.ValidationError("Invalid session ID")
        return value

    def validate_questions(self, value):
        if not value:
            raise serializers.ValidationError("Questions list cannot be empty")
        
        # Validate each question has required fields
        for idx, q_data in enumerate(value):
            required_fields = ['domain', 'question_type', 'question_text', 'correct_answer']
            for field in required_fields:
                if field not in q_data:
                    raise serializers.ValidationError(f"Question {idx} missing '{field}'")
            
            # Validate MCQ has options
            if q_data.get('question_type') == 'mcq' and 'options' not in q_data:
                raise serializers.ValidationError(f"MCQ Question {idx} missing options")
            
            # Validate domain-specific fields
            domain = q_data.get('domain')
            if domain == 'vocabulary' and 'vocabulary_item_id' not in q_data:
                raise serializers.ValidationError(f"Vocabulary Question {idx} missing vocabulary_item_id")
            elif domain == 'grammar' and 'grammar_concept_id' not in q_data:
                raise serializers.ValidationError(f"Grammar Question {idx} missing grammar_concept_id")
            elif domain == 'punctuation' and 'punctuation_mark_id' not in q_data:
                raise serializers.ValidationError(f"Punctuation Question {idx} missing punctuation_mark_id")
            elif domain == 'comprehension' and 'bloom_level' not in q_data:
                raise serializers.ValidationError(f"Comprehension Question {idx} missing bloom_level")
        
        return value


# ============================================================
# TEST GENERATION SERIALIZERS
# ============================================================

class TestGenerationConfigSerializer(serializers.Serializer):
    """Configuration for generating a new test"""
    unit_id = serializers.IntegerField()
    
    # Optional: customize question distribution
    questions_per_domain = serializers.DictField(
        child=serializers.IntegerField(),
        required=False,
        help_text="e.g., {'vocabulary': 5, 'grammar': 5, 'punctuation': 3}"
    )
    
    difficulty_distribution = serializers.DictField(
        child=serializers.IntegerField(),
        required=False,
        help_text="e.g., {'1': 2, '2': 3, '3': 3, '4': 1, '5': 1}"
    )
    
    include_domains = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of domains to include"
    )

    def validate_unit_id(self, value):
        try:
            Unit.objects.get(id=value)
        except Unit.DoesNotExist:
            raise serializers.ValidationError("Invalid unit ID")
        return value

    def validate_questions_per_domain(self, value):
        if value:
            valid_domains = [d[0] for d in UnitTestQuestion.DOMAIN_CHOICES]
            for domain in value.keys():
                if domain not in valid_domains:
                    raise serializers.ValidationError(f"Invalid domain: {domain}")
        return value

    def validate_include_domains(self, value):
        if value:
            valid_domains = [d[0] for d in UnitTestQuestion.DOMAIN_CHOICES]
            for domain in value:
                if domain not in valid_domains:
                    raise serializers.ValidationError(f"Invalid domain: {domain}")
        return value


# ============================================================
# LEGACY MODEL SERIALIZERS (For migration support)
# Only defined if legacy models are available
# ============================================================

if LEGACY_MODELS_AVAILABLE:
    class LegacyVocabularyTestSessionSerializer(serializers.Serializer):
        """Serializer for legacy vocabulary test sessions (read-only)"""
        id = serializers.IntegerField()
        student_id = serializers.CharField()
        chunk_id = serializers.IntegerField()
        started_at = serializers.DateTimeField()
        completed_at = serializers.DateTimeField(allow_null=True)
        total_questions = serializers.IntegerField()
        correct_answers = serializers.IntegerField()
        score_percentage = serializers.FloatField()
        passed = serializers.BooleanField()
        
        class Meta:
            fields = "__all__"


    class LegacyVocabularyTestQuestionSerializer(serializers.Serializer):
        """Serializer for legacy vocabulary test questions (read-only)"""
        id = serializers.IntegerField()
        session_id = serializers.IntegerField()
        vocab_item_id = serializers.IntegerField()
        question_type = serializers.CharField()
        question_text = serializers.CharField()
        options = serializers.JSONField()
        correct_answer = serializers.CharField()
        order = serializers.IntegerField()
        
        class Meta:
            fields = "__all__"


    class LegacyVocabularyTestAnswerSerializer(serializers.Serializer):
        """Serializer for legacy vocabulary test answers (read-only)"""
        id = serializers.IntegerField()
        question_id = serializers.IntegerField()
        selected_option = serializers.CharField()
        is_correct = serializers.BooleanField()
        answered_at = serializers.DateTimeField()
        time_taken_seconds = serializers.IntegerField(allow_null=True)
        
        class Meta:
            fields = "__all__"


    class LegacyVocabularyTestAttemptSerializer(serializers.Serializer):
        """Serializer for legacy vocabulary test attempts (read-only)"""
        id = serializers.IntegerField()
        user_id = serializers.IntegerField()
        lesson_id = serializers.IntegerField()
        chunk_id = serializers.IntegerField()
        score_percent = serializers.IntegerField()
        correct_answers = serializers.IntegerField()
        total_questions = serializers.IntegerField()
        created_at = serializers.DateTimeField()
        questions_data = serializers.JSONField(allow_null=True)
        
        class Meta:
            fields = "__all__"


    class LegacyToUnitTestMigrationSerializer(serializers.Serializer):
        """Serializer for mapping legacy test data to new unit test format"""
        legacy_session_id = serializers.IntegerField()
        unit_id = serializers.IntegerField()
        user_id = serializers.IntegerField()
        
        def validate_legacy_session_id(self, value):
            try:
                VocabularyTestSession.objects.get(id=value)
            except VocabularyTestSession.DoesNotExist:
                raise serializers.ValidationError("Invalid legacy session ID")
            return value
        
        def validate_unit_id(self, value):
            try:
                Unit.objects.get(id=value)
            except Unit.DoesNotExist:
                raise serializers.ValidationError("Invalid unit ID")
            return value
else:
    # Define dummy classes when legacy models aren't available
    class LegacyVocabularyTestSessionSerializer(serializers.Serializer):
        def __init__(self, *args, **kwargs):
            raise ImportError("Legacy vocabulary test models are not available")
    
    class LegacyVocabularyTestQuestionSerializer(serializers.Serializer):
        def __init__(self, *args, **kwargs):
            raise ImportError("Legacy vocabulary test models are not available")
    
    class LegacyVocabularyTestAnswerSerializer(serializers.Serializer):
        def __init__(self, *args, **kwargs):
            raise ImportError("Legacy vocabulary test models are not available")
    
    class LegacyVocabularyTestAttemptSerializer(serializers.Serializer):
        def __init__(self, *args, **kwargs):
            raise ImportError("Legacy vocabulary test models are not available")
    
    class LegacyToUnitTestMigrationSerializer(serializers.Serializer):
        def __init__(self, *args, **kwargs):
            raise ImportError("Legacy vocabulary test models are not available")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'UnitTestQuestionSerializer',
    'UnitTestQuestionListSerializer',
    'UnitTestQuestionMobileSerializer',
    'UnitTestAnswerSerializer',
    'UnitTestAnswerSubmitSerializer',
    'UnitTestAnswerMobileSerializer',
    'UnitTestSessionSerializer',
    'UnitTestSessionListSerializer',
    'UnitTestSessionCreateSerializer',
    'UnitTestSessionSubmitSerializer',
    'UnitTestSessionMobileSerializer',
    'UnitTestSessionActiveMobileSerializer',
    'VocabularyUnitTestAttemptSerializer',
    'UnitTestDomainBreakdownSerializer',
    'UnitTestHistorySerializer',
    'UnitTestHistoryMobileSerializer',
    'UnitTestPerformanceSerializer',
    'UnitTestBulkQuestionCreateSerializer',
    'TestGenerationConfigSerializer',
    'LegacyVocabularyTestSessionSerializer',
    'LegacyVocabularyTestQuestionSerializer',
    'LegacyVocabularyTestAnswerSerializer',
    'LegacyVocabularyTestAttemptSerializer',
    'LegacyToUnitTestMigrationSerializer',
]