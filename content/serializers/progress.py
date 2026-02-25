# serializers/progress.py

from rest_framework import serializers
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from content.models.core import Textbook, Unit, Lesson, LessonChunk
from content.models.grammar import (
    GrammarPracticeAttempt, GrammarTestAttempt, 
    GrammarQuestionAttempt, ChunkGrammarFocus
)
from content.models.punctuation import (
    PunctuationPracticeAttempt, PunctuationTestAttempt,
    ChunkPunctuationFocus
)
from content.models.vocabulary import (
    VocabularyAttempt, StudentVocabMastery, VocabularyItem
)
from content.models.comprehension import (
    ComprehensionPracticeAttempt, ComprehensionTestAttempt,
    ComprehensionQuestionAttempt, ChunkComprehensionFocus
)
from content.models.writing import (
    WritingPracticeAttempt, WritingTestAttempt,
    ChunkWritingFocus, UnitWritingTask
)
from content.models.pronunciation import (
    PronunciationAttempt, PronunciationMastery, PronunciationFocus
)
from content.models.testing import (
    UnitTestSession, UnitTestAnswer
)

User = get_user_model()


# ============================================================
# DOMAIN-SPECIFIC PROGRESS SERIALIZERS
# ============================================================

class GrammarProgressSerializer(serializers.Serializer):
    """Grammar domain progress summary"""
    
    # Overall stats
    total_focuses = serializers.SerializerMethodField()
    mastered_focuses = serializers.SerializerMethodField()
    in_progress_focuses = serializers.SerializerMethodField()
    not_started_focuses = serializers.SerializerMethodField()
    mastery_percentage = serializers.SerializerMethodField()
    
    # Practice stats
    total_practice_attempts = serializers.SerializerMethodField()
    average_practice_score = serializers.SerializerMethodField()
    
    # Test stats
    total_test_attempts = serializers.SerializerMethodField()
    average_test_score = serializers.SerializerMethodField()
    
    # Time spent (minutes)
    total_time_spent = serializers.SerializerMethodField()
    
    # Recent activity
    last_activity = serializers.SerializerMethodField()
    needs_review_count = serializers.SerializerMethodField()
    
    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def get_total_focuses(self, obj):
        """Total number of grammar focuses in the curriculum"""
        return ChunkGrammarFocus.objects.count()

    def get_mastered_focuses(self, obj):
        """Number of grammar focuses mastered by user"""
        if not self.user:
            return 0
        return GrammarTestAttempt.objects.filter(
            user=self.user,
            is_mastered=True
        ).values('focus').distinct().count()

    def get_in_progress_focuses(self, obj):
        """Number of grammar focuses started but not mastered"""
        if not self.user:
            return 0
        # Focuses with at least one attempt but not mastered
        attempted = GrammarTestAttempt.objects.filter(
            user=self.user
        ).values_list('focus_id', flat=True).distinct()
        
        mastered = GrammarTestAttempt.objects.filter(
            user=self.user,
            is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        
        return len(set(attempted) - set(mastered))

    def get_not_started_focuses(self, obj):
        """Number of grammar focuses never attempted"""
        total = self.get_total_focuses(obj)
        mastered = self.get_mastered_focuses(obj)
        in_progress = self.get_in_progress_focuses(obj)
        return total - (mastered + in_progress)

    def get_mastery_percentage(self, obj):
        """Percentage of focuses mastered"""
        total = self.get_total_focuses(obj)
        if total == 0:
            return 0
        mastered = self.get_mastered_focuses(obj)
        return (mastered / total) * 100

    def get_total_practice_attempts(self, obj):
        """Total number of practice attempts"""
        if not self.user:
            return 0
        return GrammarPracticeAttempt.objects.filter(user=self.user).count()

    def get_average_practice_score(self, obj):
        """Average score across all practice attempts"""
        if not self.user:
            return 0
        attempts = GrammarPracticeAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        return attempts.aggregate(avg=models.Avg('score_percent'))['avg'] or 0

    def get_total_test_attempts(self, obj):
        """Total number of test attempts"""
        if not self.user:
            return 0
        return GrammarTestAttempt.objects.filter(user=self.user).count()

    def get_average_test_score(self, obj):
        """Average score across all test attempts"""
        if not self.user:
            return 0
        attempts = GrammarTestAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        return attempts.aggregate(avg=models.Avg('score_percent'))['avg'] or 0

    def get_total_time_spent(self, obj):
        """Total minutes spent on grammar"""
        if not self.user:
            return 0
        
        total_seconds = 0
        
        practice_time = GrammarPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += practice_time
        
        test_time = GrammarTestAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += test_time
        
        return total_seconds // 60

    def get_last_activity(self, obj):
        """Most recent grammar activity timestamp"""
        if not self.user:
            return None
        
        last_practice = GrammarPracticeAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        
        last_test = GrammarTestAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        
        if not last_practice and not last_test:
            return None
        
        if last_practice and last_test:
            return max(last_practice, last_test)
        return last_practice or last_test

    def get_needs_review_count(self, obj):
        """Number of focuses that need review (failed tests)"""
        if not self.user:
            return 0
        
        recent_failures = GrammarTestAttempt.objects.filter(
            user=self.user,
            is_mastered=False,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).values_list('focus_id', flat=True).distinct()
        
        return len(recent_failures)


class PunctuationProgressSerializer(serializers.Serializer):
    """Punctuation domain progress summary"""
    
    total_focuses = serializers.SerializerMethodField()
    mastered_focuses = serializers.SerializerMethodField()
    in_progress_focuses = serializers.SerializerMethodField()
    not_started_focuses = serializers.SerializerMethodField()
    mastery_percentage = serializers.SerializerMethodField()
    total_practice_attempts = serializers.SerializerMethodField()
    average_practice_score = serializers.SerializerMethodField()
    total_test_attempts = serializers.SerializerMethodField()
    average_test_score = serializers.SerializerMethodField()
    total_time_spent = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    needs_review_count = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def get_total_focuses(self, obj):
        return ChunkPunctuationFocus.objects.count()

    def get_mastered_focuses(self, obj):
        if not self.user:
            return 0
        return PunctuationTestAttempt.objects.filter(
            user=self.user,
            is_mastered=True
        ).values('focus').distinct().count()

    def get_in_progress_focuses(self, obj):
        if not self.user:
            return 0
        attempted = PunctuationTestAttempt.objects.filter(
            user=self.user
        ).values_list('focus_id', flat=True).distinct()
        mastered = PunctuationTestAttempt.objects.filter(
            user=self.user,
            is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        return len(set(attempted) - set(mastered))

    def get_not_started_focuses(self, obj):
        total = self.get_total_focuses(obj)
        mastered = self.get_mastered_focuses(obj)
        in_progress = self.get_in_progress_focuses(obj)
        return total - (mastered + in_progress)

    def get_mastery_percentage(self, obj):
        total = self.get_total_focuses(obj)
        if total == 0:
            return 0
        mastered = self.get_mastered_focuses(obj)
        return (mastered / total) * 100

    def get_total_practice_attempts(self, obj):
        if not self.user:
            return 0
        return PunctuationPracticeAttempt.objects.filter(user=self.user).count()

    def get_average_practice_score(self, obj):
        if not self.user:
            return 0
        attempts = PunctuationPracticeAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        return attempts.aggregate(avg=models.Avg('score_percent'))['avg'] or 0

    def get_total_test_attempts(self, obj):
        if not self.user:
            return 0
        return PunctuationTestAttempt.objects.filter(user=self.user).count()

    def get_average_test_score(self, obj):
        if not self.user:
            return 0
        attempts = PunctuationTestAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        return attempts.aggregate(avg=models.Avg('score_percent'))['avg'] or 0

    def get_total_time_spent(self, obj):
        if not self.user:
            return 0
        total_seconds = 0
        practice_time = PunctuationPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += practice_time
        test_time = PunctuationTestAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += test_time
        return total_seconds // 60

    def get_last_activity(self, obj):
        if not self.user:
            return None
        last_practice = PunctuationPracticeAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        last_test = PunctuationTestAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if not last_practice and not last_test:
            return None
        if last_practice and last_test:
            return max(last_practice, last_test)
        return last_practice or last_test

    def get_needs_review_count(self, obj):
        if not self.user:
            return 0
        recent_failures = PunctuationTestAttempt.objects.filter(
            user=self.user,
            is_mastered=False,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).values_list('focus_id', flat=True).distinct()
        return len(recent_failures)


class VocabularyProgressSerializer(serializers.Serializer):
    """Vocabulary domain progress summary"""
    
    total_items = serializers.SerializerMethodField()
    
    # Mastery distribution
    mastered_count = serializers.SerializerMethodField()
    learning_count = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    new_count = serializers.SerializerMethodField()
    
    # Percentages
    mastery_percentage = serializers.SerializerMethodField()
    
    # Performance
    total_attempts = serializers.SerializerMethodField()
    overall_accuracy = serializers.SerializerMethodField()
    
    # Time spent
    total_time_spent = serializers.SerializerMethodField()
    
    # Activity
    last_activity = serializers.SerializerMethodField()
    needs_review_count = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def get_total_items(self, obj):
        """Total vocabulary items in curriculum"""
        return VocabularyItem.objects.count()

    def get_mastered_count(self, obj):
        """Items at 'mastered' level"""
        if not self.user:
            return 0
        return StudentVocabMastery.objects.filter(
            user=self.user,
            mastery_level='mastered'
        ).count()

    def get_learning_count(self, obj):
        """Items at 'learning' level"""
        if not self.user:
            return 0
        return StudentVocabMastery.objects.filter(
            user=self.user,
            mastery_level='learning'
        ).count()

    def get_review_count(self, obj):
        """Items at 'review' level"""
        if not self.user:
            return 0
        return StudentVocabMastery.objects.filter(
            user=self.user,
            mastery_level='review'
        ).count()

    def get_new_count(self, obj):
        """Items never attempted or at 'new' level"""
        if not self.user:
            return self.get_total_items(obj)
        
        mastered_items = StudentVocabMastery.objects.filter(
            user=self.user
        ).values_list('vocab_item_id', flat=True)
        
        total = self.get_total_items(obj)
        return total - mastered_items.count()

    def get_mastery_percentage(self, obj):
        """Percentage of items mastered"""
        total = self.get_total_items(obj)
        if total == 0:
            return 0
        mastered = self.get_mastered_count(obj)
        return (mastered / total) * 100

    def get_total_attempts(self, obj):
        """Total vocabulary attempts"""
        if not self.user:
            return 0
        return VocabularyAttempt.objects.filter(user=self.user).count()

    def get_overall_accuracy(self, obj):
        """Overall accuracy percentage"""
        if not self.user:
            return 0
        attempts = VocabularyAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        correct = attempts.filter(is_correct=True).count()
        return (correct / attempts.count()) * 100

    def get_total_time_spent(self, obj):
        """Total minutes spent on vocabulary"""
        if not self.user:
            return 0
        total_seconds = VocabularyAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        return total_seconds // 60

    def get_last_activity(self, obj):
        """Most recent vocabulary attempt"""
        if not self.user:
            return None
        last = VocabularyAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        return last

    def get_needs_review_count(self, obj):
        """Items needing review (review level or low accuracy)"""
        if not self.user:
            return 0
        
        review_items = StudentVocabMastery.objects.filter(
            user=self.user,
            mastery_level='review'
        ).count()
        
        low_accuracy = StudentVocabMastery.objects.filter(
            user=self.user,
            mastery_level='learning',
            correct_attempts__lt=models.F('total_attempts') * 0.7
        ).count()
        
        return review_items + low_accuracy


class ComprehensionProgressSerializer(serializers.Serializer):
    """Comprehension domain progress summary (Bloom's levels)"""
    
    total_focuses = serializers.SerializerMethodField()
    mastered_focuses = serializers.SerializerMethodField()
    in_progress_focuses = serializers.SerializerMethodField()
    not_started_focuses = serializers.SerializerMethodField()
    mastery_percentage = serializers.SerializerMethodField()
    
    # Bloom's level breakdown
    by_bloom_level = serializers.SerializerMethodField()
    
    total_practice_attempts = serializers.SerializerMethodField()
    average_practice_score = serializers.SerializerMethodField()
    total_test_attempts = serializers.SerializerMethodField()
    average_test_score = serializers.SerializerMethodField()
    total_time_spent = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    needs_review_count = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def get_total_focuses(self, obj):
        return ChunkComprehensionFocus.objects.count()

    def get_mastered_focuses(self, obj):
        if not self.user:
            return 0
        return ComprehensionTestAttempt.objects.filter(
            user=self.user,
            is_mastered=True
        ).values('focus').distinct().count()

    def get_in_progress_focuses(self, obj):
        if not self.user:
            return 0
        attempted = ComprehensionTestAttempt.objects.filter(
            user=self.user
        ).values_list('focus_id', flat=True).distinct()
        mastered = ComprehensionTestAttempt.objects.filter(
            user=self.user,
            is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        return len(set(attempted) - set(mastered))

    def get_not_started_focuses(self, obj):
        total = self.get_total_focuses(obj)
        mastered = self.get_mastered_focuses(obj)
        in_progress = self.get_in_progress_focuses(obj)
        return total - (mastered + in_progress)

    def get_mastery_percentage(self, obj):
        total = self.get_total_focuses(obj)
        if total == 0:
            return 0
        mastered = self.get_mastered_focuses(obj)
        return (mastered / total) * 100

    def get_by_bloom_level(self, obj):
        """Breakdown by Bloom's taxonomy level"""
        if not self.user:
            return {}
        
        from content.models.comprehension import BloomLevel
        
        result = {}
        for level in BloomLevel.values:
            total = ChunkComprehensionFocus.objects.filter(level=level).count()
            
            mastered = ComprehensionTestAttempt.objects.filter(
                user=self.user,
                focus__level=level,
                is_mastered=True
            ).values('focus').distinct().count()
            
            result[level] = {
                'total': total,
                'mastered': mastered,
                'percentage': (mastered / total * 100) if total > 0 else 0
            }
        
        return result

    def get_total_practice_attempts(self, obj):
        if not self.user:
            return 0
        return ComprehensionPracticeAttempt.objects.filter(user=self.user).count()

    def get_average_practice_score(self, obj):
        if not self.user:
            return 0
        attempts = ComprehensionPracticeAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        return attempts.aggregate(avg=models.Avg('score_percent'))['avg'] or 0

    def get_total_test_attempts(self, obj):
        if not self.user:
            return 0
        return ComprehensionTestAttempt.objects.filter(user=self.user).count()

    def get_average_test_score(self, obj):
        if not self.user:
            return 0
        attempts = ComprehensionTestAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        return attempts.aggregate(avg=models.Avg('score_percent'))['avg'] or 0

    def get_total_time_spent(self, obj):
        if not self.user:
            return 0
        total_seconds = 0
        practice_time = ComprehensionPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += practice_time
        test_time = ComprehensionTestAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += test_time
        return total_seconds // 60

    def get_last_activity(self, obj):
        if not self.user:
            return None
        last_practice = ComprehensionPracticeAttempt.objects.filter(
            user=self.user
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        last_test = ComprehensionTestAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if not last_practice and not last_test:
            return None
        if last_practice and last_test:
            return max(last_practice, last_test)
        return last_practice or last_test

    def get_needs_review_count(self, obj):
        if not self.user:
            return 0
        recent_failures = ComprehensionTestAttempt.objects.filter(
            user=self.user,
            is_mastered=False,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).values_list('focus_id', flat=True).distinct()
        return len(recent_failures)


class WritingProgressSerializer(serializers.Serializer):
    """Writing domain progress summary (chunk and unit level)"""
    
    # Chunk-level focuses
    chunk_focuses_total = serializers.SerializerMethodField()
    chunk_focuses_mastered = serializers.SerializerMethodField()
    chunk_mastery_percentage = serializers.SerializerMethodField()
    
    # Unit-level tasks
    unit_tasks_total = serializers.SerializerMethodField()
    unit_tasks_mastered = serializers.SerializerMethodField()
    unit_mastery_percentage = serializers.SerializerMethodField()
    
    # Practice stats
    total_practice_attempts = serializers.SerializerMethodField()
    average_practice_score = serializers.SerializerMethodField()
    
    # Test stats
    total_test_attempts = serializers.SerializerMethodField()
    average_test_score = serializers.SerializerMethodField()
    
    # By stage (paragraph, essay, etc.)
    by_stage = serializers.SerializerMethodField()
    
    total_time_spent = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    needs_review_count = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def get_chunk_focuses_total(self, obj):
        return ChunkWritingFocus.objects.count()

    def get_chunk_focuses_mastered(self, obj):
        if not self.user:
            return 0
        return WritingTestAttempt.objects.filter(
            user=self.user,
            focus__isnull=False,
            is_mastered=True
        ).values('focus').distinct().count()

    def get_chunk_mastery_percentage(self, obj):
        total = self.get_chunk_focuses_total(obj)
        if total == 0:
            return 0
        mastered = self.get_chunk_focuses_mastered(obj)
        return (mastered / total) * 100

    def get_unit_tasks_total(self, obj):
        return UnitWritingTask.objects.count()

    def get_unit_tasks_mastered(self, obj):
        if not self.user:
            return 0
        return WritingTestAttempt.objects.filter(
            user=self.user,
            task__isnull=False,
            is_mastered=True
        ).values('task').distinct().count()

    def get_unit_mastery_percentage(self, obj):
        total = self.get_unit_tasks_total(obj)
        if total == 0:
            return 0
        mastered = self.get_unit_tasks_mastered(obj)
        return (mastered / total) * 100

    def get_total_practice_attempts(self, obj):
        if not self.user:
            return 0
        return WritingPracticeAttempt.objects.filter(user=self.user).count()

    def get_average_practice_score(self, obj):
        if not self.user:
            return 0
        attempts = WritingPracticeAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        return attempts.aggregate(avg=models.Avg('keyword_match_score'))['avg'] or 0

    def get_total_test_attempts(self, obj):
        if not self.user:
            return 0
        return WritingTestAttempt.objects.filter(user=self.user).count()

    def get_average_test_score(self, obj):
        if not self.user:
            return 0
        attempts = WritingTestAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        return attempts.aggregate(avg=models.Avg('overall_score'))['avg'] or 0

    def get_by_stage(self, obj):
        """Breakdown by writing stage (paragraph, essay, etc.)"""
        if not self.user:
            return {}
        
        result = {}
        for stage_code, stage_name in UnitWritingTask.STAGE_CHOICES:
            total = UnitWritingTask.objects.filter(stage=stage_code).count()
            
            mastered = WritingTestAttempt.objects.filter(
                user=self.user,
                task__stage=stage_code,
                is_mastered=True
            ).values('task').distinct().count()
            
            result[stage_code] = {
                'name': stage_name,
                'total': total,
                'mastered': mastered,
                'percentage': (mastered / total * 100) if total > 0 else 0
            }
        
        return result

    def get_total_time_spent(self, obj):
        if not self.user:
            return 0
        total_seconds = 0
        practice_time = WritingPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_spent_seconds'))['total'] or 0
        total_seconds += practice_time
        test_time = WritingTestAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_spent_seconds'))['total'] or 0
        total_seconds += test_time
        return total_seconds // 60

    def get_last_activity(self, obj):
        if not self.user:
            return None
        last_practice = WritingPracticeAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        last_test = WritingTestAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if not last_practice and not last_test:
            return None
        if last_practice and last_test:
            return max(last_practice, last_test)
        return last_practice or last_test

    def get_needs_review_count(self, obj):
        if not self.user:
            return 0
        
        chunk_failures = WritingTestAttempt.objects.filter(
            user=self.user,
            focus__isnull=False,
            is_mastered=False,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).values_list('focus_id', flat=True).distinct()
        
        task_failures = WritingTestAttempt.objects.filter(
            user=self.user,
            task__isnull=False,
            is_mastered=False,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).values_list('task_id', flat=True).distinct()
        
        return len(chunk_failures) + len(task_failures)


class PronunciationProgressSerializer(serializers.Serializer):
    """Pronunciation domain progress summary"""
    
    total_focuses = serializers.SerializerMethodField()
    mastered_focuses = serializers.SerializerMethodField()
    in_progress_focuses = serializers.SerializerMethodField()
    not_started_focuses = serializers.SerializerMethodField()
    mastery_percentage = serializers.SerializerMethodField()
    
    total_attempts = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()
    
    total_time_spent = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    needs_review_count = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def get_total_focuses(self, obj):
        return PronunciationFocus.objects.count()

    def get_mastered_focuses(self, obj):
        if not self.user:
            return 0
        return PronunciationMastery.objects.filter(
            user=self.user,
            is_mastered=True
        ).count()

    def get_in_progress_focuses(self, obj):
        if not self.user:
            return 0
        return PronunciationMastery.objects.filter(
            user=self.user,
            is_mastered=False,
            total_attempts__gt=0
        ).count()

    def get_not_started_focuses(self, obj):
        if not self.user:
            return self.get_total_focuses(obj)
        
        started = PronunciationMastery.objects.filter(
            user=self.user
        ).values_list('focus_id', flat=True)
        
        total = self.get_total_focuses(obj)
        return total - len(started)

    def get_mastery_percentage(self, obj):
        total = self.get_total_focuses(obj)
        if total == 0:
            return 0
        mastered = self.get_mastered_focuses(obj)
        return (mastered / total) * 100

    def get_total_attempts(self, obj):
        if not self.user:
            return 0
        return PronunciationAttempt.objects.filter(user=self.user).count()

    def get_average_score(self, obj):
        if not self.user:
            return 0
        attempts = PronunciationAttempt.objects.filter(
            user=self.user,
            ai_score__isnull=False
        )
        if not attempts.exists():
            return 0
        return attempts.aggregate(avg=models.Avg('ai_score'))['avg'] or 0

    def get_best_score(self, obj):
        if not self.user:
            return 0
        best = PronunciationMastery.objects.filter(
            user=self.user
        ).aggregate(best=models.Max('best_score'))['best']
        return best or 0

    def get_total_time_spent(self, obj):
        if not self.user:
            return 0
        return 0

    def get_last_activity(self, obj):
        if not self.user:
            return None
        last = PronunciationAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        return last

    def get_needs_review_count(self, obj):
        if not self.user:
            return 0
        
        needs_review = PronunciationMastery.objects.filter(
            user=self.user,
            is_mastered=False,
            last_attempted__lt=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        return needs_review


class UnitTestProgressSerializer(serializers.Serializer):
    """Unit test progress summary"""
    
    total_units = serializers.SerializerMethodField()
    units_passed = serializers.SerializerMethodField()
    units_failed = serializers.SerializerMethodField()
    units_not_attempted = serializers.SerializerMethodField()
    pass_percentage = serializers.SerializerMethodField()
    
    total_test_sessions = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()
    
    # By unit
    unit_breakdown = serializers.SerializerMethodField()
    
    last_activity = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def get_total_units(self, obj):
        return Unit.objects.count()

    def get_units_passed(self, obj):
        if not self.user:
            return 0
        
        passed_units = UnitTestSession.objects.filter(
            user=self.user,
            passed=True
        ).values_list('unit_id', flat=True).distinct()
        
        return len(passed_units)

    def get_units_failed(self, obj):
        if not self.user:
            return 0
        
        attempted = UnitTestSession.objects.filter(
            user=self.user
        ).values_list('unit_id', flat=True).distinct()
        
        passed = UnitTestSession.objects.filter(
            user=self.user,
            passed=True
        ).values_list('unit_id', flat=True).distinct()
        
        return len(set(attempted) - set(passed))

    def get_units_not_attempted(self, obj):
        total = self.get_total_units(obj)
        attempted = UnitTestSession.objects.filter(
            user=self.user
        ).values_list('unit_id', flat=True).distinct().count() if self.user else 0
        return total - attempted

    def get_pass_percentage(self, obj):
        total = self.get_total_units(obj)
        if total == 0:
            return 0
        passed = self.get_units_passed(obj)
        return (passed / total) * 100

    def get_total_test_sessions(self, obj):
        if not self.user:
            return 0
        return UnitTestSession.objects.filter(user=self.user).count()

    def get_average_score(self, obj):
        if not self.user:
            return 0
        sessions = UnitTestSession.objects.filter(user=self.user)
        if not sessions.exists():
            return 0
        return sessions.aggregate(avg=models.Avg('score_percentage'))['avg'] or 0

    def get_unit_breakdown(self, obj):
        """Performance breakdown by unit"""
        if not self.user:
            return []
        
        result = []
        for unit in Unit.objects.all().order_by('number'):
            sessions = UnitTestSession.objects.filter(
                user=self.user,
                unit=unit
            ).order_by('-attempt_number')
            
            if sessions.exists():
                best = sessions.order_by('-score_percentage').first()
                latest = sessions.first()
                
                result.append({
                    'unit_id': unit.id,
                    'unit_title': unit.title,
                    'unit_number': unit.number,
                    'attempts': sessions.count(),
                    'best_score': best.score_percentage,
                    'latest_score': latest.score_percentage,
                    'passed': any(s.passed for s in sessions),
                    'last_attempted': latest.started_at,
                })
            else:
                result.append({
                    'unit_id': unit.id,
                    'unit_title': unit.title,
                    'unit_number': unit.number,
                    'attempts': 0,
                    'best_score': None,
                    'latest_score': None,
                    'passed': False,
                    'last_attempted': None,
                })
        
        return result

    def get_last_activity(self, obj):
        if not self.user:
            return None
        last = UnitTestSession.objects.filter(
            user=self.user
        ).order_by('-started_at').values_list('started_at', flat=True).first()
        return last


# ============================================================
# MOBILE-OPTIMIZED SERIALIZERS (ADD THIS SECTION)
# ============================================================

class DomainProgressMobileSerializer(serializers.Serializer):
    """Minimal domain progress for mobile dashboard"""
    mastery_percentage = serializers.FloatField()
    needs_review_count = serializers.IntegerField()
    last_activity = serializers.DateTimeField(allow_null=True)


class DashboardMobileSerializer(serializers.Serializer):
    """Main mobile dashboard - ultra lightweight"""
    
    # Quick stats
    streak_days = serializers.IntegerField()
    overall_mastery = serializers.FloatField()
    
    # Domain summaries (minimal)
    grammar = DomainProgressMobileSerializer()
    punctuation = DomainProgressMobileSerializer()
    vocabulary = DomainProgressMobileSerializer()
    comprehension = DomainProgressMobileSerializer()
    writing = DomainProgressMobileSerializer()
    pronunciation = DomainProgressMobileSerializer()
    
    # Recent activity (last 5 items)
    recent_activity = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Next steps (top 3)
    next_steps = serializers.ListField(
        child=serializers.DictField()
    )
    
    # In-progress items
    in_progress = serializers.ListField(
        child=serializers.DictField()
    )


# ============================================================
# OVERALL PROGRESS SERIALIZERS
# ============================================================

class OverallProgressSerializer(serializers.Serializer):
    """
    Complete student progress dashboard aggregating all domains.
    This is the main serializer for the student dashboard.
    """
    
    # Student info
    student_id = serializers.IntegerField(read_only=True)
    student_name = serializers.CharField(read_only=True)
    
    # Domain-specific progress
    grammar = GrammarProgressSerializer(read_only=True)
    punctuation = PunctuationProgressSerializer(read_only=True)
    vocabulary = VocabularyProgressSerializer(read_only=True)
    comprehension = ComprehensionProgressSerializer(read_only=True)
    writing = WritingProgressSerializer(read_only=True)
    pronunciation = PronunciationProgressSerializer(read_only=True)
    unit_tests = UnitTestProgressSerializer(read_only=True)
    
    # Overall metrics
    overall_mastery = serializers.SerializerMethodField()
    total_practices = serializers.SerializerMethodField()
    total_time_spent_hours = serializers.SerializerMethodField()
    streak_days = serializers.SerializerMethodField()
    
    # Recent activity
    recent_activity = serializers.SerializerMethodField()
    
    # Recommendations
    recommended_focus = serializers.SerializerMethodField()
    upcoming_tests = serializers.SerializerMethodField()
    
    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance')
        domain_kwargs = {'user': self.user}
        
        if 'context' in kwargs:
            kwargs['context'].update(domain_kwargs)
        else:
            kwargs['context'] = domain_kwargs
        
        super().__init__(*args, **kwargs)

    def get_overall_mastery(self, obj):
        """Calculate overall mastery across all domains"""
        if not self.user:
            return 0
        
        grammar = GrammarProgressSerializer(user=self.user).data
        punctuation = PunctuationProgressSerializer(user=self.user).data
        vocabulary = VocabularyProgressSerializer(user=self.user).data
        comprehension = ComprehensionProgressSerializer(user=self.user).data
        writing = WritingProgressSerializer(user=self.user).data
        pronunciation = PronunciationProgressSerializer(user=self.user).data
        
        percentages = [
            grammar.get('mastery_percentage', 0),
            punctuation.get('mastery_percentage', 0),
            vocabulary.get('mastery_percentage', 0),
            comprehension.get('mastery_percentage', 0),
            writing.get('chunk_mastery_percentage', 0),
            pronunciation.get('mastery_percentage', 0)
        ]
        
        valid_percentages = [p for p in percentages if p > 0]
        if not valid_percentages:
            return 0
        
        return sum(valid_percentages) / len(valid_percentages)

    def get_total_practices(self, obj):
        """Total practice attempts across all domains"""
        if not self.user:
            return 0
        
        total = 0
        total += GrammarPracticeAttempt.objects.filter(user=self.user).count()
        total += PunctuationPracticeAttempt.objects.filter(user=self.user).count()
        total += VocabularyAttempt.objects.filter(user=self.user).count()
        total += ComprehensionPracticeAttempt.objects.filter(user=self.user).count()
        total += WritingPracticeAttempt.objects.filter(user=self.user).count()
        total += PronunciationAttempt.objects.filter(user=self.user).count()
        
        return total

    def get_total_time_spent_hours(self, obj):
        """Total hours spent across all domains"""
        if not self.user:
            return 0
        
        total_minutes = 0
        
        grammar_seconds = GrammarPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_minutes += grammar_seconds // 60
        
        punct_seconds = PunctuationPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_minutes += punct_seconds // 60
        
        vocab_seconds = VocabularyAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_minutes += vocab_seconds // 60
        
        comp_seconds = ComprehensionPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_minutes += comp_seconds // 60
        
        writing_seconds = WritingPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_spent_seconds'))['total'] or 0
        total_minutes += writing_seconds // 60
        
        test_seconds = UnitTestSession.objects.filter(
            user=self.user,
            completed_at__isnull=False
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_minutes += test_seconds // 60
        
        return total_minutes / 60

    def get_streak_days(self, obj):
        """Calculate current activity streak in days"""
        if not self.user:
            return 0
        
        from django.db.models.functions import TruncDate
        
        activity_dates = set()
        
        grammar_dates = GrammarPracticeAttempt.objects.filter(
            user=self.user
        ).annotate(date=TruncDate('attempted_at')).values_list('date', flat=True)
        activity_dates.update(grammar_dates)
        
        punct_dates = PunctuationPracticeAttempt.objects.filter(
            user=self.user
        ).annotate(date=TruncDate('created_at')).values_list('date', flat=True)
        activity_dates.update(punct_dates)
        
        vocab_dates = VocabularyAttempt.objects.filter(
            user=self.user
        ).annotate(date=TruncDate('created_at')).values_list('date', flat=True)
        activity_dates.update(vocab_dates)
        
        comp_dates = ComprehensionPracticeAttempt.objects.filter(
            user=self.user
        ).annotate(date=TruncDate('attempted_at')).values_list('date', flat=True)
        activity_dates.update(comp_dates)
        
        writing_dates = WritingPracticeAttempt.objects.filter(
            user=self.user
        ).annotate(date=TruncDate('created_at')).values_list('date', flat=True)
        activity_dates.update(writing_dates)
        
        pron_dates = PronunciationAttempt.objects.filter(
            user=self.user
        ).annotate(date=TruncDate('created_at')).values_list('date', flat=True)
        activity_dates.update(pron_dates)
        
        test_dates = UnitTestSession.objects.filter(
            user=self.user
        ).annotate(date=TruncDate('started_at')).values_list('date', flat=True)
        activity_dates.update(test_dates)
        
        if not activity_dates:
            return 0
        
        sorted_dates = sorted(activity_dates, reverse=True)
        today = timezone.now().date()
        
        streak = 0
        current_date = today
        
        while current_date in sorted_dates:
            streak += 1
            current_date -= timezone.timedelta(days=1)
        
        return streak

    def get_recent_activity(self, obj):
        """Get 10 most recent activities across all domains"""
        if not self.user:
            return []
        
        activities = []
        
        for attempt in GrammarPracticeAttempt.objects.filter(
            user=self.user
        ).order_by('-attempted_at')[:3]:
            activities.append({
                'type': 'grammar_practice',
                'domain': 'grammar',
                'score': attempt.score_percent,
                'passed': attempt.is_passed,
                'timestamp': attempt.attempted_at,
                'description': f"Grammar practice: {attempt.score_percent}%"
            })
        
        for attempt in GrammarTestAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at')[:3]:
            activities.append({
                'type': 'grammar_test',
                'domain': 'grammar',
                'score': attempt.score_percent,
                'mastered': attempt.is_mastered,
                'timestamp': attempt.created_at,
                'description': f"Grammar test: {attempt.score_percent}%"
            })
        
        for attempt in VocabularyAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at')[:3]:
            activities.append({
                'type': 'vocabulary',
                'domain': 'vocabulary',
                'correct': attempt.is_correct,
                'timestamp': attempt.created_at,
                'description': f"Vocabulary: {'correct' if attempt.is_correct else 'incorrect'}"
            })
        
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:10]

    def get_recommended_focus(self, obj):
        """Generate personalized recommendations based on performance"""
        if not self.user:
            return []
        
        recommendations = []
        
        grammar_failures = GrammarTestAttempt.objects.filter(
            user=self.user,
            is_mastered=False
        ).order_by('-created_at').values_list('focus_id', flat=True).distinct()[:3]
        
        for focus_id in grammar_failures:
            try:
                focus = ChunkGrammarFocus.objects.get(id=focus_id)
                recommendations.append({
                    'domain': 'grammar',
                    'type': 'focus',
                    'id': focus_id,
                    'title': focus.focus_title,
                    'reason': 'Needs review (test failed)',
                    'priority': 'high'
                })
            except ChunkGrammarFocus.DoesNotExist:
                pass
        
        vocab_review = StudentVocabMastery.objects.filter(
            user=self.user,
            mastery_level='review'
        ).select_related('vocab_item')[:3]
        
        for mastery in vocab_review:
            recommendations.append({
                'domain': 'vocabulary',
                'type': 'item',
                'id': mastery.vocab_item_id,
                'title': mastery.vocab_item.word,
                'reason': 'Needs review (low retention)',
                'priority': 'medium'
            })
        
        return recommendations[:5]

    def get_upcoming_tests(self, obj):
        """Identify upcoming unit tests based on progress"""
        if not self.user:
            return []
        
        upcoming = []
        
        all_units = Unit.objects.all().order_by('number')
        
        for unit in all_units:
            sessions = UnitTestSession.objects.filter(
                user=self.user,
                unit=unit
            )
            
            if not sessions.exists():
                upcoming.append({
                    'unit_id': unit.id,
                    'unit_title': unit.title,
                    'unit_number': unit.number,
                    'status': 'available',
                    'attempts_remaining': 3,
                    'reason': 'Not started'
                })
            else:
                latest = sessions.order_by('-attempt_number').first()
                if not latest.passed and sessions.count() < 3:
                    upcoming.append({
                        'unit_id': unit.id,
                        'unit_title': unit.title,
                        'unit_number': unit.number,
                        'status': 'retake_available',
                        'attempts_remaining': 3 - sessions.count(),
                        'last_score': latest.score_percentage,
                        'reason': f'Retry available ({3 - sessions.count()} attempts left)'
                    })
        
        return upcoming[:5]


# ============================================================
# UNIT & LESSON PROGRESS SERIALIZERS
# ============================================================

class UnitProgressDetailSerializer(serializers.Serializer):
    """Detailed progress for a specific unit"""
    
    unit_id = serializers.IntegerField()
    unit_title = serializers.CharField()
    unit_number = serializers.IntegerField()
    
    # Lesson completion
    total_lessons = serializers.SerializerMethodField()
    lessons_completed = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    
    # Test performance
    test_attempts = serializers.SerializerMethodField()
    best_test_score = serializers.SerializerMethodField()
    latest_test_score = serializers.SerializerMethodField()
    test_passed = serializers.SerializerMethodField()
    
    # Time spent
    time_spent_minutes = serializers.SerializerMethodField()
    
    # Domain mastery within unit
    domain_mastery = serializers.SerializerMethodField()
    
    # Last activity
    last_activity = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.unit = kwargs.pop('unit', None)
        super().__init__(*args, **kwargs)

    def get_total_lessons(self, obj):
        if not self.unit:
            return 0
        return self.unit.lessons.count()

    def get_lessons_completed(self, obj):
        """Calculate completed lessons based on chunk mastery"""
        if not self.user or not self.unit:
            return 0
        
        completed = 0
        for lesson in self.unit.lessons.all():
            chunks = lesson.chunks.all()
            if chunks.exists() and all(
                chunk.is_mastered_by(self.user) for chunk in chunks
            ):
                completed += 1
        
        return completed

    def get_completion_percentage(self, obj):
        total = self.get_total_lessons(obj)
        if total == 0:
            return 0
        completed = self.get_lessons_completed(obj)
        return (completed / total) * 100

    def get_test_attempts(self, obj):
        if not self.user or not self.unit:
            return 0
        return UnitTestSession.objects.filter(
            user=self.user,
            unit=self.unit
        ).count()

    def get_best_test_score(self, obj):
        if not self.user or not self.unit:
            return None
        best = UnitTestSession.objects.filter(
            user=self.user,
            unit=self.unit
        ).order_by('-score_percentage').first()
        return best.score_percentage if best else None

    def get_latest_test_score(self, obj):
        if not self.user or not self.unit:
            return None
        latest = UnitTestSession.objects.filter(
            user=self.user,
            unit=self.unit
        ).order_by('-started_at').first()
        return latest.score_percentage if latest else None

    def get_test_passed(self, obj):
        if not self.user or not self.unit:
            return False
        return UnitTestSession.objects.filter(
            user=self.user,
            unit=self.unit,
            passed=True
        ).exists()

    def get_time_spent_minutes(self, obj):
        if not self.user or not self.unit:
            return 0
        
        total_seconds = 0
        
        test_time = UnitTestSession.objects.filter(
            user=self.user,
            unit=self.unit,
            completed_at__isnull=False
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += test_time
        
        chunks = LessonChunk.objects.filter(lesson__unit=self.unit)
        
        grammar_time = GrammarPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += grammar_time
        
        punct_time = PunctuationPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += punct_time
        
        vocab_time = VocabularyAttempt.objects.filter(
            user=self.user,
            vocab_item__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += vocab_time
        
        comp_time = ComprehensionPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += comp_time
        
        writing_time = WritingPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_spent_seconds'))['total'] or 0
        total_seconds += writing_time
        
        return total_seconds // 60

    def get_domain_mastery(self, obj):
        """Mastery percentages for each domain within this unit"""
        if not self.user or not self.unit:
            return {}
        
        chunks = LessonChunk.objects.filter(lesson__unit=self.unit)
        
        result = {}
        
        grammar_focuses = ChunkGrammarFocus.objects.filter(chunk__in=chunks)
        if grammar_focuses.exists():
            mastered = 0
            for focus in grammar_focuses:
                if GrammarTestAttempt.objects.filter(
                    user=self.user,
                    focus=focus,
                    is_mastered=True
                ).exists():
                    mastered += 1
            result['grammar'] = (mastered / grammar_focuses.count()) * 100
        
        punct_focuses = ChunkPunctuationFocus.objects.filter(chunk__in=chunks)
        if punct_focuses.exists():
            mastered = 0
            for focus in punct_focuses:
                if PunctuationTestAttempt.objects.filter(
                    user=self.user,
                    focus=focus,
                    is_mastered=True
                ).exists():
                    mastered += 1
            result['punctuation'] = (mastered / punct_focuses.count()) * 100
        
        vocab_items = VocabularyItem.objects.filter(chunk__in=chunks)
        if vocab_items.exists():
            mastered = StudentVocabMastery.objects.filter(
                user=self.user,
                vocab_item__in=vocab_items,
                mastery_level='mastered'
            ).count()
            result['vocabulary'] = (mastered / vocab_items.count()) * 100
        
        comp_focuses = ChunkComprehensionFocus.objects.filter(chunk__in=chunks)
        if comp_focuses.exists():
            mastered = 0
            for focus in comp_focuses:
                if ComprehensionTestAttempt.objects.filter(
                    user=self.user,
                    focus=focus,
                    is_mastered=True
                ).exists():
                    mastered += 1
            result['comprehension'] = (mastered / comp_focuses.count()) * 100
        
        writing_focuses = ChunkWritingFocus.objects.filter(chunk__in=chunks)
        if writing_focuses.exists():
            mastered = 0
            for focus in writing_focuses:
                if WritingTestAttempt.objects.filter(
                    user=self.user,
                    focus=focus,
                    is_mastered=True
                ).exists():
                    mastered += 1
            result['writing'] = (mastered / writing_focuses.count()) * 100
        
        pron_focuses = PronunciationFocus.objects.filter(chunk__in=chunks)
        if pron_focuses.exists():
            mastered = PronunciationMastery.objects.filter(
                user=self.user,
                focus__in=pron_focuses,
                is_mastered=True
            ).count()
            result['pronunciation'] = (mastered / pron_focuses.count()) * 100
        
        return result

    def get_last_activity(self, obj):
        """Most recent activity timestamp for this unit"""
        if not self.user or not self.unit:
            return None
        
        chunks = LessonChunk.objects.filter(lesson__unit=self.unit)
        
        timestamps = []
        
        grammar_time = GrammarPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        if grammar_time:
            timestamps.append(grammar_time)
        
        punct_time = PunctuationPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if punct_time:
            timestamps.append(punct_time)
        
        vocab_time = VocabularyAttempt.objects.filter(
            user=self.user,
            vocab_item__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if vocab_time:
            timestamps.append(vocab_time)
        
        comp_time = ComprehensionPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        if comp_time:
            timestamps.append(comp_time)
        
        writing_time = WritingPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if writing_time:
            timestamps.append(writing_time)
        
        pron_time = PronunciationAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if pron_time:
            timestamps.append(pron_time)
        
        test_time = UnitTestSession.objects.filter(
            user=self.user,
            unit=self.unit
        ).order_by('-started_at').values_list('started_at', flat=True).first()
        if test_time:
            timestamps.append(test_time)
        
        if timestamps:
            return max(timestamps)
        return None


class LessonProgressSerializer(serializers.Serializer):
    """Progress for a specific lesson"""
    
    lesson_id = serializers.IntegerField()
    lesson_title = serializers.CharField()
    lesson_number = serializers.IntegerField()
    
    # Chunk completion
    total_chunks = serializers.SerializerMethodField()
    chunks_completed = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    
    # Chunk-level mastery
    chunk_mastery = serializers.SerializerMethodField()
    
    # Time spent
    time_spent_minutes = serializers.SerializerMethodField()
    
    # Last activity
    last_activity = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.lesson = kwargs.pop('lesson', None)
        super().__init__(*args, **kwargs)

    def get_total_chunks(self, obj):
        if not self.lesson:
            return 0
        return self.lesson.chunks.count()

    def get_chunks_completed(self, obj):
        """Chunks where all domains are mastered"""
        if not self.user or not self.lesson:
            return 0
        
        completed = 0
        for chunk in self.lesson.chunks.all():
            if chunk.is_mastered_by(self.user):
                completed += 1
        
        return completed

    def get_completion_percentage(self, obj):
        total = self.get_total_chunks(obj)
        if total == 0:
            return 0
        completed = self.get_chunks_completed(obj)
        return (completed / total) * 100

    def get_chunk_mastery(self, obj):
        """Mastery status for each chunk"""
        if not self.user or not self.lesson:
            return []
        
        result = []
        for chunk in self.lesson.chunks.all().order_by('order'):
            status = chunk.get_mastery_status(self.user)
            result.append({
                'chunk_id': chunk.id,
                'order': chunk.order,
                'mastered': status['overall'] if status else False,
                'by_domain': status['by_domain'] if status else {},
                'next_domain': status['next_domain_to_work'] if status else None,
            })
        
        return result

    def get_time_spent_minutes(self, obj):
        """Total minutes spent on this lesson"""
        if not self.user or not self.lesson:
            return 0
        
        chunks = self.lesson.chunks.all()
        total_seconds = 0
        
        grammar_time = GrammarPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += grammar_time
        
        punct_time = PunctuationPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += punct_time
        
        vocab_time = VocabularyAttempt.objects.filter(
            user=self.user,
            vocab_item__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += vocab_time
        
        comp_time = ComprehensionPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += comp_time
        
        writing_time = WritingPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_spent_seconds'))['total'] or 0
        total_seconds += writing_time
        
        pron_time = PronunciationAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += pron_time
        
        return total_seconds // 60

    def get_last_activity(self, obj):
        """Most recent activity timestamp for this lesson"""
        if not self.user or not self.lesson:
            return None
        
        chunks = self.lesson.chunks.all()
        timestamps = []
        
        grammar_time = GrammarPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        if grammar_time:
            timestamps.append(grammar_time)
        
        punct_time = PunctuationPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if punct_time:
            timestamps.append(punct_time)
        
        vocab_time = VocabularyAttempt.objects.filter(
            user=self.user,
            vocab_item__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if vocab_time:
            timestamps.append(vocab_time)
        
        comp_time = ComprehensionPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        if comp_time:
            timestamps.append(comp_time)
        
        writing_time = WritingPracticeAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if writing_time:
            timestamps.append(writing_time)
        
        pron_time = PronunciationAttempt.objects.filter(
            user=self.user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if pron_time:
            timestamps.append(pron_time)
        
        if timestamps:
            return max(timestamps)
        return None


# ============================================================
# EXPORTS (Add at the end of the file)
# ============================================================

__all__ = [
    'GrammarProgressSerializer',
    'PunctuationProgressSerializer',
    'VocabularyProgressSerializer',
    'ComprehensionProgressSerializer',
    'WritingProgressSerializer',
    'PronunciationProgressSerializer',
    'UnitTestProgressSerializer',
    'OverallProgressSerializer',
    'DomainProgressMobileSerializer',
    'DashboardMobileSerializer',
    'UnitProgressDetailSerializer',
    'LessonProgressSerializer',
]