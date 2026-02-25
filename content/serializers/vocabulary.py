# serializers/vocabulary.py

from rest_framework import serializers
from content.models.vocabulary import (
    VocabularyItem,
    VocabularyAttempt,
    StudentVocabMastery
)
from content.models.core import Lesson, LessonChunk
from django.db import models
from django.utils import timezone


# ============================================================
# VOCABULARY ITEM SERIALIZERS
# ============================================================

class VocabularyItemSerializer(serializers.ModelSerializer):
    part_of_speech_display = serializers.CharField(
        source='get_part_of_speech_display', 
        read_only=True
    )
    lesson_title = serializers.CharField(
        source='lesson.title', 
        read_only=True,
        default=None
    )
    chunk_order = serializers.IntegerField(
        source='chunk.order', 
        read_only=True,
        default=None
    )
    mastery_stats = serializers.SerializerMethodField()

    class Meta:
        model = VocabularyItem
        fields = [
            "id",
            "lesson_id",
            "lesson_title",
            "chunk_id",
            "chunk_order",
            "word",
            "urdu",
            "meaning",
            "synonyms",
            "antonyms",
            "example_sentence",
            "part_of_speech",
            "part_of_speech_display",
            "mastery_stats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_mastery_stats(self, obj):
        """Get mastery statistics for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                mastery = StudentVocabMastery.objects.get(
                    user=request.user,
                    vocab_item=obj
                )
                return {
                    'mastery_level': mastery.mastery_level,
                    'mastery_level_display': mastery.get_mastery_level_display(),
                    'accuracy_percentage': mastery.accuracy_percentage,
                    'total_attempts': mastery.total_attempts,
                    'correct_attempts': mastery.correct_attempts,
                    'last_practiced': mastery.last_practiced,
                }
            except StudentVocabMastery.DoesNotExist:
                return {
                    'mastery_level': 'new',
                    'mastery_level_display': 'New',
                    'accuracy_percentage': 0,
                    'total_attempts': 0,
                    'correct_attempts': 0,
                    'last_practiced': None,
                }
        return None


class VocabularyItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for vocabulary listings"""
    part_of_speech_display = serializers.CharField(
        source='get_part_of_speech_display', 
        read_only=True
    )
    
    class Meta:
        model = VocabularyItem
        fields = [
            "id",
            "word",
            "urdu",
            "part_of_speech",
            "part_of_speech_display",
            "lesson_id",
        ]


class VocabularyItemDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with related data"""
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    chunk_order = serializers.IntegerField(source='chunk.order', read_only=True)
    recent_attempts = serializers.SerializerMethodField()
    
    class Meta:
        model = VocabularyItem
        fields = [
            "id",
            "lesson_id",
            "lesson_title",
            "chunk_id",
            "chunk_order",
            "word",
            "urdu",
            "meaning",
            "synonyms",
            "antonyms",
            "example_sentence",
            "part_of_speech",
            "part_of_speech_display",
            "recent_attempts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_recent_attempts(self, obj):
        """Get recent attempt history for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = obj.attempts.filter(user=request.user).order_by('-created_at')[:5]
            return VocabularyAttemptSerializer(attempts, many=True).data
        return []


# ============================================================
# VOCABULARY ATTEMPT SERIALIZERS
# ============================================================

class VocabularyAttemptSerializer(serializers.ModelSerializer):
    word = serializers.CharField(source='vocab_item.word', read_only=True)
    is_correct_display = serializers.CharField(
        source='get_is_correct_display', 
        read_only=True
    )

    class Meta:
        model = VocabularyAttempt
        fields = [
            "id",
            "user_id",
            "vocab_item_id",
            "word",
            "session_id",
            "cycle_number",
            "is_correct",
            "is_correct_display",
            "time_taken_seconds",
            "created_at",
        ]
        read_only_fields = ["id", "user_id", "created_at"]


class VocabularyAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting vocabulary practice attempts"""
    vocab_item_id = serializers.IntegerField()
    session_id = serializers.CharField(max_length=100)
    is_correct = serializers.BooleanField()
    time_taken_seconds = serializers.IntegerField(min_value=0, required=False)
    cycle_number = serializers.IntegerField(min_value=1, default=1)

    def validate_vocab_item_id(self, value):
        try:
            VocabularyItem.objects.get(id=value)
        except VocabularyItem.DoesNotExist:
            raise serializers.ValidationError("Invalid vocabulary item ID")
        return value

    def validate_session_id(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Session ID cannot be empty")
        return value.strip()


class VocabularyBatchAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting multiple vocabulary attempts at once"""
    session_id = serializers.CharField(max_length=100)
    attempts = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_session_id(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Session ID cannot be empty")
        return value.strip()
    
    def validate_attempts(self, value):
        if not value:
            raise serializers.ValidationError("Attempts list cannot be empty")
        
        for idx, attempt in enumerate(value):
            if 'vocab_item_id' not in attempt:
                raise serializers.ValidationError(f"Attempt {idx} missing vocab_item_id")
            if 'is_correct' not in attempt:
                raise serializers.ValidationError(f"Attempt {idx} missing is_correct")
            
            # Validate vocab_item exists
            try:
                VocabularyItem.objects.get(id=attempt['vocab_item_id'])
            except VocabularyItem.DoesNotExist:
                raise serializers.ValidationError(
                    f"Attempt {idx}: Invalid vocabulary item ID {attempt['vocab_item_id']}"
                )
        
        return value


# ============================================================
# MASTERY SERIALIZERS
# ============================================================

class StudentVocabMasterySerializer(serializers.ModelSerializer):
    word = serializers.CharField(source='vocab_item.word', read_only=True)
    urdu = serializers.CharField(source='vocab_item.urdu', read_only=True)
    part_of_speech = serializers.CharField(
        source='vocab_item.part_of_speech', 
        read_only=True
    )
    part_of_speech_display = serializers.CharField(
        source='vocab_item.get_part_of_speech_display', 
        read_only=True
    )
    mastery_level_display = serializers.CharField(
        source='get_mastery_level_display', 
        read_only=True
    )
    needs_review = serializers.SerializerMethodField()
    next_review_date = serializers.SerializerMethodField()

    class Meta:
        model = StudentVocabMastery
        fields = [
            "id",
            "user_id",
            "vocab_item_id",
            "word",
            "urdu",
            "part_of_speech",
            "part_of_speech_display",
            "mastery_level",
            "mastery_level_display",
            "last_practiced",
            "total_attempts",
            "correct_attempts",
            "accuracy_percentage",
            "needs_review",
            "next_review_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", 
            "user_id", 
            "created_at", 
            "updated_at",
            "accuracy_percentage"
        ]

    def get_needs_review(self, obj):
        """Determine if item needs review based on spaced repetition"""
        if not obj.last_practiced:
            return True
        
        days_since = (timezone.now() - obj.last_practiced).days
        
        # Review schedule based on mastery level
        if obj.mastery_level == 'mastered':
            return days_since >= 30
        elif obj.mastery_level == 'review':
            return days_since >= 1
        elif obj.mastery_level == 'learning':
            return days_since >= 3
        else:  # new
            return True

    def get_next_review_date(self, obj):
        """Calculate next review date based on spaced repetition"""
        if not obj.last_practiced:
            return timezone.now().isoformat()
        
        days_since = (timezone.now() - obj.last_practiced).days
        
        if obj.mastery_level == 'mastered':
            # Mastered: review after 30 days
            review_date = obj.last_practiced + timezone.timedelta(days=30)
        elif obj.mastery_level == 'review':
            # Needs review: review next day
            review_date = obj.last_practiced + timezone.timedelta(days=1)
        elif obj.mastery_level == 'learning':
            # Learning: review after 3 days
            review_date = obj.last_practiced + timezone.timedelta(days=3)
        else:  # new
            # New: review immediately
            return timezone.now().isoformat()
        
        return review_date.isoformat()


class StudentVocabMasteryUpdateSerializer(serializers.Serializer):
    """Serializer for manually updating mastery level"""
    vocab_item_id = serializers.IntegerField()
    mastery_level = serializers.ChoiceField(
        choices=[level[0] for level in StudentVocabMastery.MASTERY_LEVELS]
    )
    
    def validate_vocab_item_id(self, value):
        try:
            VocabularyItem.objects.get(id=value)
        except VocabularyItem.DoesNotExist:
            raise serializers.ValidationError("Invalid vocabulary item ID")
        return value


# ============================================================
# PROGRESS & ANALYTICS SERIALIZERS
# ============================================================

class VocabularyProgressSummarySerializer(serializers.Serializer):
    """Summary of vocabulary progress for a user"""
    total_items = serializers.IntegerField()
    
    # Mastery distribution
    mastered_count = serializers.IntegerField()
    learning_count = serializers.IntegerField()
    review_count = serializers.IntegerField()
    new_count = serializers.IntegerField()
    
    # Percentages
    mastery_percentage = serializers.FloatField()
    
    # Performance
    total_attempts = serializers.IntegerField()
    overall_accuracy = serializers.FloatField()
    
    # Recent activity
    recently_mastered = StudentVocabMasterySerializer(many=True)
    needs_review = StudentVocabMasterySerializer(many=True)
    
    # By part of speech
    by_part_of_speech = serializers.DictField(
        child=serializers.DictField()
    )


class VocabularyItemProgressSerializer(serializers.Serializer):
    """Detailed progress for a specific vocabulary item"""
    vocab_item_id = serializers.IntegerField()
    word = serializers.CharField()
    urdu = serializers.CharField()
    part_of_speech = serializers.CharField()
    
    # Mastery info
    mastery_level = serializers.CharField()
    accuracy = serializers.FloatField()
    
    # Attempt history
    total_attempts = serializers.IntegerField()
    attempts_last_week = serializers.IntegerField()
    attempts_last_month = serializers.IntegerField()
    
    # Timeline
    first_attempted = serializers.DateTimeField(allow_null=True)
    last_attempted = serializers.DateTimeField(allow_null=True)
    
    # Next steps
    needs_review = serializers.BooleanField()
    suggested_action = serializers.CharField()  # 'practice', 'review', 'mastered'


class VocabularySessionSummarySerializer(serializers.Serializer):
    """Summary of a practice session"""
    session_id = serializers.CharField()
    total_attempts = serializers.IntegerField()
    correct_attempts = serializers.IntegerField()
    accuracy = serializers.FloatField()
    time_spent_seconds = serializers.IntegerField()
    
    # Items practiced
    items_practiced = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Mastery changes
    newly_mastered = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Recommendations
    next_items_to_practice = serializers.ListField(
        child=serializers.DictField()
    )


# ============================================================
# BULK OPERATION SERIALIZERS
# ============================================================

class VocabularyBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating vocabulary items"""
    lesson_id = serializers.IntegerField()
    items = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_lesson_id(self, value):
        try:
            Lesson.objects.get(id=value)
        except Lesson.DoesNotExist:
            raise serializers.ValidationError("Invalid lesson ID")
        return value

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Items list cannot be empty")
        
        for idx, item_data in enumerate(value):
            if 'word' not in item_data:
                raise serializers.ValidationError(f"Item {idx} missing 'word' field")
            
            # Validate part_of_speech if provided
            if 'part_of_speech' in item_data:
                valid_pos = [pos[0] for pos in VocabularyItem.PARTS_OF_SPEECH]
                if item_data['part_of_speech'] not in valid_pos:
                    raise serializers.ValidationError(
                        f"Item {idx}: Invalid part_of_speech. Must be one of {valid_pos}"
                    )
        
        return value


class VocabularyBulkMasteryUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating mastery levels"""
    updates = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_updates(self, value):
        if not value:
            raise serializers.ValidationError("Updates list cannot be empty")
        
        valid_levels = [level[0] for level in StudentVocabMastery.MASTERY_LEVELS]
        
        for idx, update in enumerate(value):
            if 'vocab_item_id' not in update:
                raise serializers.ValidationError(f"Update {idx} missing vocab_item_id")
            if 'mastery_level' not in update:
                raise serializers.ValidationError(f"Update {idx} missing mastery_level")
            
            # Validate mastery level
            if update['mastery_level'] not in valid_levels:
                raise serializers.ValidationError(
                    f"Update {idx}: Invalid mastery_level. Must be one of {valid_levels}"
                )
            
            # Validate vocab_item exists
            try:
                VocabularyItem.objects.get(id=update['vocab_item_id'])
            except VocabularyItem.DoesNotExist:
                raise serializers.ValidationError(
                    f"Update {idx}: Invalid vocabulary item ID {update['vocab_item_id']}"
                )
        
        return value


# ============================================================
# MOBILE-OPTIMIZED SERIALIZERS
# ============================================================

class VocabularyItemMobileSerializer(serializers.ModelSerializer):
    """Lightweight serializer for mobile devices"""
    part_of_speech_display = serializers.CharField(
        source='get_part_of_speech_display', 
        read_only=True
    )
    
    class Meta:
        model = VocabularyItem
        fields = [
            "id",
            "word",
            "urdu",
            "part_of_speech",
            "part_of_speech_display",
        ]


class StudentVocabMasteryMobileSerializer(serializers.ModelSerializer):
    """Lightweight mastery serializer for mobile"""
    word = serializers.CharField(source='vocab_item.word', read_only=True)
    urdu = serializers.CharField(source='vocab_item.urdu', read_only=True)
    mastery_level_display = serializers.CharField(
        source='get_mastery_level_display', 
        read_only=True
    )
    
    class Meta:
        model = StudentVocabMastery
        fields = [
            "vocab_item_id",
            "word",
            "urdu",
            "mastery_level",
            "mastery_level_display",
            "accuracy_percentage",
            "needs_review",
        ]