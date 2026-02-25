# serializers/pronunciation.py

from rest_framework import serializers
from content.models.pronunciation import (
    PronunciationFocus,
    PronunciationAttempt,
    PronunciationMastery
)
from django.utils import timezone
import datetime


# ============================================================
# TEACHING LAYER SERIALIZERS
# ============================================================

class PronunciationFocusSerializer(serializers.ModelSerializer):
    attempt_stats = serializers.SerializerMethodField()
    mastery_status = serializers.SerializerMethodField()
    chunk_title = serializers.CharField(source='chunk.lesson.title', read_only=True, default="")

    class Meta:
        model = PronunciationFocus
        fields = [
            "id",
            "chunk_id",
            "focus_title",
            "focus_description",
            "sequence_order",
            "chunk_title",
            "attempt_stats",
            "mastery_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_sequence_order(self, value):
        """Validate sequence order is between 1 and 3"""
        if value < 1 or value > 3:
            raise serializers.ValidationError("Sequence order must be between 1 and 3")
        return value

    def get_attempt_stats(self, obj):
        """Get attempt statistics for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = PronunciationAttempt.objects.filter(
                user=request.user,
                focus=obj
            )
            latest = attempts.order_by('-created_at').first()
            
            # Separate practice and test attempts
            practice_attempts = attempts.filter(attempt_type='practice')
            test_attempts = attempts.filter(attempt_type='test')
            
            return {
                'total_attempts': attempts.count(),
                'practice_attempts': practice_attempts.count(),
                'test_attempts': test_attempts.count(),
                'latest_score': latest.ai_score if latest else None,
                'latest_attempt_number': latest.attempt_number if latest else None,
                'current_cycle': latest.cycle_number if latest else 1,
                'passed_attempts': attempts.filter(ai_score__gte=90).count(),
            }
        return None

    def get_mastery_status(self, obj):
        """Get mastery status for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                mastery = PronunciationMastery.objects.get(
                    user=request.user,
                    focus=obj
                )
                return {
                    'is_mastered': mastery.is_mastered,
                    'best_score': mastery.best_score,
                    'last_score': mastery.last_score,
                    'total_attempts': mastery.total_attempts,
                    'last_attempted': mastery.last_attempted,
                    'mastered_at': mastery.mastered_at,
                }
            except PronunciationMastery.DoesNotExist:
                return {
                    'is_mastered': False,
                    'best_score': None,
                    'last_score': None,
                    'total_attempts': 0,
                    'last_attempted': None,
                    'mastered_at': None,
                }
        return None


class PronunciationFocusListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for pronunciation focus listings"""
    is_mastered = serializers.SerializerMethodField()
    
    class Meta:
        model = PronunciationFocus
        fields = [
            "id",
            "focus_title",
            "sequence_order",
            "is_mastered",
        ]

    def get_is_mastered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                mastery = PronunciationMastery.objects.get(
                    user=request.user,
                    focus=obj
                )
                return mastery.is_mastered
            except PronunciationMastery.DoesNotExist:
                return False
        return False


# ============================================================
# ATTEMPT SERIALIZERS
# ============================================================

class PronunciationAttemptSerializer(serializers.ModelSerializer):
    focus_details = serializers.SerializerMethodField()
    is_passed = serializers.BooleanField(read_only=True)
    recording_url = serializers.SerializerMethodField()

    class Meta:
        model = PronunciationAttempt
        fields = [
            "id",
            "user_id",
            "focus_id",
            "focus_details",
            "chunk_id",
            "attempt_number",
            "cycle_number",
            "recording",
            "recording_url",
            "ai_feedback",
            "ai_score",
            "is_passed",
            "attempt_type",
            "created_at",
        ]
        read_only_fields = [
            "id", 
            "user_id", 
            "created_at", 
            "ai_feedback", 
            "ai_score", 
            "is_passed"
        ]

    def get_focus_details(self, obj):
        """Get focus details if focus exists"""
        if obj.focus:
            return {
                'id': obj.focus.id,
                'focus_title': obj.focus.focus_title,
                'sequence_order': obj.focus.sequence_order,
            }
        return None

    def get_recording_url(self, obj):
        """Get full URL for recording file"""
        if obj.recording and hasattr(obj.recording, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.recording.url)
        return None


class PronunciationAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a pronunciation attempt"""
    focus_id = serializers.IntegerField(required=False, allow_null=True)
    chunk_id = serializers.IntegerField(required=False, allow_null=True)
    recording = serializers.FileField()
    attempt_type = serializers.ChoiceField(
        choices=[('practice', 'Practice'), ('test', 'Test')],
        default='practice'
    )

    def validate(self, data):
        """Validate that either focus_id or chunk_id is provided"""
        if not data.get('focus_id') and not data.get('chunk_id'):
            raise serializers.ValidationError(
                "Either focus_id or chunk_id must be provided"
            )
        
        # Validate focus_id if provided
        if data.get('focus_id'):
            try:
                PronunciationFocus.objects.get(id=data['focus_id'])
            except PronunciationFocus.DoesNotExist:
                raise serializers.ValidationError({
                    "focus_id": "Invalid pronunciation focus ID"
                })
        
        return data

    def validate_recording(self, value):
        """Validate audio file"""
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("Audio file too large (max 10MB)")
        
        # Check file extension
        ext = value.name.split('.')[-1].lower()
        if ext not in ['mp3', 'wav', 'm4a', 'ogg', 'webm']:
            raise serializers.ValidationError(
                "Unsupported audio format. Use mp3, wav, m4a, ogg, or webm"
            )
        
        return value


# ============================================================
# MOBILE-OPTIMIZED SERIALIZERS (ADD THIS SECTION)
# ============================================================

class PronunciationAttemptMobileSerializer(serializers.ModelSerializer):
    """Mobile-optimized pronunciation attempt serializer"""
    is_passed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PronunciationAttempt
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
        read_only_fields = ["id", "created_at", "is_passed"]


class PronunciationMasteryMobileSerializer(serializers.ModelSerializer):
    """Mobile-optimized pronunciation mastery serializer"""
    
    class Meta:
        model = PronunciationMastery
        fields = [
            "focus_id",
            "is_mastered",
            "best_score",
            "last_score",
            "total_attempts",
        ]


# ============================================================
# MASTERY SERIALIZERS
# ============================================================

class PronunciationMasterySerializer(serializers.ModelSerializer):
    focus_details = serializers.SerializerMethodField()
    mastery_level = serializers.SerializerMethodField()
    next_review = serializers.SerializerMethodField()

    class Meta:
        model = PronunciationMastery
        fields = [
            "id",
            "user_id",
            "focus_id",
            "focus_details",
            "total_attempts",
            "best_score",
            "last_score",
            "is_mastered",
            "mastery_level",
            "last_attempted",
            "mastered_at",
            "next_review",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", 
            "user_id", 
            "created_at", 
            "updated_at",
            "is_mastered"
        ]

    def get_focus_details(self, obj):
        """Get focus details"""
        if obj.focus:
            return {
                'id': obj.focus.id,
                'focus_title': obj.focus.focus_title,
                'sequence_order': obj.focus.sequence_order,
            }
        return None

    def get_mastery_level(self, obj):
        """Determine mastery level based on score"""
        if obj.is_mastered:
            return "mastered"
        elif obj.best_score and obj.best_score >= 75:
            return "advanced"
        elif obj.best_score and obj.best_score >= 50:
            return "intermediate"
        elif obj.best_score:
            return "beginner"
        return "not_started"

    def get_next_review(self, obj):
        """Calculate next review date based on spaced repetition"""
        if not obj.last_attempted:
            return None
        
        # Simple spaced repetition: review after 1 day, then 3 days, then 7 days
        if obj.is_mastered:
            # Mastered items: review after 30 days
            review_date = obj.last_attempted + datetime.timedelta(days=30)
        elif obj.total_attempts == 1:
            review_date = obj.last_attempted + datetime.timedelta(days=1)
        elif obj.total_attempts == 2:
            review_date = obj.last_attempted + datetime.timedelta(days=3)
        elif obj.total_attempts >= 3:
            review_date = obj.last_attempted + datetime.timedelta(days=7)
        else:
            return None
        
        return review_date.isoformat()


class PronunciationMasteryUpdateSerializer(serializers.Serializer):
    """Serializer for manually updating mastery status"""
    focus_id = serializers.IntegerField()
    is_mastered = serializers.BooleanField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_focus_id(self, value):
        try:
            PronunciationFocus.objects.get(id=value)
        except PronunciationFocus.DoesNotExist:
            raise serializers.ValidationError("Invalid pronunciation focus ID")
        return value


# ============================================================
# PROGRESS & ANALYTICS SERIALIZERS
# ============================================================

class PronunciationProgressSummarySerializer(serializers.Serializer):
    """Summary of pronunciation progress across all focuses"""
    total_focuses = serializers.IntegerField()
    mastered_focuses = serializers.IntegerField()
    in_progress_focuses = serializers.IntegerField()
    not_started_focuses = serializers.IntegerField()
    
    # Score statistics
    average_best_score = serializers.FloatField()
    average_last_score = serializers.FloatField()
    
    # Attempt statistics
    total_attempts = serializers.IntegerField()
    practice_attempts = serializers.IntegerField()
    test_attempts = serializers.IntegerField()
    
    # Mastery percentage
    mastery_percentage = serializers.FloatField()
    
    # Recently mastered
    recently_mastered = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )


