# content/serializers/progress.py

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

# Writing — new three-tier architecture
from content.models.writing import (
    WritingAttempt,
    WritingStageMastery,
    WritingStageContent,
    WritingAcademicYear,
    PHASE_DISSECT,
    PHASE_IMITATE,
    PHASE_PRODUCE,
    TIER_SENTENCE,
    TIER_PARAGRAPH,
    TIER_GENRE,
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

    total_focuses           = serializers.SerializerMethodField()
    mastered_focuses        = serializers.SerializerMethodField()
    in_progress_focuses     = serializers.SerializerMethodField()
    not_started_focuses     = serializers.SerializerMethodField()
    mastery_percentage      = serializers.SerializerMethodField()
    total_practice_attempts = serializers.SerializerMethodField()
    average_practice_score  = serializers.SerializerMethodField()
    total_test_attempts     = serializers.SerializerMethodField()
    average_test_score      = serializers.SerializerMethodField()
    total_time_spent        = serializers.SerializerMethodField()
    last_activity           = serializers.SerializerMethodField()
    needs_review_count      = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def get_total_focuses(self, obj):
        return ChunkGrammarFocus.objects.count()

    def get_mastered_focuses(self, obj):
        if not self.user:
            return 0
        return GrammarTestAttempt.objects.filter(
            user=self.user, is_mastered=True
        ).values('focus').distinct().count()

    def get_in_progress_focuses(self, obj):
        if not self.user:
            return 0
        attempted = GrammarTestAttempt.objects.filter(
            user=self.user
        ).values_list('focus_id', flat=True).distinct()
        mastered = GrammarTestAttempt.objects.filter(
            user=self.user, is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        return len(set(attempted) - set(mastered))

    def get_not_started_focuses(self, obj):
        return (
            self.get_total_focuses(obj)
            - self.get_mastered_focuses(obj)
            - self.get_in_progress_focuses(obj)
        )

    def get_mastery_percentage(self, obj):
        total = self.get_total_focuses(obj)
        if total == 0:
            return 0
        return (self.get_mastered_focuses(obj) / total) * 100

    def get_total_practice_attempts(self, obj):
        if not self.user:
            return 0
        return GrammarPracticeAttempt.objects.filter(user=self.user).count()

    def get_average_practice_score(self, obj):
        if not self.user:
            return 0
        attempts = GrammarPracticeAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        return attempts.aggregate(
            avg=models.Avg('score_percent')
        )['avg'] or 0

    def get_total_test_attempts(self, obj):
        if not self.user:
            return 0
        return GrammarTestAttempt.objects.filter(user=self.user).count()

    def get_average_test_score(self, obj):
        if not self.user:
            return 0
        attempts = GrammarTestAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        return attempts.aggregate(
            avg=models.Avg('score_percent')
        )['avg'] or 0

    def get_total_time_spent(self, obj):
        if not self.user:
            return 0
        total_seconds = 0
        total_seconds += GrammarPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += GrammarTestAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        return total_seconds // 60

    def get_last_activity(self, obj):
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

    total_focuses           = serializers.SerializerMethodField()
    mastered_focuses        = serializers.SerializerMethodField()
    in_progress_focuses     = serializers.SerializerMethodField()
    not_started_focuses     = serializers.SerializerMethodField()
    mastery_percentage      = serializers.SerializerMethodField()
    total_practice_attempts = serializers.SerializerMethodField()
    average_practice_score  = serializers.SerializerMethodField()
    total_test_attempts     = serializers.SerializerMethodField()
    average_test_score      = serializers.SerializerMethodField()
    total_time_spent        = serializers.SerializerMethodField()
    last_activity           = serializers.SerializerMethodField()
    needs_review_count      = serializers.SerializerMethodField()

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
            user=self.user, is_mastered=True
        ).values('focus').distinct().count()

    def get_in_progress_focuses(self, obj):
        if not self.user:
            return 0
        attempted = PunctuationTestAttempt.objects.filter(
            user=self.user
        ).values_list('focus_id', flat=True).distinct()
        mastered = PunctuationTestAttempt.objects.filter(
            user=self.user, is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        return len(set(attempted) - set(mastered))

    def get_not_started_focuses(self, obj):
        return (
            self.get_total_focuses(obj)
            - self.get_mastered_focuses(obj)
            - self.get_in_progress_focuses(obj)
        )

    def get_mastery_percentage(self, obj):
        total = self.get_total_focuses(obj)
        if total == 0:
            return 0
        return (self.get_mastered_focuses(obj) / total) * 100

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
        total_seconds += PunctuationPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += PunctuationTestAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
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

    total_items             = serializers.SerializerMethodField()
    mastered_count          = serializers.SerializerMethodField()
    learning_count          = serializers.SerializerMethodField()
    review_count            = serializers.SerializerMethodField()
    new_count               = serializers.SerializerMethodField()
    mastery_percentage      = serializers.SerializerMethodField()
    total_attempts          = serializers.SerializerMethodField()
    overall_accuracy        = serializers.SerializerMethodField()
    total_time_spent        = serializers.SerializerMethodField()
    last_activity           = serializers.SerializerMethodField()
    needs_review_count      = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def get_total_items(self, obj):
        return VocabularyItem.objects.count()

    def get_mastered_count(self, obj):
        if not self.user:
            return 0
        return StudentVocabMastery.objects.filter(
            user=self.user, mastery_level='mastered'
        ).count()

    def get_learning_count(self, obj):
        if not self.user:
            return 0
        return StudentVocabMastery.objects.filter(
            user=self.user, mastery_level='learning'
        ).count()

    def get_review_count(self, obj):
        if not self.user:
            return 0
        return StudentVocabMastery.objects.filter(
            user=self.user, mastery_level='review'
        ).count()

    def get_new_count(self, obj):
        if not self.user:
            return self.get_total_items(obj)
        started = StudentVocabMastery.objects.filter(
            user=self.user
        ).values_list('vocab_item_id', flat=True)
        return self.get_total_items(obj) - started.count()

    def get_mastery_percentage(self, obj):
        total = self.get_total_items(obj)
        if total == 0:
            return 0
        return (self.get_mastered_count(obj) / total) * 100

    def get_total_attempts(self, obj):
        if not self.user:
            return 0
        return VocabularyAttempt.objects.filter(user=self.user).count()

    def get_overall_accuracy(self, obj):
        if not self.user:
            return 0
        attempts = VocabularyAttempt.objects.filter(user=self.user)
        if not attempts.exists():
            return 0
        correct = attempts.filter(is_correct=True).count()
        return (correct / attempts.count()) * 100

    def get_total_time_spent(self, obj):
        if not self.user:
            return 0
        total_seconds = VocabularyAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        return total_seconds // 60

    def get_last_activity(self, obj):
        if not self.user:
            return None
        return VocabularyAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()

    def get_needs_review_count(self, obj):
        if not self.user:
            return 0
        review_items = StudentVocabMastery.objects.filter(
            user=self.user, mastery_level='review'
        ).count()
        low_accuracy = StudentVocabMastery.objects.filter(
            user=self.user,
            mastery_level='learning',
            correct_attempts__lt=models.F('total_attempts') * 0.7
        ).count()
        return review_items + low_accuracy


class ComprehensionProgressSerializer(serializers.Serializer):
    """Comprehension domain progress summary (Bloom's levels)"""

    total_focuses           = serializers.SerializerMethodField()
    mastered_focuses        = serializers.SerializerMethodField()
    in_progress_focuses     = serializers.SerializerMethodField()
    not_started_focuses     = serializers.SerializerMethodField()
    mastery_percentage      = serializers.SerializerMethodField()
    by_bloom_level          = serializers.SerializerMethodField()
    total_practice_attempts = serializers.SerializerMethodField()
    average_practice_score  = serializers.SerializerMethodField()
    total_test_attempts     = serializers.SerializerMethodField()
    average_test_score      = serializers.SerializerMethodField()
    total_time_spent        = serializers.SerializerMethodField()
    last_activity           = serializers.SerializerMethodField()
    needs_review_count      = serializers.SerializerMethodField()

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
            user=self.user, is_mastered=True
        ).values('focus').distinct().count()

    def get_in_progress_focuses(self, obj):
        if not self.user:
            return 0
        attempted = ComprehensionTestAttempt.objects.filter(
            user=self.user
        ).values_list('focus_id', flat=True).distinct()
        mastered = ComprehensionTestAttempt.objects.filter(
            user=self.user, is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        return len(set(attempted) - set(mastered))

    def get_not_started_focuses(self, obj):
        return (
            self.get_total_focuses(obj)
            - self.get_mastered_focuses(obj)
            - self.get_in_progress_focuses(obj)
        )

    def get_mastery_percentage(self, obj):
        total = self.get_total_focuses(obj)
        if total == 0:
            return 0
        return (self.get_mastered_focuses(obj) / total) * 100

    def get_by_bloom_level(self, obj):
        if not self.user:
            return {}
        from content.models.comprehension import BloomLevel
        result = {}
        for level in BloomLevel.values:
            total = ChunkComprehensionFocus.objects.filter(
                level=level
            ).count()
            mastered = ComprehensionTestAttempt.objects.filter(
                user=self.user,
                focus__level=level,
                is_mastered=True
            ).values('focus').distinct().count()
            result[level] = {
                'total':      total,
                'mastered':   mastered,
                'percentage': (mastered / total * 100) if total > 0 else 0,
            }
        return result

    def get_total_practice_attempts(self, obj):
        if not self.user:
            return 0
        return ComprehensionPracticeAttempt.objects.filter(
            user=self.user
        ).count()

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
        total_seconds += ComprehensionPracticeAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += ComprehensionTestAttempt.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
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
    """
    Writing domain progress summary.
    Rebuilt for the new three-tier architecture.
    Tracks: stages mastered per tier, attempts per phase,
    time spent, last activity, pending teacher review.
    """

    # Stage mastery — overall
    total_stages        = serializers.SerializerMethodField()
    mastered_stages     = serializers.SerializerMethodField()
    mastery_percentage  = serializers.SerializerMethodField()

    # Stage mastery — by tier
    by_tier             = serializers.SerializerMethodField()

    # Attempt stats
    total_attempts          = serializers.SerializerMethodField()
    dissect_attempts        = serializers.SerializerMethodField()
    imitate_attempts        = serializers.SerializerMethodField()
    produce_attempts        = serializers.SerializerMethodField()
    pending_teacher_review  = serializers.SerializerMethodField()

    # Time spent
    total_time_spent    = serializers.SerializerMethodField()

    # Activity
    last_activity       = serializers.SerializerMethodField()
    needs_review_count  = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def _get_academic_year(self):
        return WritingAcademicYear.get_current()

    def get_total_stages(self, obj):
        """Total stage content records available to this student."""
        return WritingStageContent.objects.filter(
            is_complete=True
        ).count()

    def get_mastered_stages(self, obj):
        """Stages mastered by this student in the current academic year."""
        if not self.user:
            return 0
        year = self._get_academic_year()
        if not year:
            return 0
        return WritingStageMastery.objects.filter(
            user=self.user,
            academic_year=year,
        ).count()

    def get_mastery_percentage(self, obj):
        total = self.get_total_stages(obj)
        if total == 0:
            return 0
        return (self.get_mastered_stages(obj) / total) * 100

    def get_by_tier(self, obj):
        """Mastery breakdown by tier — sentence, paragraph, genre."""
        if not self.user:
            return {}
        year = self._get_academic_year()
        result = {}
        for tier in (TIER_SENTENCE, TIER_PARAGRAPH, TIER_GENRE):
            total = WritingStageContent.objects.filter(
                stage__tier=tier,
                is_complete=True,
            ).count()
            mastered = 0
            if year:
                mastered = WritingStageMastery.objects.filter(
                    user=self.user,
                    academic_year=year,
                    content__stage__tier=tier,
                ).count()
            result[tier] = {
                'total':      total,
                'mastered':   mastered,
                'percentage': (mastered / total * 100) if total > 0 else 0,
            }
        return result

    def get_total_attempts(self, obj):
        if not self.user:
            return 0
        return WritingAttempt.objects.filter(user=self.user).count()

    def get_dissect_attempts(self, obj):
        if not self.user:
            return 0
        return WritingAttempt.objects.filter(
            user=self.user, phase=PHASE_DISSECT
        ).count()

    def get_imitate_attempts(self, obj):
        if not self.user:
            return 0
        return WritingAttempt.objects.filter(
            user=self.user, phase=PHASE_IMITATE
        ).count()

    def get_produce_attempts(self, obj):
        if not self.user:
            return 0
        return WritingAttempt.objects.filter(
            user=self.user, phase=PHASE_PRODUCE
        ).count()

    def get_pending_teacher_review(self, obj):
        """Produce submissions waiting for teacher review."""
        if not self.user:
            return 0
        from content.models.writing import STATUS_PENDING
        return WritingAttempt.objects.filter(
            user=self.user,
            phase=PHASE_PRODUCE,
            status=STATUS_PENDING,
        ).count()

    def get_total_time_spent(self, obj):
        """Total minutes spent on writing."""
        if not self.user:
            return 0
        total_seconds = WritingAttempt.objects.filter(
            user=self.user
        ).aggregate(
            total=models.Sum('time_spent_seconds')
        )['total'] or 0
        return total_seconds // 60

    def get_last_activity(self, obj):
        if not self.user:
            return None
        return WritingAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()

    def get_needs_review_count(self, obj):
        """
        Produce attempts that failed in the last 7 days
        and are in cooldown — student needs to revisit.
        """
        if not self.user:
            return 0
        from content.models.writing import STATUS_FAILED, STATUS_COOLDOWN
        return WritingAttempt.objects.filter(
            user=self.user,
            phase=PHASE_PRODUCE,
            status__in=(STATUS_FAILED, STATUS_COOLDOWN),
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).values('content').distinct().count()


class PronunciationProgressSerializer(serializers.Serializer):
    """Pronunciation domain progress summary"""

    total_focuses       = serializers.SerializerMethodField()
    mastered_focuses    = serializers.SerializerMethodField()
    in_progress_focuses = serializers.SerializerMethodField()
    not_started_focuses = serializers.SerializerMethodField()
    mastery_percentage  = serializers.SerializerMethodField()
    total_attempts      = serializers.SerializerMethodField()
    average_score       = serializers.SerializerMethodField()
    best_score          = serializers.SerializerMethodField()
    total_time_spent    = serializers.SerializerMethodField()
    last_activity       = serializers.SerializerMethodField()
    needs_review_count  = serializers.SerializerMethodField()

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
            user=self.user, is_mastered=True
        ).count()

    def get_in_progress_focuses(self, obj):
        if not self.user:
            return 0
        return PronunciationMastery.objects.filter(
            user=self.user, is_mastered=False, total_attempts__gt=0
        ).count()

    def get_not_started_focuses(self, obj):
        if not self.user:
            return self.get_total_focuses(obj)
        started = PronunciationMastery.objects.filter(
            user=self.user
        ).values_list('focus_id', flat=True)
        return self.get_total_focuses(obj) - len(started)

    def get_mastery_percentage(self, obj):
        total = self.get_total_focuses(obj)
        if total == 0:
            return 0
        return (self.get_mastered_focuses(obj) / total) * 100

    def get_total_attempts(self, obj):
        if not self.user:
            return 0
        return PronunciationAttempt.objects.filter(user=self.user).count()

    def get_average_score(self, obj):
        if not self.user:
            return 0
        attempts = PronunciationAttempt.objects.filter(
            user=self.user, ai_score__isnull=False
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
        return 0

    def get_last_activity(self, obj):
        if not self.user:
            return None
        return PronunciationAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at').values_list('created_at', flat=True).first()

    def get_needs_review_count(self, obj):
        if not self.user:
            return 0
        return PronunciationMastery.objects.filter(
            user=self.user,
            is_mastered=False,
            last_attempted__lt=timezone.now() - timezone.timedelta(days=7)
        ).count()


class UnitTestProgressSerializer(serializers.Serializer):
    """Unit test progress summary"""

    total_units         = serializers.SerializerMethodField()
    units_passed        = serializers.SerializerMethodField()
    units_failed        = serializers.SerializerMethodField()
    units_not_attempted = serializers.SerializerMethodField()
    pass_percentage     = serializers.SerializerMethodField()
    total_test_sessions = serializers.SerializerMethodField()
    average_score       = serializers.SerializerMethodField()
    unit_breakdown      = serializers.SerializerMethodField()
    last_activity       = serializers.SerializerMethodField()

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
        return UnitTestSession.objects.filter(
            user=self.user, passed=True
        ).values_list('unit_id', flat=True).distinct().count()

    def get_units_failed(self, obj):
        if not self.user:
            return 0
        attempted = set(UnitTestSession.objects.filter(
            user=self.user
        ).values_list('unit_id', flat=True).distinct())
        passed = set(UnitTestSession.objects.filter(
            user=self.user, passed=True
        ).values_list('unit_id', flat=True).distinct())
        return len(attempted - passed)

    def get_units_not_attempted(self, obj):
        attempted = (
            UnitTestSession.objects.filter(
                user=self.user
            ).values_list('unit_id', flat=True).distinct().count()
            if self.user else 0
        )
        return self.get_total_units(obj) - attempted

    def get_pass_percentage(self, obj):
        total = self.get_total_units(obj)
        if total == 0:
            return 0
        return (self.get_units_passed(obj) / total) * 100

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
        return sessions.aggregate(
            avg=models.Avg('score_percentage')
        )['avg'] or 0

    def get_unit_breakdown(self, obj):
        if not self.user:
            return []
        result = []
        for unit in Unit.objects.all().order_by('number'):
            sessions = UnitTestSession.objects.filter(
                user=self.user, unit=unit
            ).order_by('-attempt_number')
            if sessions.exists():
                best   = sessions.order_by('-score_percentage').first()
                latest = sessions.first()
                result.append({
                    'unit_id':       unit.id,
                    'unit_title':    unit.title,
                    'unit_number':   unit.number,
                    'attempts':      sessions.count(),
                    'best_score':    best.score_percentage,
                    'latest_score':  latest.score_percentage,
                    'passed':        any(s.passed for s in sessions),
                    'last_attempted': latest.started_at,
                })
            else:
                result.append({
                    'unit_id':       unit.id,
                    'unit_title':    unit.title,
                    'unit_number':   unit.number,
                    'attempts':      0,
                    'best_score':    None,
                    'latest_score':  None,
                    'passed':        False,
                    'last_attempted': None,
                })
        return result

    def get_last_activity(self, obj):
        if not self.user:
            return None
        return UnitTestSession.objects.filter(
            user=self.user
        ).order_by('-started_at').values_list('started_at', flat=True).first()


# ============================================================
# MOBILE-OPTIMIZED SERIALIZERS
# ============================================================

class DomainProgressMobileSerializer(serializers.Serializer):
    """Minimal domain progress for mobile dashboard"""
    mastery_percentage = serializers.FloatField()
    needs_review_count = serializers.IntegerField()
    last_activity      = serializers.DateTimeField(allow_null=True)


class DashboardMobileSerializer(serializers.Serializer):
    """Main mobile dashboard - ultra lightweight"""

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
# OVERALL PROGRESS SERIALIZER
# ============================================================

class OverallProgressSerializer(serializers.Serializer):
    """
    Complete student progress dashboard aggregating all domains.
    """

    student_id   = serializers.IntegerField(read_only=True)
    student_name = serializers.CharField(read_only=True)

    grammar       = GrammarProgressSerializer(read_only=True)
    punctuation   = PunctuationProgressSerializer(read_only=True)
    vocabulary    = VocabularyProgressSerializer(read_only=True)
    comprehension = ComprehensionProgressSerializer(read_only=True)
    writing       = WritingProgressSerializer(read_only=True)
    pronunciation = PronunciationProgressSerializer(read_only=True)
    unit_tests    = UnitTestProgressSerializer(read_only=True)

    overall_mastery        = serializers.SerializerMethodField()
    total_practices        = serializers.SerializerMethodField()
    total_time_spent_hours = serializers.SerializerMethodField()
    streak_days            = serializers.SerializerMethodField()
    recent_activity        = serializers.SerializerMethodField()
    recommended_focus      = serializers.SerializerMethodField()
    upcoming_tests         = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

    def get_overall_mastery(self, obj):
        if not self.user:
            return 0
        percentages = [
            GrammarProgressSerializer(user=self.user).data.get(
                'mastery_percentage', 0
            ),
            PunctuationProgressSerializer(user=self.user).data.get(
                'mastery_percentage', 0
            ),
            VocabularyProgressSerializer(user=self.user).data.get(
                'mastery_percentage', 0
            ),
            ComprehensionProgressSerializer(user=self.user).data.get(
                'mastery_percentage', 0
            ),
            WritingProgressSerializer(user=self.user).data.get(
                'mastery_percentage', 0
            ),
            PronunciationProgressSerializer(user=self.user).data.get(
                'mastery_percentage', 0
            ),
        ]
        valid = [p for p in percentages if p > 0]
        return sum(valid) / len(valid) if valid else 0

    def get_total_practices(self, obj):
        if not self.user:
            return 0
        total = 0
        total += GrammarPracticeAttempt.objects.filter(user=self.user).count()
        total += PunctuationPracticeAttempt.objects.filter(user=self.user).count()
        total += VocabularyAttempt.objects.filter(user=self.user).count()
        total += ComprehensionPracticeAttempt.objects.filter(user=self.user).count()
        total += WritingAttempt.objects.filter(user=self.user).count()
        total += PronunciationAttempt.objects.filter(user=self.user).count()
        return total

    def get_total_time_spent_hours(self, obj):
        if not self.user:
            return 0
        total_minutes = 0
        total_minutes += (
            GrammarPracticeAttempt.objects.filter(user=self.user).aggregate(
                total=models.Sum('time_taken_seconds')
            )['total'] or 0
        ) // 60
        total_minutes += (
            PunctuationPracticeAttempt.objects.filter(user=self.user).aggregate(
                total=models.Sum('time_taken_seconds')
            )['total'] or 0
        ) // 60
        total_minutes += (
            VocabularyAttempt.objects.filter(user=self.user).aggregate(
                total=models.Sum('time_taken_seconds')
            )['total'] or 0
        ) // 60
        total_minutes += (
            ComprehensionPracticeAttempt.objects.filter(user=self.user).aggregate(
                total=models.Sum('time_taken_seconds')
            )['total'] or 0
        ) // 60
        total_minutes += (
            WritingAttempt.objects.filter(user=self.user).aggregate(
                total=models.Sum('time_spent_seconds')
            )['total'] or 0
        ) // 60
        return total_minutes / 60

    def get_streak_days(self, obj):
        if not self.user:
            return 0
        from django.db.models.functions import TruncDate
        activity_dates = set()
        for qs, field in [
            (GrammarPracticeAttempt.objects.filter(user=self.user), 'attempted_at'),
            (PunctuationPracticeAttempt.objects.filter(user=self.user), 'created_at'),
            (VocabularyAttempt.objects.filter(user=self.user), 'created_at'),
            (ComprehensionPracticeAttempt.objects.filter(user=self.user), 'attempted_at'),
            (WritingAttempt.objects.filter(user=self.user), 'created_at'),
            (PronunciationAttempt.objects.filter(user=self.user), 'created_at'),
            (UnitTestSession.objects.filter(user=self.user), 'started_at'),
        ]:
            dates = qs.annotate(
                date=TruncDate(field)
            ).values_list('date', flat=True)
            activity_dates.update(dates)
        if not activity_dates:
            return 0
        sorted_dates = sorted(activity_dates, reverse=True)
        today        = timezone.now().date()
        streak       = 0
        current_date = today
        while current_date in sorted_dates:
            streak       += 1
            current_date -= timezone.timedelta(days=1)
        return streak

    def get_recent_activity(self, obj):
        if not self.user:
            return []
        activities = []
        for attempt in GrammarPracticeAttempt.objects.filter(
            user=self.user
        ).order_by('-attempted_at')[:3]:
            activities.append({
                'type':        'grammar_practice',
                'domain':      'grammar',
                'score':       attempt.score_percent,
                'passed':      attempt.is_passed,
                'timestamp':   attempt.attempted_at,
                'description': f"Grammar practice: {attempt.score_percent}%",
            })
        for attempt in GrammarTestAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at')[:3]:
            activities.append({
                'type':        'grammar_test',
                'domain':      'grammar',
                'score':       attempt.score_percent,
                'mastered':    attempt.is_mastered,
                'timestamp':   attempt.created_at,
                'description': f"Grammar test: {attempt.score_percent}%",
            })
        for attempt in VocabularyAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at')[:3]:
            activities.append({
                'type':        'vocabulary',
                'domain':      'vocabulary',
                'correct':     attempt.is_correct,
                'timestamp':   attempt.created_at,
                'description': (
                    f"Vocabulary: "
                    f"{'correct' if attempt.is_correct else 'incorrect'}"
                ),
            })
        for attempt in WritingAttempt.objects.filter(
            user=self.user
        ).order_by('-created_at')[:3]:
            activities.append({
                'type':        'writing',
                'domain':      'writing',
                'phase':       attempt.phase,
                'status':      attempt.status,
                'timestamp':   attempt.created_at,
                'description': (
                    f"Writing {attempt.get_phase_display()}: "
                    f"{attempt.get_status_display()}"
                ),
            })
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:10]

    def get_recommended_focus(self, obj):
        if not self.user:
            return []
        recommendations = []
        grammar_failures = GrammarTestAttempt.objects.filter(
            user=self.user, is_mastered=False
        ).order_by('-created_at').values_list(
            'focus_id', flat=True
        ).distinct()[:3]
        for focus_id in grammar_failures:
            try:
                focus = ChunkGrammarFocus.objects.get(id=focus_id)
                recommendations.append({
                    'domain':   'grammar',
                    'type':     'focus',
                    'id':       focus_id,
                    'title':    focus.focus_title,
                    'reason':   'Needs review (test failed)',
                    'priority': 'high',
                })
            except ChunkGrammarFocus.DoesNotExist:
                pass
        vocab_review = StudentVocabMastery.objects.filter(
            user=self.user, mastery_level='review'
        ).select_related('vocab_item')[:3]
        for mastery in vocab_review:
            recommendations.append({
                'domain':   'vocabulary',
                'type':     'item',
                'id':       mastery.vocab_item_id,
                'title':    mastery.vocab_item.word,
                'reason':   'Needs review (low retention)',
                'priority': 'medium',
            })
        return recommendations[:5]

    def get_upcoming_tests(self, obj):
        if not self.user:
            return []
        upcoming = []
        for unit in Unit.objects.all().order_by('number'):
            sessions = UnitTestSession.objects.filter(
                user=self.user, unit=unit
            )
            if not sessions.exists():
                upcoming.append({
                    'unit_id':           unit.id,
                    'unit_title':        unit.title,
                    'unit_number':       unit.number,
                    'status':            'available',
                    'attempts_remaining': 3,
                    'reason':            'Not started',
                })
            else:
                latest = sessions.order_by('-attempt_number').first()
                if not latest.passed and sessions.count() < 3:
                    upcoming.append({
                        'unit_id':           unit.id,
                        'unit_title':        unit.title,
                        'unit_number':       unit.number,
                        'status':            'retake_available',
                        'attempts_remaining': 3 - sessions.count(),
                        'last_score':        latest.score_percentage,
                        'reason': (
                            f'Retry available '
                            f'({3 - sessions.count()} attempts left)'
                        ),
                    })
        return upcoming[:5]


# ============================================================
# UNIT & LESSON PROGRESS SERIALIZERS
# ============================================================

class UnitProgressDetailSerializer(serializers.Serializer):
    """Detailed progress for a specific unit"""

    unit_id              = serializers.IntegerField()
    unit_title           = serializers.CharField()
    unit_number          = serializers.IntegerField()
    total_lessons        = serializers.SerializerMethodField()
    lessons_completed    = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    test_attempts        = serializers.SerializerMethodField()
    best_test_score      = serializers.SerializerMethodField()
    latest_test_score    = serializers.SerializerMethodField()
    test_passed          = serializers.SerializerMethodField()
    time_spent_minutes   = serializers.SerializerMethodField()
    domain_mastery       = serializers.SerializerMethodField()
    last_activity        = serializers.SerializerMethodField()

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
        return (self.get_lessons_completed(obj) / total) * 100

    def get_test_attempts(self, obj):
        if not self.user or not self.unit:
            return 0
        return UnitTestSession.objects.filter(
            user=self.user, unit=self.unit
        ).count()

    def get_best_test_score(self, obj):
        if not self.user or not self.unit:
            return None
        best = UnitTestSession.objects.filter(
            user=self.user, unit=self.unit
        ).order_by('-score_percentage').first()
        return best.score_percentage if best else None

    def get_latest_test_score(self, obj):
        if not self.user or not self.unit:
            return None
        latest = UnitTestSession.objects.filter(
            user=self.user, unit=self.unit
        ).order_by('-started_at').first()
        return latest.score_percentage if latest else None

    def get_test_passed(self, obj):
        if not self.user or not self.unit:
            return False
        return UnitTestSession.objects.filter(
            user=self.user, unit=self.unit, passed=True
        ).exists()

    def get_time_spent_minutes(self, obj):
        if not self.user or not self.unit:
            return 0
        chunks        = LessonChunk.objects.filter(lesson__unit=self.unit)
        total_seconds = 0
        total_seconds += UnitTestSession.objects.filter(
            user=self.user,
            unit=self.unit,
            completed_at__isnull=False,
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += GrammarPracticeAttempt.objects.filter(
            user=self.user, focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += PunctuationPracticeAttempt.objects.filter(
            user=self.user, focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += VocabularyAttempt.objects.filter(
            user=self.user, vocab_item__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += ComprehensionPracticeAttempt.objects.filter(
            user=self.user, focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        # Writing time — scoped to unit via WritingStageContent
        total_seconds += WritingAttempt.objects.filter(
            user=self.user, content__unit=self.unit
        ).aggregate(total=models.Sum('time_spent_seconds'))['total'] or 0
        return total_seconds // 60

    def get_domain_mastery(self, obj):
        """Mastery percentages for each domain within this unit."""
        if not self.user or not self.unit:
            return {}
        chunks = LessonChunk.objects.filter(lesson__unit=self.unit)
        result = {}

        # Grammar
        grammar_focuses = ChunkGrammarFocus.objects.filter(chunk__in=chunks)
        if grammar_focuses.exists():
            mastered = sum(
                1 for f in grammar_focuses
                if GrammarTestAttempt.objects.filter(
                    user=self.user, focus=f, is_mastered=True
                ).exists()
            )
            result['grammar'] = (mastered / grammar_focuses.count()) * 100

        # Punctuation
        punct_focuses = ChunkPunctuationFocus.objects.filter(chunk__in=chunks)
        if punct_focuses.exists():
            mastered = sum(
                1 for f in punct_focuses
                if PunctuationTestAttempt.objects.filter(
                    user=self.user, focus=f, is_mastered=True
                ).exists()
            )
            result['punctuation'] = (mastered / punct_focuses.count()) * 100

        # Vocabulary
        vocab_items = VocabularyItem.objects.filter(chunk__in=chunks)
        if vocab_items.exists():
            mastered = StudentVocabMastery.objects.filter(
                user=self.user,
                vocab_item__in=vocab_items,
                mastery_level='mastered',
            ).count()
            result['vocabulary'] = (mastered / vocab_items.count()) * 100

        # Comprehension
        comp_focuses = ChunkComprehensionFocus.objects.filter(chunk__in=chunks)
        if comp_focuses.exists():
            mastered = sum(
                1 for f in comp_focuses
                if ComprehensionTestAttempt.objects.filter(
                    user=self.user, focus=f, is_mastered=True
                ).exists()
            )
            result['comprehension'] = (mastered / comp_focuses.count()) * 100

        # Writing — new architecture
        year = WritingAcademicYear.get_current()
        writing_contents = WritingStageContent.objects.filter(
            unit=self.unit, is_complete=True
        )
        if writing_contents.exists() and year:
            mastered = WritingStageMastery.objects.filter(
                user=self.user,
                content__in=writing_contents,
                academic_year=year,
            ).count()
            result['writing'] = (mastered / writing_contents.count()) * 100

        # Pronunciation
        pron_focuses = PronunciationFocus.objects.filter(chunk__in=chunks)
        if pron_focuses.exists():
            mastered = PronunciationMastery.objects.filter(
                user=self.user,
                focus__in=pron_focuses,
                is_mastered=True,
            ).count()
            result['pronunciation'] = (mastered / pron_focuses.count()) * 100

        return result

    def get_last_activity(self, obj):
        if not self.user or not self.unit:
            return None
        chunks     = LessonChunk.objects.filter(lesson__unit=self.unit)
        timestamps = []
        for qs, field in [
            (GrammarPracticeAttempt.objects.filter(
                user=self.user, focus__chunk__in=chunks
            ), 'attempted_at'),
            (PunctuationPracticeAttempt.objects.filter(
                user=self.user, focus__chunk__in=chunks
            ), 'created_at'),
            (VocabularyAttempt.objects.filter(
                user=self.user, vocab_item__chunk__in=chunks
            ), 'created_at'),
            (ComprehensionPracticeAttempt.objects.filter(
                user=self.user, focus__chunk__in=chunks
            ), 'attempted_at'),
            (WritingAttempt.objects.filter(
                user=self.user, content__unit=self.unit
            ), 'created_at'),
            (PronunciationAttempt.objects.filter(
                user=self.user, focus__chunk__in=chunks
            ), 'created_at'),
            (UnitTestSession.objects.filter(
                user=self.user, unit=self.unit
            ), 'started_at'),
        ]:
            ts = qs.order_by(f'-{field}').values_list(field, flat=True).first()
            if ts:
                timestamps.append(ts)
        return max(timestamps) if timestamps else None


class LessonProgressSerializer(serializers.Serializer):
    """Progress for a specific lesson"""

    lesson_id             = serializers.IntegerField()
    lesson_title          = serializers.CharField()
    lesson_number         = serializers.IntegerField()
    total_chunks          = serializers.SerializerMethodField()
    chunks_completed      = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    chunk_mastery         = serializers.SerializerMethodField()
    time_spent_minutes    = serializers.SerializerMethodField()
    last_activity         = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user   = kwargs.pop('user', None)
        self.lesson = kwargs.pop('lesson', None)
        super().__init__(*args, **kwargs)

    def get_total_chunks(self, obj):
        if not self.lesson:
            return 0
        return self.lesson.chunks.count()

    def get_chunks_completed(self, obj):
        if not self.user or not self.lesson:
            return 0
        return sum(
            1 for chunk in self.lesson.chunks.all()
            if chunk.is_mastered_by(self.user)
        )

    def get_completion_percentage(self, obj):
        total = self.get_total_chunks(obj)
        if total == 0:
            return 0
        return (self.get_chunks_completed(obj) / total) * 100

    def get_chunk_mastery(self, obj):
        if not self.user or not self.lesson:
            return []
        result = []
        for chunk in self.lesson.chunks.all().order_by('order'):
            status = chunk.get_mastery_status(self.user)
            result.append({
                'chunk_id':    chunk.id,
                'order':       chunk.order,
                'mastered':    status['overall'] if status else False,
                'by_domain':   status['by_domain'] if status else {},
                'next_domain': status['next_domain_to_work'] if status else None,
            })
        return result

    def get_time_spent_minutes(self, obj):
        if not self.user or not self.lesson:
            return 0
        chunks        = self.lesson.chunks.all()
        total_seconds = 0
        total_seconds += GrammarPracticeAttempt.objects.filter(
            user=self.user, focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += PunctuationPracticeAttempt.objects.filter(
            user=self.user, focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += VocabularyAttempt.objects.filter(
            user=self.user, vocab_item__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += ComprehensionPracticeAttempt.objects.filter(
            user=self.user, focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        total_seconds += PronunciationAttempt.objects.filter(
            user=self.user, focus__chunk__in=chunks
        ).aggregate(total=models.Sum('time_taken_seconds'))['total'] or 0
        # Writing is unit-level, not lesson-level — not included here
        return total_seconds // 60

    def get_last_activity(self, obj):
        if not self.user or not self.lesson:
            return None
        chunks     = self.lesson.chunks.all()
        timestamps = []
        for qs, field in [
            (GrammarPracticeAttempt.objects.filter(
                user=self.user, focus__chunk__in=chunks
            ), 'attempted_at'),
            (PunctuationPracticeAttempt.objects.filter(
                user=self.user, focus__chunk__in=chunks
            ), 'created_at'),
            (VocabularyAttempt.objects.filter(
                user=self.user, vocab_item__chunk__in=chunks
            ), 'created_at'),
            (ComprehensionPracticeAttempt.objects.filter(
                user=self.user, focus__chunk__in=chunks
            ), 'attempted_at'),
            (PronunciationAttempt.objects.filter(
                user=self.user, focus__chunk__in=chunks
            ), 'created_at'),
        ]:
            ts = qs.order_by(f'-{field}').values_list(field, flat=True).first()
            if ts:
                timestamps.append(ts)
        return max(timestamps) if timestamps else None


# ============================================================
# EXPORTS
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