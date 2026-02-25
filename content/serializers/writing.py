# serializers/writing.py

from rest_framework import serializers
from content.models.writing import (
    ChunkWritingFocus,
    UnitWritingTask,
    WritingPrompt,
    WritingPracticeAttempt,
    WritingTestAttempt
)
from content.models.core import LessonChunk, Unit
from django.db import models
from django.core.exceptions import ValidationError


# ============================================================
# CHUNK-LEVEL FOCUS SERIALIZERS
# ============================================================

class ChunkWritingFocusSerializer(serializers.ModelSerializer):
    prompts_count = serializers.IntegerField(source='prompts.count', read_only=True)
    practice_stats = serializers.SerializerMethodField()
    test_stats = serializers.SerializerMethodField()
    chunk_title = serializers.CharField(source='chunk.lesson.title', read_only=True, default="")

    class Meta:
        model = ChunkWritingFocus
        fields = [
            "id",
            "chunk_id",
            "chunk_title",
            "focus_title",
            "focus_description",
            "depth_level",
            "sequence_order",
            "prompts_count",
            "practice_stats",
            "test_stats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_depth_level(self, value):
        """Validate depth level is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Depth level must be between 1 and 5")
        return value

    def validate_sequence_order(self, value):
        """Validate sequence order is between 1 and 3"""
        if value < 1 or value > 3:
            raise serializers.ValidationError("Sequence order must be between 1 and 3")
        return value

    def get_practice_stats(self, obj):
        """Get practice attempt statistics for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = WritingPracticeAttempt.objects.filter(
                user=request.user,
                focus=obj
            )
            latest = attempts.order_by('-created_at').first()
            
            return {
                'total_attempts': attempts.count(),
                'latest_score': latest.keyword_match_score if latest else None,
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
                'latest_score': latest.overall_score if latest else None,
                'latest_attempt_number': latest.attempt_number if latest else None,
                'current_cycle': latest.cycle_number if latest else 1,
                'is_mastered': attempts.filter(is_mastered=True).exists(),
                'mastered_at': attempts.filter(is_mastered=True).first().created_at if attempts.filter(is_mastered=True).exists() else None,
            }
        return None


class ChunkWritingFocusListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for chunk writing focus listings"""
    
    class Meta:
        model = ChunkWritingFocus
        fields = [
            "id",
            "focus_title",
            "depth_level",
            "sequence_order",
        ]


# ============================================================
# UNIT-LEVEL TASK SERIALIZERS
# ============================================================

class UnitWritingTaskSerializer(serializers.ModelSerializer):
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    prompts_count = serializers.IntegerField(source='prompts.count', read_only=True)
    test_stats = serializers.SerializerMethodField()
    unit_title = serializers.CharField(source='unit.title', read_only=True)

    class Meta:
        model = UnitWritingTask
        fields = [
            "id",
            "unit_id",
            "unit_title",
            "task_title",
            "task_description",
            "stage",
            "stage_display",
            "difficulty_level",
            "order",
            "prompts_count",
            "test_stats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_difficulty_level(self, value):
        """Validate difficulty level is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Difficulty level must be between 1 and 5")
        return value

    def get_test_stats(self, obj):
        """Get test attempt statistics for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = obj.test_attempts.filter(user=request.user)
            latest = attempts.order_by('-created_at').first()
            
            return {
                'total_attempts': attempts.count(),
                'latest_score': latest.overall_score if latest else None,
                'latest_attempt_number': latest.attempt_number if latest else None,
                'current_cycle': latest.cycle_number if latest else 1,
                'is_mastered': attempts.filter(is_mastered=True).exists(),
                'mastered_at': attempts.filter(is_mastered=True).first().created_at if attempts.filter(is_mastered=True).exists() else None,
            }
        return None


class UnitWritingTaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for unit task listings"""
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    
    class Meta:
        model = UnitWritingTask
        fields = [
            "id",
            "task_title",
            "stage",
            "stage_display",
            "difficulty_level",
            "order",
        ]


# ============================================================
# WRITING PROMPT SERIALIZERS
# ============================================================

class WritingPromptSerializer(serializers.ModelSerializer):
    prompt_type_display = serializers.CharField(
        source='get_prompt_type_display', 
        read_only=True
    )
    focus_title = serializers.CharField(
        source='focus.focus_title', 
        read_only=True,
        default=None
    )
    task_title = serializers.CharField(
        source='task.task_title', 
        read_only=True,
        default=None
    )
    keywords_list = serializers.SerializerMethodField()

    class Meta:
        model = WritingPrompt
        fields = [
            "id",
            "focus_id",
            "focus_title",
            "task_id",
            "task_title",
            "prompt_type",
            "prompt_type_display",
            "prompt_text",
            "expected_keywords",
            "keywords_list",
            "rubric",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_keywords_list(self, obj):
        """Parse expected keywords into a list"""
        if obj.expected_keywords:
            return [k.strip() for k in obj.expected_keywords.split(',') if k.strip()]
        return []

    def validate(self, data):
        """Ensure prompt is linked to either focus or task, not both"""
        focus = data.get('focus', getattr(self.instance, 'focus', None))
        task = data.get('task', getattr(self.instance, 'task', None))
        
        if bool(focus) == bool(task):
            raise serializers.ValidationError(
                "WritingPrompt must be linked to either a focus OR a task, not both."
            )
        
        return data


class WritingPromptListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for prompt listings"""
    prompt_type_display = serializers.CharField(
        source='get_prompt_type_display', 
        read_only=True
    )
    
    class Meta:
        model = WritingPrompt
        fields = [
            "id",
            "prompt_type",
            "prompt_type_display",
            "prompt_text",
        ]


# ============================================================
# PRACTICE ATTEMPT SERIALIZERS
# ============================================================

class WritingPracticeAttemptSerializer(serializers.ModelSerializer):
    focus_title = serializers.CharField(
        source='focus.focus_title', 
        read_only=True,
        default=None
    )
    prompt_text = serializers.CharField(
        source='prompt.prompt_text', 
        read_only=True
    )
    prompt_type = serializers.CharField(
        source='prompt.prompt_type', 
        read_only=True
    )

    class Meta:
        model = WritingPracticeAttempt
        fields = [
            "id",
            "user_id",
            "focus_id",
            "focus_title",
            "prompt_id",
            "prompt_text",
            "prompt_type",
            "attempt_number",
            "cycle_number",
            "response_text",
            "keyword_match_score",
            "is_passed",
            "time_spent_seconds",
            "hints_used",
            "created_at",
        ]
        read_only_fields = [
            "id", 
            "user_id", 
            "created_at", 
            "is_passed"
        ]


class WritingPracticeAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a practice attempt"""
    focus_id = serializers.IntegerField(required=False, allow_null=True)
    prompt_id = serializers.IntegerField()
    response_text = serializers.CharField()
    time_spent_seconds = serializers.IntegerField(min_value=0, required=False)
    hints_used = serializers.IntegerField(min_value=0, default=0)

    def validate(self, data):
        """Validate focus_id if provided"""
        if data.get('focus_id'):
            try:
                ChunkWritingFocus.objects.get(id=data['focus_id'])
            except ChunkWritingFocus.DoesNotExist:
                raise serializers.ValidationError({
                    "focus_id": "Invalid writing focus ID"
                })
        
        # Validate prompt exists
        try:
            prompt = WritingPrompt.objects.get(id=data['prompt_id'])
        except WritingPrompt.DoesNotExist:
            raise serializers.ValidationError({
                "prompt_id": "Invalid prompt ID"
            })
        
        # If focus_id provided, ensure prompt belongs to that focus
        if data.get('focus_id') and prompt.focus_id != data['focus_id']:
            raise serializers.ValidationError(
                "Prompt does not belong to the specified focus"
            )
        
        return data

    def validate_response_text(self, value):
        """Validate response is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Response text cannot be empty")
        return value.strip()


# ============================================================
# TEST ATTEMPT SERIALIZERS
# ============================================================

class WritingTestAttemptSerializer(serializers.ModelSerializer):
    focus_title = serializers.CharField(
        source='focus.focus_title', 
        read_only=True,
        default=None
    )
    task_title = serializers.CharField(
        source='task.task_title', 
        read_only=True,
        default=None
    )
    prompt_text = serializers.CharField(
        source='prompt.prompt_text', 
        read_only=True
    )
    prompt_type = serializers.CharField(
        source='prompt.prompt_type', 
        read_only=True
    )
    is_passed = serializers.BooleanField(source='is_mastered', read_only=True)
    context_type = serializers.SerializerMethodField()

    class Meta:
        model = WritingTestAttempt
        fields = [
            "id",
            "user_id",
            "focus_id",
            "focus_title",
            "task_id",
            "task_title",
            "prompt_id",
            "prompt_text",
            "prompt_type",
            "attempt_number",
            "cycle_number",
            "response_text",
            "rubric_scores",
            "overall_score",
            "is_mastered",
            "is_passed",
            "feedback",
            "time_spent_seconds",
            "context_type",
            "created_at",
        ]
        read_only_fields = [
            "id", 
            "user_id", 
            "created_at", 
            "is_mastered"
        ]

    def get_context_type(self, obj):
        """Return whether this is chunk-level or unit-level"""
        if obj.focus:
            return "chunk"
        elif obj.task:
            return "unit"
        return None


class WritingTestAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a test attempt"""
    focus_id = serializers.IntegerField(required=False, allow_null=True)
    task_id = serializers.IntegerField(required=False, allow_null=True)
    prompt_id = serializers.IntegerField()
    response_text = serializers.CharField()
    time_spent_seconds = serializers.IntegerField(min_value=0, required=False)

    def validate(self, data):
        """Validate that either focus_id or task_id is provided, but not both"""
        focus_id = data.get('focus_id')
        task_id = data.get('task_id')
        
        if bool(focus_id) == bool(task_id):
            raise serializers.ValidationError(
                "Must provide either focus_id OR task_id, not both"
            )
        
        # Validate focus if provided
        if focus_id:
            try:
                ChunkWritingFocus.objects.get(id=focus_id)
            except ChunkWritingFocus.DoesNotExist:
                raise serializers.ValidationError({
                    "focus_id": "Invalid writing focus ID"
                })
        
        # Validate task if provided
        if task_id:
            try:
                UnitWritingTask.objects.get(id=task_id)
            except UnitWritingTask.DoesNotExist:
                raise serializers.ValidationError({
                    "task_id": "Invalid writing task ID"
                })
        
        # Validate prompt exists
        try:
            prompt = WritingPrompt.objects.get(id=data['prompt_id'])
        except WritingPrompt.DoesNotExist:
            raise serializers.ValidationError({
                "prompt_id": "Invalid prompt ID"
            })
        
        # If focus_id provided, ensure prompt belongs to that focus
        if focus_id and prompt.focus_id != focus_id:
            raise serializers.ValidationError(
                "Prompt does not belong to the specified focus"
            )
        
        # If task_id provided, ensure prompt belongs to that task
        if task_id and prompt.task_id != task_id:
            raise serializers.ValidationError(
                "Prompt does not belong to the specified task"
            )
        
        return data

    def validate_response_text(self, value):
        """Validate response is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Response text cannot be empty")
        return value.strip()


# ============================================================
# PROGRESS & ANALYTICS SERIALIZERS
# ============================================================

class WritingProgressSummarySerializer(serializers.Serializer):
    """Summary of writing progress across all levels"""
    
    # Chunk-level progress
    chunk_focuses_total = serializers.IntegerField()
    chunk_focuses_mastered = serializers.IntegerField()
    chunk_focuses_in_progress = serializers.IntegerField()
    chunk_mastery_percentage = serializers.FloatField()
    
    # Unit-level progress
    unit_tasks_total = serializers.IntegerField()
    unit_tasks_mastered = serializers.IntegerField()
    unit_tasks_in_progress = serializers.IntegerField()
    unit_mastery_percentage = serializers.FloatField()
    
    # Practice stats
    total_practice_attempts = serializers.IntegerField()
    average_practice_score = serializers.FloatField()
    
    # Test stats
    total_test_attempts = serializers.IntegerField()
    average_test_score = serializers.FloatField()
    
    # By stage (paragraph, essay, etc.)
    by_stage = serializers.DictField(
        child=serializers.DictField()
    )
    
    # Recent activity
    recent_practice = WritingPracticeAttemptSerializer(many=True)
    recent_tests = WritingTestAttemptSerializer(many=True)


class WritingFocusProgressSerializer(serializers.Serializer):
    """Detailed progress for a specific writing focus"""
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
    
    # Performance by prompt
    prompt_performance = serializers.DictField(
        child=serializers.DictField()
    )
    
    # Next steps
    next_action = serializers.CharField()  # 'practice', 'test', 'review', 'mastered'
    next_action_details = serializers.DictField()


class WritingTaskProgressSerializer(serializers.Serializer):
    """Detailed progress for a unit-level writing task"""
    task_id = serializers.IntegerField()
    task_title = serializers.CharField()
    stage = serializers.CharField()
    difficulty_level = serializers.IntegerField()
    
    # Test tracking
    current_test_cycle = serializers.IntegerField()
    current_test_attempt = serializers.IntegerField()
    is_mastered = serializers.BooleanField()
    test_attempts_remaining = serializers.IntegerField()
    
    # Best performance
    best_score = serializers.IntegerField()
    best_score_date = serializers.DateTimeField()
    
    # Performance by rubric criterion
    rubric_performance = serializers.DictField(
        child=serializers.FloatField()
    )
    
    # Next steps
    next_action = serializers.CharField()
    improvement_areas = serializers.ListField(
        child=serializers.CharField()
    )


# ============================================================
# BULK OPERATION SERIALIZERS
# ============================================================

class WritingBulkPromptCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating writing prompts"""
    focus_id = serializers.IntegerField(required=False, allow_null=True)
    task_id = serializers.IntegerField(required=False, allow_null=True)
    prompts = serializers.ListField(
        child=serializers.DictField()
    )

    def validate(self, data):
        """Validate that either focus_id or task_id is provided"""
        focus_id = data.get('focus_id')
        task_id = data.get('task_id')
        
        if bool(focus_id) == bool(task_id):
            raise serializers.ValidationError(
                "Must provide either focus_id OR task_id"
            )
        
        # Validate focus if provided
        if focus_id:
            try:
                ChunkWritingFocus.objects.get(id=focus_id)
            except ChunkWritingFocus.DoesNotExist:
                raise serializers.ValidationError({
                    "focus_id": "Invalid writing focus ID"
                })
        
        # Validate task if provided
        if task_id:
            try:
                UnitWritingTask.objects.get(id=task_id)
            except UnitWritingTask.DoesNotExist:
                raise serializers.ValidationError({
                    "task_id": "Invalid writing task ID"
                })
        
        return data

    def validate_prompts(self, value):
        if not value:
            raise serializers.ValidationError("Prompts list cannot be empty")
        
        for idx, prompt_data in enumerate(value):
            if 'prompt_text' not in prompt_data:
                raise serializers.ValidationError(f"Prompt {idx} missing 'prompt_text'")
            if 'prompt_type' not in prompt_data:
                raise serializers.ValidationError(f"Prompt {idx} missing 'prompt_type'")
            
            # Validate prompt_type
            valid_types = [pt[0] for pt in WritingPrompt.PROMPT_TYPE_CHOICES]
            if prompt_data['prompt_type'] not in valid_types:
                raise serializers.ValidationError(
                    f"Prompt {idx}: Invalid prompt_type. Must be one of {valid_types}"
                )
        
        return value


# ============================================================
# MOBILE-OPTIMIZED SERIALIZERS
# ============================================================

class WritingPromptMobileSerializer(serializers.ModelSerializer):
    """Lightweight serializer for mobile devices"""
    prompt_type_display = serializers.CharField(
        source='get_prompt_type_display', 
        read_only=True
    )
    
    class Meta:
        model = WritingPrompt
        fields = [
            "id",
            "prompt_type",
            "prompt_type_display",
            "prompt_text",
        ]


class WritingPracticeAttemptMobileSerializer(serializers.ModelSerializer):
    """Mobile-optimized practice attempt serializer"""
    
    class Meta:
        model = WritingPracticeAttempt
        fields = [
            "id",
            "prompt_id",
            "attempt_number",
            "is_passed",
            "keyword_match_score",
            "created_at",
        ]


class WritingTestAttemptMobileSerializer(serializers.ModelSerializer):
    """Mobile-optimized test attempt serializer"""
    context_type = serializers.SerializerMethodField()
    
    class Meta:
        model = WritingTestAttempt
        fields = [
            "id",
            "prompt_id",
            "attempt_number",
            "overall_score",
            "is_mastered",
            "context_type",
            "created_at",
        ]
    
    def get_context_type(self, obj):
        if obj.focus:
            return "chunk"
        elif obj.task:
            return "unit"
        return None