class PronunciationFocusProgressSerializer(serializers.Serializer):
    """Detailed progress for a specific pronunciation focus"""
    focus_id = serializers.IntegerField()
    focus_title = serializers.CharField()
    sequence_order = serializers.IntegerField()
    
    # Current cycle tracking
    current_cycle = serializers.IntegerField()
    current_attempt = serializers.IntegerField()
    attempts_remaining = serializers.IntegerField()
    
    # Performance
    best_score = serializers.IntegerField(allow_null=True)
    last_score = serializers.IntegerField(allow_null=True)
    average_score = serializers.FloatField()
    
    # Status
    is_mastered = serializers.BooleanField()
    mastery_threshold_reached = serializers.BooleanField()
    
    # Timeline
    last_attempted = serializers.DateTimeField(allow_null=True)
    first_attempted = serializers.DateTimeField(allow_null=True)
    
    # Next steps
    next_action = serializers.CharField()  # 'practice', 'test', 'review', 'mastered'
    suggested_focus = serializers.CharField(allow_null=True)


# ============================================================
# BATCH OPERATION SERIALIZERS
# ============================================================

class PronunciationBulkFocusCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating pronunciation focuses"""
    chunk_id = serializers.IntegerField()
    focuses = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_chunk_id(self, value):
        from content.models.core import LessonChunk
        try:
            LessonChunk.objects.get(id=value)
        except LessonChunk.DoesNotExist:
            raise serializers.ValidationError("Invalid chunk ID")
        return value

    def validate_focuses(self, value):
        if not value:
            raise serializers.ValidationError("Focuses list cannot be empty")
        
        # Validate sequence orders are unique within the list
        sequence_orders = []
        for idx, focus_data in enumerate(value):
            if 'focus_title' not in focus_data:
                raise serializers.ValidationError(f"Focus {idx} missing focus_title")
            
            if 'sequence_order' not in focus_data:
                raise serializers.ValidationError(f"Focus {idx} missing sequence_order")
            
            if 'focus_description' not in focus_data:
                focus_data['focus_description'] = ''  # Provide default
            
            seq = focus_data['sequence_order']
            if seq < 1 or seq > 3:
                raise serializers.ValidationError(
                    f"Focus {idx} sequence_order must be between 1 and 3"
                )
            
            if seq in sequence_orders:
                raise serializers.ValidationError(
                    f"Duplicate sequence_order {seq} in focuses list"
                )
            
            sequence_orders.append(seq)
        
        return value


# ============================================================
# AUDIO PROCESSING SERIALIZERS
# ============================================================

class PronunciationAudioAnalysisSerializer(serializers.Serializer):
    """Serializer for audio analysis results"""
    focus_id = serializers.IntegerField()
    recording_url = serializers.URLField()
    analysis_results = serializers.DictField(
        child=serializers.DictField()
    )


class PronunciationFeedbackSerializer(serializers.Serializer):
    """Serializer for AI-generated feedback"""
    focus_id = serializers.IntegerField()
    focus_title = serializers.CharField()
    score = serializers.IntegerField(min_value=0, max_value=100)
    feedback = serializers.CharField()
    strengths = serializers.ListField(child=serializers.CharField())
    areas_for_improvement = serializers.ListField(child=serializers.CharField())
    phoneme_analysis = serializers.DictField(
        child=serializers.DictField(),
        required=False
    )


# ============================================================
# EXPORTS (Optional - add at the end of the file)
# ============================================================

__all__ = [
    'PronunciationFocusSerializer',
    'PronunciationFocusListSerializer',
    'PronunciationAttemptSerializer',
    'PronunciationAttemptSubmitSerializer',
    'PronunciationAttemptMobileSerializer',
    'PronunciationMasterySerializer',
    'PronunciationMasteryUpdateSerializer',
    'PronunciationMasteryMobileSerializer',
    'PronunciationProgressSummarySerializer',
    'PronunciationFocusProgressSerializer',
    'PronunciationBulkFocusCreateSerializer',
    'PronunciationAudioAnalysisSerializer',
    'PronunciationFeedbackSerializer',
]