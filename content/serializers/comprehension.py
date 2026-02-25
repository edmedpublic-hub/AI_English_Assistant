# serializers/comprehension.py

from rest_framework import serializers
from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionQuestion,
    ComprehensionPracticeAttempt,
    ComprehensionTestAttempt,
    ComprehensionQuestionAttempt,
    BloomLevel,
)


# ============================================================
# BASE VALIDATION MIXINS
# ============================================================

class QuestionTypeValidationMixin:
    """Mixin for question type validation logic"""

    def validate_question_type_specific(self, question_type, options, correct_answer):
        """Validate based on question type"""
        if question_type == ComprehensionQuestion.TYPE_MCQ:
            if not options:
                raise serializers.ValidationError({
                    "options": "MCQ questions must have options."
                })

            option_list = [opt.strip() for opt in options.splitlines() if opt.strip()]

            if len(option_list) < 2:
                raise serializers.ValidationError({
                    "options": "MCQ questions must have at least two options."
                })

            normalized_options = [o.strip().lower() for o in option_list]
            if not correct_answer or correct_answer.strip().lower() not in normalized_options:
                raise serializers.ValidationError({
                    "correct_answer": "Correct answer must exactly match one of the options."
                })

        elif question_type in [
            ComprehensionQuestion.TYPE_TRUE_FALSE,
            ComprehensionQuestion.TYPE_SHORT_ANSWER,
        ]:
            if not correct_answer or not correct_answer.strip():
                raise serializers.ValidationError({
                    "correct_answer": "This question type must define a correct answer."
                })

        # Open-ended questions don't need validation for correct_answer
        return True


# ============================================================
# TEACHING LAYER SERIALIZERS
# ============================================================

