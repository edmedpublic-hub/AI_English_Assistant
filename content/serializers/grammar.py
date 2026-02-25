from rest_framework import serializers
from content.models.grammar import (
    GrammarConcept, GrammarRule, GrammarExample,
    ChunkGrammarFocus, GrammarQuestion,
    GrammarPracticeAttempt, GrammarTestAttempt,
    GrammarQuestionAttempt
)
from django.db import models


# ============================================================
# KNOWLEDGE LAYER SERIALIZERS
# ============================================================

class GrammarRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarRule
        fields = [
            "id",
            "rule_text",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GrammarExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarExample
        fields = [
            "id",
            "sentence",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GrammarConceptSerializer(serializers.ModelSerializer):
    rules = GrammarRuleSerializer(many=True, read_only=True)
    examples = serializers.SerializerMethodField()
    teaching_instances_count = serializers.IntegerField(
        source='teaching_instances.count', 
        read_only=True
    )

    class Meta:
        model = GrammarConcept
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "category",
            "order_index",
            "rules",
            "examples",
            "teaching_instances_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_examples(self, obj):
        """Get examples through rules"""
        examples = GrammarExample.objects.filter(rule__concept=obj)
        return GrammarExampleSerializer(examples, many=True).data


class GrammarConceptListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for concept listings"""
    class Meta:
        model = GrammarConcept
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "order_index",
        ]


# ============================================================
# TEACHING LAYER SERIALIZERS
# ============================================================

class GrammarQuestionSerializer(serializers.ModelSerializer):
    parsed_options = serializers.ListField(
        source='get_options_list',
        read_only=True
    )

    class Meta:
        model = GrammarQuestion
        fields = [
            "id",
            "question_text",
            "options",
            "parsed_options",
            "correct_answer",
            "question_type",
            "difficulty",
            "explanation",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validation for MCQ questions"""
        request = self.context.get('request')
        if request and request.method in ['POST', 'PUT', 'PATCH']:
            # Create a temporary instance for validation
            question_type = data.get('question_type', getattr(self.instance, 'question_type', None))
            options = data.get('options', getattr(self.instance, 'options', None))
            correct_answer = data.get('correct_answer', getattr(self.instance, 'correct_answer', ''))

            if question_type == GrammarQuestion.TYPE_MCQ:
                if not options:
                    raise serializers.ValidationError({
                        "options": "MCQ questions must have options."
                    })

                option_list = [opt.strip() for opt in options.splitlines() if opt.strip()]
                
                if len(option_list) < 2:
                    raise serializers.ValidationError({
                        "options": "MCQ questions must have at least two options."
                    })

                if correct_answer not in option_list:
                    raise serializers.ValidationError({
                        "correct_answer": "Correct answer must exactly match one of the options."
                    })
            else:
                if not correct_answer.strip():
                    raise serializers.ValidationError({
                        "correct_answer": "Non-MCQ questions must define a correct answer."
                    })
        
        return data


class ChunkGrammarFocusSerializer(serializers.ModelSerializer):
    concept_details = GrammarConceptListSerializer(source='concept', read_only=True)
    questions = GrammarQuestionSerializer(many=True, read_only=True)
    practice_stats = serializers.SerializerMethodField()
    test_stats = serializers.SerializerMethodField()

    class Meta:
        model = ChunkGrammarFocus
        fields = [
            "id",
            "chunk_id",
            "focus_title",
            "focus_description",
            "depth_level",
            "sequence_order",
            "concept",
            "concept_details",
            "questions",
            "practice_stats",
            "test_stats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_practice_stats(self, obj):
        """Get practice attempt statistics for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = obj.practice_attempts.filter(user=request.user)
            latest = attempts.order_by('-attempted_at').first()
            
            return {
                'total_attempts': attempts.count(),
                'latest_score': latest.score_percent if latest else None,
                'latest_attempt_number': latest.attempt_number if latest else None,
                'current_cycle': latest.cycle_number if latest else 1,
                'passed_in_cycle': attempts.filter(
                    cycle_number=latest.cycle_number if latest else 1,
                    is_passed=True
                ).exists() if latest else False,
            }
        return None

    def get_test_stats(self, obj):
        """Get test attempt statistics for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = obj.test_attempts.filter(user=request.user)
            latest = attempts.order_by('-created_at').first()
            
            return {
                'total_attempts': attempts.count(),
                'latest_score': latest.score_percent if latest else None,
                'latest_attempt_number': latest.attempt_number if latest else None,
                'current_cycle': latest.cycle_number if latest else 1,
                'is_mastered': attempts.filter(is_mastered=True).exists(),
                'mastered_at': attempts.filter(is_mastered=True).first().created_at if attempts.filter(is_mastered=True).exists() else None,
            }
        return None


class ChunkGrammarFocusListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for grammar focus listings"""
    concept_name = serializers.CharField(source='concept.name', read_only=True)
    
    class Meta:
        model = ChunkGrammarFocus
        fields = [
            "id",
            "focus_title",
            "depth_level",
            "sequence_order",
            "concept_name",
        ]


# ============================================================
# PRACTICE LAYER SERIALIZERS
# ============================================================

class GrammarPracticeAttemptSerializer(serializers.ModelSerializer):
    focus_details = ChunkGrammarFocusListSerializer(source='focus', read_only=True)
    
    class Meta:
        model = GrammarPracticeAttempt
        fields = [
            "id",
            "user_id",
            "focus_id",
            "focus_details",
            "attempt_number",
            "cycle_number",
            "score_percent",
            "is_passed",
            "correct_answers",
            "total_questions",
            "questions_data",
            "attempted_at",
        ]
        read_only_fields = [
            "id", 
            "user_id", 
            "attempted_at", 
            "is_passed"
        ]


class GrammarPracticeAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a practice attempt"""
    focus_id = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    time_taken_seconds = serializers.IntegerField(min_value=0, required=False)

    def validate_focus_id(self, value):
        try:
            ChunkGrammarFocus.objects.get(id=value)
        except ChunkGrammarFocus.DoesNotExist:
            raise serializers.ValidationError("Invalid grammar focus ID")
        return value

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Answers cannot be empty")
        
        # Validate each answer has required fields
        for idx, answer in enumerate(value):
            if 'question_id' not in answer:
                raise serializers.ValidationError(f"Answer {idx} missing question_id")
            if 'selected_answer' not in answer:
                raise serializers.ValidationError(f"Answer {idx} missing selected_answer")
        
        return value


# ============================================================
# TEST LAYER SERIALIZERS
# ============================================================

class GrammarTestAttemptSerializer(serializers.ModelSerializer):
    focus_details = ChunkGrammarFocusListSerializer(source='focus', read_only=True)
    is_passed = serializers.BooleanField(source='is_mastered', read_only=True)

    class Meta:
        model = GrammarTestAttempt
        fields = [
            "id",
            "user_id",
            "focus_id",
            "focus_details",
            "attempt_number",
            "cycle_number",
            "score_percent",
            "is_mastered",
            "is_passed",
            "correct_answers",
            "total_questions",
            "questions_snapshot",
            "created_at",
        ]
        read_only_fields = [
            "id", 
            "user_id", 
            "created_at", 
            "is_mastered"
        ]


class GrammarTestAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a test attempt"""
    focus_id = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    time_taken_seconds = serializers.IntegerField(min_value=0, required=False)

    def validate_focus_id(self, value):
        try:
            ChunkGrammarFocus.objects.get(id=value)
        except ChunkGrammarFocus.DoesNotExist:
            raise serializers.ValidationError("Invalid grammar focus ID")
        return value

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Answers cannot be empty")
        
        for idx, answer in enumerate(value):
            if 'question_id' not in answer:
                raise serializers.ValidationError(f"Answer {idx} missing question_id")
            if 'selected_answer' not in answer:
                raise serializers.ValidationError(f"Answer {idx} missing selected_answer")
        
        return value


# ============================================================
# QUESTION ATTEMPT SERIALIZERS (Analytics)
# ============================================================

class GrammarQuestionAttemptSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    correct_answer = serializers.CharField(source='question.correct_answer', read_only=True)

    class Meta:
        model = GrammarQuestionAttempt
        fields = [
            "id",
            "user_id",
            "question_id",
            "question_text",
            "correct_answer",
            "selected_answer",
            "is_correct",
            "time_taken_seconds",
            "attempted_at",
        ]
        read_only_fields = ["id", "user_id", "attempted_at"]


class GrammarQuestionAttemptDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with practice/test context"""
    question = GrammarQuestionSerializer(read_only=True)
    practice_attempt_id = serializers.IntegerField(source='practice_attempt.id', read_only=True)
    test_attempt_id = serializers.IntegerField(source='test_attempt.id', read_only=True)

    class Meta:
        model = GrammarQuestionAttempt
        fields = [
            "id",
            "user_id",
            "question",
            "practice_attempt_id",
            "test_attempt_id",
            "selected_answer",
            "is_correct",
            "time_taken_seconds",
            "attempted_at",
        ]
        read_only_fields = ["id", "user_id", "attempted_at"]


# ============================================================
# PROGRESS & MASTERY SERIALIZERS
# ============================================================

class GrammarConceptProgressSerializer(serializers.Serializer):
    """Tracks progress on a specific concept"""
    concept_id = serializers.IntegerField()
    concept_name = serializers.CharField()
    category = serializers.CharField()
    
    # Practice stats
    practice_attempts = serializers.IntegerField()
    best_practice_score = serializers.FloatField()
    latest_practice_score = serializers.FloatField()
    
    # Test stats
    test_attempts = serializers.IntegerField()
    best_test_score = serializers.FloatField()
    is_mastered = serializers.BooleanField()
    
    # Mastery
    mastery_status = serializers.CharField()  # 'not_started', 'in_progress', 'mastered'
    last_attempted = serializers.DateTimeField(allow_null=True)


class GrammarFocusProgressSerializer(serializers.Serializer):
    """Detailed progress for a specific grammar focus"""
    focus_id = serializers.IntegerField()
    focus_title = serializers.CharField()
    depth_level = serializers.IntegerField()
    
    # Practice tracking
    current_practice_cycle = serializers.IntegerField()
    current_practice_attempt = serializers.IntegerField()
    practice_passed_in_cycle = serializers.BooleanField()
    practice_attempts_remaining = serializers.IntegerField()
    
    # Test tracking
    current_test_cycle = serializers.IntegerField()
    current_test_attempt = serializers.IntegerField()
    is_mastered = serializers.BooleanField()
    test_attempts_remaining = serializers.IntegerField()
    
    # Next steps
    next_action = serializers.CharField()  # 'practice', 'test', 'review', 'mastered'
    next_action_details = serializers.DictField()


# ============================================================
# BULK OPERATION SERIALIZERS
# ============================================================

class GrammarBulkQuestionCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating questions"""
    focus_id = serializers.IntegerField()
    questions = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_focus_id(self, value):
        try:
            ChunkGrammarFocus.objects.get(id=value)
        except ChunkGrammarFocus.DoesNotExist:
            raise serializers.ValidationError("Invalid grammar focus ID")
        return value

    def validate_questions(self, value):
        if not value:
            raise serializers.ValidationError("Questions list cannot be empty")
        
        for idx, question_data in enumerate(value):
            # Basic validation for each question
            if 'question_text' not in question_data:
                raise serializers.ValidationError(f"Question {idx} missing question_text")
            if 'correct_answer' not in question_data:
                raise serializers.ValidationError(f"Question {idx} missing correct_answer")
        
        return value