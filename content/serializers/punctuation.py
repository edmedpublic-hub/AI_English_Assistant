# serializers/punctuation.py

from rest_framework import serializers
from content.models.punctuation import (
    PunctuationMark, PunctuationRule, PunctuationExample,
    ChunkPunctuationFocus, ChunkPunctuationFocusRule,
    PunctuationPracticeAttempt, PunctuationTestAttempt,
    PunctuationQuestion
)
from django.db import models


# ============================================================
# KNOWLEDGE LAYER SERIALIZERS
# ============================================================

class PunctuationMarkSerializer(serializers.ModelSerializer):
    rules_count = serializers.IntegerField(source='rules.count', read_only=True)
    
    class Meta:
        model = PunctuationMark
        fields = [
            "id",
            "name",
            "symbol",
            "description",
            "order_index",
            "rules_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PunctuationRuleSerializer(serializers.ModelSerializer):
    mark_details = PunctuationMarkSerializer(source='mark', read_only=True)
    examples_count = serializers.IntegerField(source='examples.count', read_only=True)
    
    class Meta:
        model = PunctuationRule
        fields = [
            "id",
            "mark_id",
            "mark_details",
            "rule_text",
            "examples_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PunctuationExampleSerializer(serializers.ModelSerializer):
    rule_text = serializers.CharField(source='rule.rule_text', read_only=True)
    mark_symbol = serializers.CharField(source='rule.mark.symbol', read_only=True)
    
    class Meta:
        model = PunctuationExample
        fields = [
            "id",
            "rule_id",
            "rule_text",
            "mark_symbol",
            "sentence",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PunctuationMarkDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for punctuation mark with all related data"""
    rules = PunctuationRuleSerializer(many=True, read_only=True)
    
    class Meta:
        model = PunctuationMark
        fields = [
            "id",
            "name",
            "symbol",
            "description",
            "order_index",
            "rules",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PunctuationRuleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for punctuation rule with examples"""
    mark_details = PunctuationMarkSerializer(source='mark', read_only=True)
    examples = PunctuationExampleSerializer(many=True, read_only=True)
    
    class Meta:
        model = PunctuationRule
        fields = [
            "id",
            "mark_id",
            "mark_details",
            "rule_text",
            "examples",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ============================================================
# TEACHING LAYER SERIALIZERS
# ============================================================

class PunctuationQuestionSerializer(serializers.ModelSerializer):
    options_list = serializers.ListField(
        source='options_list',
        read_only=True
    )
    focus_title = serializers.CharField(source='focus.focus_title', read_only=True)
    mark_symbol = serializers.CharField(source='focus.mark.symbol', read_only=True)

    class Meta:
        model = PunctuationQuestion
        fields = [
            "id",
            "focus_id",
            "focus_title",
            "mark_symbol",
            "question_text",
            "options",
            "options_list",
            "correct_answer",
            "question_type",
            "difficulty",
            "explanation",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate MCQ questions have correct answer in options."""
        request = self.context.get('request')
        if request and request.method in ['POST', 'PUT', 'PATCH']:
            question_type = data.get('question_type', getattr(self.instance, 'question_type', None))
            options = data.get('options', getattr(self.instance, 'options', ''))
            correct_answer = data.get('correct_answer', getattr(self.instance, 'correct_answer', ''))

            if question_type == 'mcq':
                if not options:
                    raise serializers.ValidationError({
                        "options": "MCQ questions must have options."
                    })

                # Parse options using pipe separator
                option_list = [opt.strip() for opt in options.split('|') if opt.strip()]
                
                if len(option_list) < 2:
                    raise serializers.ValidationError({
                        "options": "MCQ questions must have at least two options."
                    })

                if correct_answer not in option_list:
                    raise serializers.ValidationError({
                        "correct_answer": "Correct answer must match one of the options."
                    })
        
        return data


class ChunkPunctuationFocusRuleSerializer(serializers.ModelSerializer):
    rule_details = PunctuationRuleSerializer(source='rule', read_only=True)
    
    class Meta:
        model = ChunkPunctuationFocusRule
        fields = [
            "id",
            "focus_id",
            "rule_id",
            "rule_details",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChunkPunctuationFocusSerializer(serializers.ModelSerializer):
    mark_details = PunctuationMarkSerializer(source='mark', read_only=True)
    focus_rules = ChunkPunctuationFocusRuleSerializer(many=True, read_only=True)
    questions = PunctuationQuestionSerializer(many=True, read_only=True)
    practice_stats = serializers.SerializerMethodField()
    test_stats = serializers.SerializerMethodField()
    question_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = ChunkPunctuationFocus
        fields = [
            "id",
            "chunk_id",
            "mark_id",
            "mark_details",
            "focus_title",
            "focus_description",
            "depth_level",
            "sequence_order",
            "focus_rules",
            "questions",
            "question_count",
            "practice_stats",
            "test_stats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_sequence_order(self, value):
        """Validate sequence order is between 1 and 3"""
        if value < 1 or value > 3:
            raise serializers.ValidationError("Sequence order must be between 1 and 3")
        return value

    def validate_depth_level(self, value):
        """Validate depth level is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Depth level must be between 1 and 5")
        return value

    def get_practice_stats(self, obj):
        """Get practice attempt statistics for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = obj.practice_attempts.filter(user=request.user)
            latest = attempts.order_by('-created_at').first()
            
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


class ChunkPunctuationFocusListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for punctuation focus listings"""
    mark_symbol = serializers.CharField(source='mark.symbol', read_only=True)
    mark_name = serializers.CharField(source='mark.name', read_only=True)
    
    class Meta:
        model = ChunkPunctuationFocus
        fields = [
            "id",
            "focus_title",
            "mark_symbol",
            "mark_name",
            "depth_level",
            "sequence_order",
        ]


# ============================================================
# PRACTICE LAYER SERIALIZERS
# ============================================================

class PunctuationPracticeAttemptSerializer(serializers.ModelSerializer):
    focus_details = ChunkPunctuationFocusListSerializer(source='focus', read_only=True)
    
    class Meta:
        model = PunctuationPracticeAttempt
        fields = [
            "id",
            "user_id",
            "focus_id",
            "focus_details",
            "attempt_number",
            "cycle_number",
            "score_percent",
            "is_passed",
            "questions_data",
            "created_at",
        ]
        read_only_fields = [
            "id", 
            "user_id", 
            "created_at", 
            "is_passed"
        ]


class PunctuationPracticeAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a practice attempt"""
    focus_id = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(allow_blank=True)
        )
    )
    time_taken_seconds = serializers.IntegerField(min_value=0, required=False)

    def validate_focus_id(self, value):
        try:
            ChunkPunctuationFocus.objects.get(id=value)
        except ChunkPunctuationFocus.DoesNotExist:
            raise serializers.ValidationError("Invalid punctuation focus ID")
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

class PunctuationTestAttemptSerializer(serializers.ModelSerializer):
    focus_details = ChunkPunctuationFocusListSerializer(source='focus', read_only=True)
    is_passed = serializers.BooleanField(source='is_mastered', read_only=True)

    class Meta:
        model = PunctuationTestAttempt
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
            "total_questions",
            "correct_answers",
            "questions_data",
            "created_at",
        ]
        read_only_fields = [
            "id", 
            "user_id", 
            "created_at", 
            "is_mastered"
        ]


class PunctuationTestAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a test attempt"""
    focus_id = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(allow_blank=True)
        )
    )
    time_taken_seconds = serializers.IntegerField(min_value=0, required=False)

    def validate_focus_id(self, value):
        try:
            ChunkPunctuationFocus.objects.get(id=value)
        except ChunkPunctuationFocus.DoesNotExist:
            raise serializers.ValidationError("Invalid punctuation focus ID")
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
# PROGRESS & MASTERY SERIALIZERS
# ============================================================

class PunctuationMarkProgressSerializer(serializers.Serializer):
    """Progress tracking by punctuation mark"""
    mark_id = serializers.IntegerField()
    mark_symbol = serializers.CharField()
    mark_name = serializers.CharField()
    
    # Focus counts
    total_focuses = serializers.IntegerField()
    mastered_focuses = serializers.IntegerField()
    in_progress_focuses = serializers.IntegerField()
    not_started_focuses = serializers.IntegerField()
    
    # Practice stats
    practice_attempts = serializers.IntegerField()
    average_practice_score = serializers.FloatField()
    
    # Test stats
    test_attempts = serializers.IntegerField()
    average_test_score = serializers.FloatField()
    
    # Mastery percentage
    mastery_percentage = serializers.FloatField()


class PunctuationFocusProgressSerializer(serializers.Serializer):
    """Detailed progress for a specific punctuation focus"""
    focus_id = serializers.IntegerField()
    focus_title = serializers.CharField()
    mark_symbol = serializers.CharField()
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
    
    # Question-level performance by type
    question_performance = serializers.DictField(
        child=serializers.DictField()
    )
    
    # Next steps
    next_action = serializers.CharField()  # 'practice', 'test', 'review', 'mastered'
    next_action_details = serializers.DictField()


# ============================================================
# BULK OPERATION SERIALIZERS
# ============================================================

class PunctuationBulkQuestionCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating questions"""
    focus_id = serializers.IntegerField()
    questions = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_focus_id(self, value):
        try:
            ChunkPunctuationFocus.objects.get(id=value)
        except ChunkPunctuationFocus.DoesNotExist:
            raise serializers.ValidationError("Invalid punctuation focus ID")
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
            if 'question_type' not in question_data:
                raise serializers.ValidationError(f"Question {idx} missing question_type")
            
            # Type-specific validation
            q_type = question_data.get('question_type')
            if q_type == 'mcq' and 'options' not in question_data:
                raise serializers.ValidationError(f"MCQ Question {idx} missing options")
        
        return value


class PunctuationBulkFocusRuleCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating focus-rule mappings"""
    focus_id = serializers.IntegerField()
    rule_ids = serializers.ListField(
        child=serializers.IntegerField()
    )

    def validate_focus_id(self, value):
        try:
            ChunkPunctuationFocus.objects.get(id=value)
        except ChunkPunctuationFocus.DoesNotExist:
            raise serializers.ValidationError("Invalid punctuation focus ID")
        return value

    def validate_rule_ids(self, value):
        if not value:
            raise serializers.ValidationError("Rule IDs list cannot be empty")
        
        # Validate all rule IDs exist
        existing_rules = PunctuationRule.objects.filter(id__in=value)
        if existing_rules.count() != len(value):
            invalid_ids = set(value) - set(existing_rules.values_list('id', flat=True))
            raise serializers.ValidationError(f"Invalid rule IDs: {invalid_ids}")
        
        return value