class ComprehensionQuestionSerializer(serializers.ModelSerializer, QuestionTypeValidationMixin):
    """Serializer for comprehension questions"""
    parsed_options = serializers.ListField(
        source='get_options_list',
        read_only=True
    )
    focus_title = serializers.CharField(
        source='focus.focus_title',
        read_only=True
    )
    level_display = serializers.CharField(
        source='focus.get_level_display',
        read_only=True
    )

    class Meta:
        model = ComprehensionQuestion
        fields = [
            "id",
            "focus_id",
            "focus_title",
            "question_text",
            "options",
            "parsed_options",
            "correct_answer",
            "question_type",
            "difficulty",
            "explanation",
            "level_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate based on question type"""
        request = self.context.get('request')
        if request and request.method in ['POST', 'PUT', 'PATCH']:
            question_type = data.get(
                'question_type',
                getattr(self.instance, 'question_type', None)
            )
            options = data.get('options', getattr(self.instance, 'options', None))
            correct_answer = data.get(
                'correct_answer',
                getattr(self.instance, 'correct_answer', '')
            )

            self.validate_question_type_specific(question_type, options, correct_answer)

        return data


class ChunkComprehensionFocusSerializer(serializers.ModelSerializer):
    """Detailed serializer for comprehension focus with nested questions"""
    questions = ComprehensionQuestionSerializer(many=True, read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    question_count = serializers.IntegerField(
        source='questions.count',
        read_only=True
    )
    
    # Progress stats for authenticated users
    practice_stats = serializers.SerializerMethodField()
    test_stats = serializers.SerializerMethodField()

    class Meta:
        model = ChunkComprehensionFocus
        fields = [
            "id",
            "chunk_id",
            "focus_title",
            "focus_description",
            "level",
            "level_display",
            "depth_level",
            "sequence_order",
            "questions",
            "question_count",
            "practice_stats",
            "test_stats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate sequence order matches Bloom's level"""
        level = data.get('level', getattr(self.instance, 'level', None))
        sequence_order = data.get(
            'sequence_order',
            getattr(self.instance, 'sequence_order', None)
        )

        expected_order = {
            BloomLevel.LITERAL: 1,
            BloomLevel.INFERENTIAL: 2,
            BloomLevel.EVALUATIVE: 3,
        }

        if level and sequence_order:
            if sequence_order != expected_order.get(level):
                raise serializers.ValidationError({
                    "sequence_order": (
                        f"{dict(BloomLevel.choices)[level]} focus must have "
                        f"sequence_order {expected_order[level]}."
                    )
                })

        return data

    def get_practice_stats(self, obj):
        """Get practice attempt statistics for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = obj.practice_attempts.filter(user=request.user)
            latest = attempts.order_by('-attempted_at').first()

            if latest:
                attempts_in_cycle = attempts.filter(
                    cycle_number=latest.cycle_number
                ).count()

                return {
                    'total_attempts': attempts.count(),
                    'latest_score': latest.score_percent,
                    'latest_attempt_number': latest.attempt_number,
                    'current_cycle': latest.cycle_number,
                    'attempts_used_in_cycle': attempts_in_cycle,
                    'attempts_remaining': 3 - attempts_in_cycle,
                    'passed_in_cycle': attempts.filter(
                        cycle_number=latest.cycle_number,
                        is_passed=True
                    ).exists(),
                }
            return {
                'total_attempts': 0,
                'latest_score': None,
                'latest_attempt_number': None,
                'current_cycle': 1,
                'attempts_used_in_cycle': 0,
                'attempts_remaining': 3,
                'passed_in_cycle': False,
            }
        return None

    def get_test_stats(self, obj):
        """Get test attempt statistics for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = obj.test_attempts.filter(user=request.user)
            latest = attempts.order_by('-created_at').first()

            if latest:
                attempts_in_cycle = attempts.filter(
                    cycle_number=latest.cycle_number
                ).count()

                mastered_attempt = attempts.filter(is_mastered=True).first()

                return {
                    'total_attempts': attempts.count(),
                    'latest_score': latest.score_percent,
                    'latest_attempt_number': latest.attempt_number,
                    'current_cycle': latest.cycle_number,
                    'attempts_used_in_cycle': attempts_in_cycle,
                    'attempts_remaining': 3 - attempts_in_cycle,
                    'is_mastered': attempts.filter(is_mastered=True).exists(),
                    'mastered_at': mastered_attempt.created_at if mastered_attempt else None,
                }
            return {
                'total_attempts': 0,
                'latest_score': None,
                'latest_attempt_number': None,
                'current_cycle': 1,
                'attempts_used_in_cycle': 0,
                'attempts_remaining': 3,
                'is_mastered': False,
                'mastered_at': None,
            }
        return None


class ChunkComprehensionFocusListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for comprehension focus listings"""
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    question_count = serializers.IntegerField(
        source='questions.count',
        read_only=True
    )

    class Meta:
        model = ChunkComprehensionFocus
        fields = [
            "id",
            "focus_title",
            "level",
            "level_display",
            "depth_level",
            "sequence_order",
            "question_count",
        ]


# ============================================================
# PRACTICE LAYER SERIALIZERS
# ============================================================

class ComprehensionPracticeAttemptSerializer(serializers.ModelSerializer):
    """Serializer for practice attempt records"""
    focus_details = ChunkComprehensionFocusListSerializer(
        source='focus',
        read_only=True
    )
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = ComprehensionPracticeAttempt
        fields = [
            "id",
            "user_id",
            "username",
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
            "is_passed",
            "score_percent",
            "correct_answers",
        ]


class ComprehensionPracticeAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a practice attempt"""
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(allow_blank=True, required=False)
        ),
        min_length=1
    )
    time_taken_seconds = serializers.IntegerField(
        min_value=0,
        required=False,
        allow_null=True
    )

    def validate_answers(self, value):
        """Validate each answer has required fields"""
        for idx, answer in enumerate(value):
            if 'question_id' not in answer:
                raise serializers.ValidationError(
                    f"Answer at index {idx} missing 'question_id'"
                )

            # Ensure at least one answer field is present
            has_answer = (
                'selected_answer' in answer or
                'open_ended_answer' in answer
            )
            if not has_answer:
                raise serializers.ValidationError(
                    f"Answer at index {idx} must have either "
                    "'selected_answer' or 'open_ended_answer'"
                )

        return value


# ============================================================
# TEST LAYER SERIALIZERS
# ============================================================

class ComprehensionTestAttemptSerializer(serializers.ModelSerializer):
    """Serializer for test attempt records"""
    focus_details = ChunkComprehensionFocusListSerializer(
        source='focus',
        read_only=True
    )
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    is_passed = serializers.BooleanField(
        source='is_mastered',
        read_only=True
    )

    class Meta:
        model = ComprehensionTestAttempt
        fields = [
            "id",
            "user_id",
            "username",
            "focus_id",
            "focus_details",
            "attempt_number",
            "cycle_number",
            "score_percent",
            "is_mastered",
            "is_passed",
            "correct_answers",
            "total_questions",
            "questions_data",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "created_at",
            "is_mastered",
            "score_percent",
            "correct_answers",
        ]


class ComprehensionTestAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a test attempt"""
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(allow_blank=True, required=False)
        ),
        min_length=1
    )
    time_taken_seconds = serializers.IntegerField(
        min_value=0,
        required=False,
        allow_null=True
    )

    def validate_answers(self, value):
        """Validate each answer has required fields"""
        for idx, answer in enumerate(value):
            if 'question_id' not in answer:
                raise serializers.ValidationError(
                    f"Answer at index {idx} missing 'question_id'"
                )

            has_answer = (
                'selected_answer' in answer or
                'open_ended_answer' in answer
            )
            if not has_answer:
                raise serializers.ValidationError(
                    f"Answer at index {idx} must have either "
                    "'selected_answer' or 'open_ended_answer'"
                )

        return value


# ============================================================
# QUESTION ATTEMPT SERIALIZERS (Analytics)
# ============================================================

class ComprehensionQuestionAttemptSerializer(serializers.ModelSerializer):
    """Basic serializer for question attempts"""
    question_text = serializers.CharField(
        source='question.question_text',
        read_only=True
    )
    question_type = serializers.CharField(
        source='question.question_type',
        read_only=True
    )
    correct_answer = serializers.CharField(
        source='question.correct_answer',
        read_only=True
    )
    focus_title = serializers.CharField(
        source='question.focus.focus_title',
        read_only=True
    )
    level = serializers.CharField(
        source='question.focus.level',
        read_only=True
    )

    class Meta:
        model = ComprehensionQuestionAttempt
        fields = [
            "id",
            "user_id",
            "question_id",
            "question_text",
            "question_type",
            "correct_answer",
            "focus_title",
            "level",
            "cycle_number",
            "attempt_number",
            "selected_answer",
            "open_ended_answer",
            "is_correct",
            "time_taken_seconds",
            "attempted_at",
        ]
        read_only_fields = ["id", "user_id", "attempted_at"]


class ComprehensionQuestionAttemptDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with practice/test context"""
    question = ComprehensionQuestionSerializer(read_only=True)
    practice_attempt_id = serializers.IntegerField(
        source='practice_attempt.id',
        read_only=True
    )
    test_attempt_id = serializers.IntegerField(
        source='test_attempt.id',
        read_only=True
    )

    class Meta:
        model = ComprehensionQuestionAttempt
        fields = [
            "id",
            "user_id",
            "question",
            "practice_attempt_id",
            "test_attempt_id",
            "cycle_number",
            "attempt_number",
            "selected_answer",
            "open_ended_answer",
            "is_correct",
            "time_taken_seconds",
            "attempted_at",
        ]
        read_only_fields = ["id", "user_id", "attempted_at"]


# ============================================================
# PROGRESS & MASTERY SERIALIZERS
# ============================================================

class ComprehensionBloomLevelProgressSerializer(serializers.Serializer):
    """Progress tracking by Bloom's level"""
    level = serializers.CharField()
    level_display = serializers.CharField()

    # Focus counts
    total_focuses = serializers.IntegerField(min_value=0)
    mastered_focuses = serializers.IntegerField(min_value=0)
    in_progress_focuses = serializers.IntegerField(min_value=0)
    not_started_focuses = serializers.IntegerField(min_value=0)

    # Practice stats
    practice_attempts = serializers.IntegerField(min_value=0)
    average_practice_score = serializers.FloatField(
        min_value=0.0,
        max_value=100.0
    )

    # Test stats
    test_attempts = serializers.IntegerField(min_value=0)
    average_test_score = serializers.FloatField(
        min_value=0.0,
        max_value=100.0
    )

    # Mastery percentage
    mastery_percentage = serializers.FloatField(
        min_value=0.0,
        max_value=100.0
    )


class ComprehensionFocusProgressSerializer(serializers.Serializer):
    """Detailed progress for a specific comprehension focus"""
    focus_id = serializers.IntegerField()
    focus_title = serializers.CharField()
    level = serializers.CharField()
    depth_level = serializers.IntegerField()

    # Practice tracking
    current_practice_cycle = serializers.IntegerField(min_value=1)
    current_practice_attempt = serializers.IntegerField(min_value=0)
    practice_passed_in_cycle = serializers.BooleanField()
    practice_attempts_remaining = serializers.IntegerField(min_value=0, max_value=3)

    # Test tracking
    current_test_cycle = serializers.IntegerField(min_value=1)
    current_test_attempt = serializers.IntegerField(min_value=0)
    is_mastered = serializers.BooleanField()
    test_attempts_remaining = serializers.IntegerField(min_value=0, max_value=3)

    # Question-level analytics
    questions_correct = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
        allow_empty=True
    )
    questions_incorrect = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
        allow_empty=True
    )

    # Next steps
    next_action = serializers.ChoiceField(
        choices=['practice', 'test', 'review', 'mastered']
    )
    next_action_details = serializers.DictField(allow_empty=True)


# ============================================================
# BULK OPERATION SERIALIZERS
# ============================================================

class ComprehensionBulkQuestionCreateSerializer(serializers.Serializer, QuestionTypeValidationMixin):
    """Serializer for bulk creating questions"""
    focus_id = serializers.IntegerField()
    questions = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )

    def validate_focus_id(self, value):
        """Validate focus exists"""
        try:
            ChunkComprehensionFocus.objects.get(id=value)
        except ChunkComprehensionFocus.DoesNotExist:
            raise serializers.ValidationError("Invalid comprehension focus ID")
        return value

    def validate_questions(self, value):
        """Validate each question in the bulk create list"""
        for idx, question_data in enumerate(value):
            # Required fields
            if 'question_text' not in question_data:
                raise serializers.ValidationError(
                    f"Question at index {idx} missing 'question_text'"
                )
            if 'question_type' not in question_data:
                raise serializers.ValidationError(
                    f"Question at index {idx} missing 'question_type'"
                )

            # Validate based on question type
            q_type = question_data.get('question_type')
            options = question_data.get('options', '')
            correct_answer = question_data.get('correct_answer', '')

            try:
                self.validate_question_type_specific(q_type, options, correct_answer)
            except serializers.ValidationError as e:
                # Re-raise with index context
                raise serializers.ValidationError(
                    f"Question at index {idx}: {str(e.detail)}"
                )

        return value