# content/api_views/progress.py

"""
Progress tracking views for comprehensive student dashboards.
Aggregates data from all domains to provide unified progress reporting.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import models, transaction
from django.db.models import Q, Prefetch, Count, Avg, Max, Sum, F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from datetime import timedelta

from content.models.core import Textbook, Unit, Lesson, LessonChunk
from content.models.grammar import (
    GrammarPracticeAttempt, GrammarTestAttempt,
    ChunkGrammarFocus
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
    ChunkComprehensionFocus, BloomLevel
)

# Writing — new three-tier architecture
from content.models.writing import (
    WritingAttempt,
    WritingStageMastery,
    WritingStageContent,
    WritingAcademicYear,
    PHASE_PRODUCE,
    STATUS_FAILED,
    STATUS_COOLDOWN,
)

from content.models.pronunciation import (
    PronunciationAttempt, PronunciationMastery, PronunciationFocus
)
from content.models.testing import (
    UnitTestSession, UnitTestAnswer
)
from django.contrib.auth import get_user_model

from content.serializers.progress import (
    GrammarProgressSerializer,
    PunctuationProgressSerializer,
    VocabularyProgressSerializer,
    ComprehensionProgressSerializer,
    WritingProgressSerializer,
    PronunciationProgressSerializer,
    UnitTestProgressSerializer,
    OverallProgressSerializer,
    DomainProgressMobileSerializer,
    DashboardMobileSerializer,
    UnitProgressDetailSerializer,
    LessonProgressSerializer,
)
from .base import BaseViewSet, ProgressViewSet, log_user_activity
from .testing import UnitTestSessionListSerializer

User = get_user_model()


# ============================================================
# HELPERS
# ============================================================

def _get_current_writing_year():
    """Return the current WritingAcademicYear or None."""
    return WritingAcademicYear.get_current()


# ============================================================
# DASHBOARD VIEWS
# ============================================================

class DashboardViewSet(viewsets.GenericViewSet):
    """
    Main dashboard view aggregating all progress data.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.GET.get('mobile') == 'true':
            return DashboardMobileSerializer
        return OverallProgressSerializer

    @action(detail=False, methods=['get'])
    def overview(self, request):
        user = request.user

        grammar       = GrammarProgressSerializer(user=user).data
        punctuation   = PunctuationProgressSerializer(user=user).data
        vocabulary    = VocabularyProgressSerializer(user=user).data
        comprehension = ComprehensionProgressSerializer(user=user).data
        writing       = WritingProgressSerializer(user=user).data
        pronunciation = PronunciationProgressSerializer(user=user).data
        unit_tests    = UnitTestProgressSerializer(user=user).data

        overall_mastery  = self._calculate_overall_mastery(user)
        recent_activity  = self._get_recent_activity(user)
        recommendations  = self._get_recommendations(user)
        upcoming_tests   = self._get_upcoming_tests(user)
        unit_progress    = self._get_unit_progress(user)
        streak_days      = self._calculate_streak(user)
        total_time_hours = self._calculate_total_time(user)

        if request.GET.get('mobile') == 'true':
            data = {
                'streak_days':     streak_days,
                'overall_mastery': overall_mastery,
                'grammar': {
                    'mastery_percentage': grammar.get('mastery_percentage', 0),
                    'needs_review_count': grammar.get('needs_review_count', 0),
                    'last_activity':      grammar.get('last_activity'),
                },
                'punctuation': {
                    'mastery_percentage': punctuation.get('mastery_percentage', 0),
                    'needs_review_count': punctuation.get('needs_review_count', 0),
                    'last_activity':      punctuation.get('last_activity'),
                },
                'vocabulary': {
                    'mastery_percentage': vocabulary.get('mastery_percentage', 0),
                    'needs_review_count': vocabulary.get('needs_review_count', 0),
                    'last_activity':      vocabulary.get('last_activity'),
                },
                'comprehension': {
                    'mastery_percentage': comprehension.get('mastery_percentage', 0),
                    'needs_review_count': comprehension.get('needs_review_count', 0),
                    'last_activity':      comprehension.get('last_activity'),
                },
                'writing': {
                    'mastery_percentage': writing.get('mastery_percentage', 0),
                    'needs_review_count': writing.get('needs_review_count', 0),
                    'last_activity':      writing.get('last_activity'),
                },
                'pronunciation': {
                    'mastery_percentage': pronunciation.get('mastery_percentage', 0),
                    'needs_review_count': pronunciation.get('needs_review_count', 0),
                    'last_activity':      pronunciation.get('last_activity'),
                },
                'recent_activity': recent_activity[:5],
                'next_steps':      recommendations[:3],
                'in_progress':     self._get_in_progress_items(user)[:3],
            }
        else:
            data = {
                'student_id':            user.id,
                'student_name':          user.get_full_name() or user.username,
                'overall_mastery':       overall_mastery,
                'total_practices':       self._calculate_total_practices(user),
                'total_time_spent_hours': total_time_hours,
                'streak_days':           streak_days,
                'grammar':               grammar,
                'punctuation':           punctuation,
                'vocabulary':            vocabulary,
                'comprehension':         comprehension,
                'writing':               writing,
                'pronunciation':         pronunciation,
                'unit_tests':            unit_tests,
                'recent_activity':       recent_activity,
                'recommended_focus':     recommendations,
                'upcoming_tests':        upcoming_tests,
                'unit_progress':         unit_progress,
            }

        log_user_activity(
            user, 'view_dashboard',
            {'mobile': request.GET.get('mobile') == 'true'}
        )
        return Response(data)

    def _calculate_overall_mastery(self, user):
        """Calculate overall mastery percentage across all domains."""
        # Grammar
        total_grammar    = ChunkGrammarFocus.objects.count()
        mastered_grammar = GrammarTestAttempt.objects.filter(
            user=user, is_mastered=True
        ).values('focus').distinct().count()

        # Punctuation
        total_punctuation    = ChunkPunctuationFocus.objects.count()
        mastered_punctuation = PunctuationTestAttempt.objects.filter(
            user=user, is_mastered=True
        ).values('focus').distinct().count()

        # Vocabulary
        total_vocab    = VocabularyItem.objects.count()
        mastered_vocab = StudentVocabMastery.objects.filter(
            user=user, mastery_level='mastered'
        ).count()

        # Comprehension
        total_comprehension    = ChunkComprehensionFocus.objects.count()
        mastered_comprehension = ComprehensionTestAttempt.objects.filter(
            user=user, is_mastered=True
        ).values('focus').distinct().count()

        # Writing — new architecture
        year = _get_current_writing_year()
        total_writing    = WritingStageContent.objects.filter(
            is_complete=True
        ).count()
        mastered_writing = (
            WritingStageMastery.objects.filter(
                user=user, academic_year=year
            ).count()
            if year else 0
        )

        # Pronunciation
        total_pronunciation    = PronunciationFocus.objects.count()
        mastered_pronunciation = PronunciationMastery.objects.filter(
            user=user, is_mastered=True
        ).count()

        def pct(mastered, total):
            return (mastered / total * 100) if total > 0 else 0

        percentages = [
            pct(mastered_grammar,       total_grammar),
            pct(mastered_punctuation,   total_punctuation),
            pct(mastered_vocab,         total_vocab),
            pct(mastered_comprehension, total_comprehension),
            pct(mastered_writing,       total_writing),
            pct(mastered_pronunciation, total_pronunciation),
        ]
        valid = [p for p in percentages if p > 0]
        return sum(valid) / len(valid) if valid else 0

    def _calculate_total_practices(self, user):
        total  = 0
        total += GrammarPracticeAttempt.objects.filter(user=user).count()
        total += PunctuationPracticeAttempt.objects.filter(user=user).count()
        total += VocabularyAttempt.objects.filter(user=user).count()
        total += ComprehensionPracticeAttempt.objects.filter(user=user).count()
        total += WritingAttempt.objects.filter(user=user).count()
        total += PronunciationAttempt.objects.filter(user=user).count()
        return total

    def _calculate_total_time(self, user):
        total_seconds  = 0
        total_seconds += GrammarPracticeAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += PunctuationPracticeAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += VocabularyAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += ComprehensionPracticeAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += WritingAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_spent_seconds'))['total'] or 0
        total_seconds += UnitTestSession.objects.filter(
            user=user, completed_at__isnull=False
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        return total_seconds / 3600

    def _calculate_streak(self, user):
        from django.db.models.functions import TruncDate
        activity_dates = set()

        for qs, field in [
            (GrammarPracticeAttempt.objects.filter(user=user),     'attempted_at'),
            (PunctuationPracticeAttempt.objects.filter(user=user), 'created_at'),
            (VocabularyAttempt.objects.filter(user=user),          'created_at'),
            (ComprehensionPracticeAttempt.objects.filter(user=user), 'attempted_at'),
            (WritingAttempt.objects.filter(user=user),             'created_at'),
            (PronunciationAttempt.objects.filter(user=user),       'created_at'),
            (UnitTestSession.objects.filter(user=user),            'started_at'),
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
            current_date -= timedelta(days=1)

        return streak

    def _get_recent_activity(self, user, limit=20):
        activities = []

        for attempt in GrammarPracticeAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-attempted_at')[:5]:
            activities.append({
                'id':          attempt.id,
                'type':        'grammar_practice',
                'domain':      'grammar',
                'title':       attempt.focus.focus_title if attempt.focus else 'Grammar Practice',
                'score':       attempt.score_percent,
                'passed':      attempt.is_passed,
                'timestamp':   attempt.attempted_at,
                'description': f"Grammar practice: {attempt.score_percent}%",
            })

        for attempt in GrammarTestAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-created_at')[:5]:
            activities.append({
                'id':          attempt.id,
                'type':        'grammar_test',
                'domain':      'grammar',
                'title':       attempt.focus.focus_title if attempt.focus else 'Grammar Test',
                'score':       attempt.score_percent,
                'mastered':    attempt.is_mastered,
                'timestamp':   attempt.created_at,
                'description': f"Grammar test: {attempt.score_percent}%",
            })

        for attempt in PunctuationPracticeAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-created_at')[:5]:
            activities.append({
                'id':          attempt.id,
                'type':        'punctuation_practice',
                'domain':      'punctuation',
                'title':       attempt.focus.focus_title if attempt.focus else 'Punctuation Practice',
                'score':       attempt.score_percent,
                'passed':      attempt.is_passed,
                'timestamp':   attempt.created_at,
                'description': f"Punctuation practice: {attempt.score_percent}%",
            })

        for attempt in PunctuationTestAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-created_at')[:5]:
            activities.append({
                'id':          attempt.id,
                'type':        'punctuation_test',
                'domain':      'punctuation',
                'title':       attempt.focus.focus_title if attempt.focus else 'Punctuation Test',
                'score':       attempt.score_percent,
                'mastered':    attempt.is_mastered,
                'timestamp':   attempt.created_at,
                'description': f"Punctuation test: {attempt.score_percent}%",
            })

        for attempt in VocabularyAttempt.objects.filter(
            user=user
        ).select_related('vocab_item').order_by('-created_at')[:5]:
            activities.append({
                'id':          attempt.id,
                'type':        'vocabulary',
                'domain':      'vocabulary',
                'title':       attempt.vocab_item.word if attempt.vocab_item else 'Vocabulary',
                'correct':     attempt.is_correct,
                'timestamp':   attempt.created_at,
                'description': (
                    f"Vocabulary: {attempt.vocab_item.word} - "
                    f"{'correct' if attempt.is_correct else 'incorrect'}"
                ),
            })

        for attempt in ComprehensionPracticeAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-attempted_at')[:5]:
            activities.append({
                'id':          attempt.id,
                'type':        'comprehension_practice',
                'domain':      'comprehension',
                'title':       attempt.focus.focus_title if attempt.focus else 'Comprehension Practice',
                'score':       attempt.score_percent,
                'passed':      attempt.is_passed,
                'timestamp':   attempt.attempted_at,
                'description': f"Comprehension practice: {attempt.score_percent}%",
            })

        for attempt in ComprehensionTestAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-created_at')[:5]:
            activities.append({
                'id':          attempt.id,
                'type':        'comprehension_test',
                'domain':      'comprehension',
                'title':       attempt.focus.focus_title if attempt.focus else 'Comprehension Test',
                'score':       attempt.score_percent,
                'mastered':    attempt.is_mastered,
                'timestamp':   attempt.created_at,
                'description': f"Comprehension test: {attempt.score_percent}%",
            })

        # Writing — new architecture
        for attempt in WritingAttempt.objects.filter(
            user=user
        ).select_related('content__stage').order_by('-created_at')[:5]:
            activities.append({
                'id':          attempt.id,
                'type':        'writing',
                'domain':      'writing',
                'title':       attempt.content.stage.name,
                'phase':       attempt.phase,
                'status':      attempt.status,
                'score':       attempt.effective_score(),
                'timestamp':   attempt.created_at,
                'description': (
                    f"Writing {attempt.get_phase_display()}: "
                    f"{attempt.get_status_display()}"
                ),
            })

        for attempt in PronunciationAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-created_at')[:5]:
            activities.append({
                'id':          attempt.id,
                'type':        'pronunciation',
                'domain':      'pronunciation',
                'title':       attempt.focus.focus_title if attempt.focus else 'Pronunciation',
                'score':       attempt.ai_score,
                'passed':      attempt.is_passed,
                'attempt_type': attempt.attempt_type,
                'timestamp':   attempt.created_at,
                'description': f"Pronunciation ({attempt.attempt_type}): {attempt.ai_score}%",
            })

        for session in UnitTestSession.objects.filter(
            user=user
        ).select_related('unit').order_by('-started_at')[:5]:
            activities.append({
                'id':             session.id,
                'type':           'unit_test',
                'domain':         'unit_test',
                'title':          f"Unit {session.unit.number}: {session.unit.title}",
                'score':          session.score_percentage,
                'passed':         session.passed,
                'attempt_number': session.attempt_number,
                'timestamp':      session.started_at,
                'description':    f"Unit test: {session.score_percentage:.1f}%",
            })

        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]

    def _get_recommendations(self, user, limit=5):
        recommendations = []

        # Grammar
        grammar_failures = GrammarTestAttempt.objects.filter(
            user=user, is_mastered=False
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

        # Punctuation
        punct_failures = PunctuationTestAttempt.objects.filter(
            user=user, is_mastered=False
        ).order_by('-created_at').values_list(
            'focus_id', flat=True
        ).distinct()[:3]
        for focus_id in punct_failures:
            try:
                focus = ChunkPunctuationFocus.objects.get(id=focus_id)
                recommendations.append({
                    'domain':   'punctuation',
                    'type':     'focus',
                    'id':       focus_id,
                    'title':    focus.focus_title,
                    'reason':   'Needs review (test failed)',
                    'priority': 'high',
                })
            except ChunkPunctuationFocus.DoesNotExist:
                pass

        # Vocabulary
        vocab_review = StudentVocabMastery.objects.filter(
            user=user, mastery_level='review'
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

        # Comprehension
        comp_failures = ComprehensionTestAttempt.objects.filter(
            user=user, is_mastered=False
        ).order_by('-created_at').values_list(
            'focus_id', flat=True
        ).distinct()[:3]
        for focus_id in comp_failures:
            try:
                focus = ChunkComprehensionFocus.objects.get(id=focus_id)
                recommendations.append({
                    'domain':   'comprehension',
                    'type':     'focus',
                    'id':       focus_id,
                    'title':    focus.focus_title,
                    'level':    focus.get_level_display(),
                    'reason':   f"{focus.get_level_display()} level needs work",
                    'priority': 'medium',
                })
            except ChunkComprehensionFocus.DoesNotExist:
                pass

        # Writing — new architecture
        # Recommend stages in cooldown or failed produce attempts
        year = _get_current_writing_year()
        if year:
            writing_needs_review = WritingAttempt.objects.filter(
                user=user,
                phase=PHASE_PRODUCE,
                status__in=(STATUS_FAILED, STATUS_COOLDOWN),
            ).select_related(
                'content__stage'
            ).order_by('-created_at').distinct()[:2]

            for attempt in writing_needs_review:
                recommendations.append({
                    'domain':   'writing',
                    'type':     'stage',
                    'id':       attempt.content.id,
                    'title':    attempt.content.stage.name,
                    'reason':   'Writing practice needed — review and retry',
                    'priority': 'medium',
                })

        # Pronunciation
        pron_review = PronunciationMastery.objects.filter(
            user=user, is_mastered=False
        ).filter(
            Q(last_attempted__lt=timezone.now() - timedelta(days=7))
            | Q(last_attempted__isnull=True)
        ).select_related('focus')[:2]
        for mastery in pron_review:
            recommendations.append({
                'domain':   'pronunciation',
                'type':     'focus',
                'id':       mastery.focus_id,
                'title':    mastery.focus.focus_title,
                'reason':   'Not practiced recently',
                'priority': 'low',
            })

        # Unit tests
        units_failed = UnitTestSession.objects.filter(
            user=user, passed=False
        ).values_list('unit_id', flat=True).distinct()[:2]
        for unit_id in units_failed:
            try:
                unit          = Unit.objects.get(id=unit_id)
                attempts_used = UnitTestSession.objects.filter(
                    user=user, unit_id=unit_id
                ).count()
                if attempts_used < 3:
                    recommendations.append({
                        'domain':   'unit_test',
                        'type':     'unit',
                        'id':       unit_id,
                        'title':    f"Unit {unit.number}: {unit.title}",
                        'reason':   f'Failed test (attempt {attempts_used + 1}/3)',
                        'priority': 'highest',
                    })
            except Unit.DoesNotExist:
                pass

        priority_order = {'highest': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(
            key=lambda x: priority_order.get(x['priority'], 4)
        )
        return recommendations[:limit]

    def _get_upcoming_tests(self, user, limit=5):
        upcoming = []
        for unit in Unit.objects.all().order_by('number'):
            sessions = UnitTestSession.objects.filter(user=user, unit=unit)
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
        return upcoming[:limit]

    def _get_unit_progress(self, user):
        units    = Unit.objects.all().order_by('number')
        progress = []

        for unit in units:
            total_lessons     = unit.lessons.count()
            completed_lessons = 0

            for lesson in unit.lessons.all():
                chunks = lesson.chunks.all()
                if chunks.exists() and all(
                    chunk.is_mastered_by(user) for chunk in chunks
                ):
                    completed_lessons += 1

            test_sessions = UnitTestSession.objects.filter(user=user, unit=unit)
            test_score    = None
            test_passed   = None
            if test_sessions.exists():
                best        = test_sessions.order_by('-score_percentage').first()
                test_score  = best.score_percentage
                test_passed = best.passed

            last_activity = self._get_unit_last_activity(user, unit)

            progress.append({
                'unit_id':              unit.id,
                'unit_title':           unit.title,
                'unit_number':          unit.number,
                'total_lessons':        total_lessons,
                'completed_lessons':    completed_lessons,
                'completion_percentage': (
                    (completed_lessons / total_lessons * 100)
                    if total_lessons > 0 else 0
                ),
                'test_score':           test_score,
                'test_passed':          test_passed,
                'last_activity':        last_activity,
            })

        return progress

    def _get_unit_last_activity(self, user, unit):
        chunks     = LessonChunk.objects.filter(lesson__unit=unit)
        timestamps = []

        for qs, field in [
            (GrammarPracticeAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'attempted_at'),
            (PunctuationPracticeAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'created_at'),
            (VocabularyAttempt.objects.filter(
                user=user, vocab_item__chunk__in=chunks
            ), 'created_at'),
            (ComprehensionPracticeAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'attempted_at'),
            (PronunciationAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'created_at'),
            (UnitTestSession.objects.filter(user=user, unit=unit), 'started_at'),
        ]:
            ts = qs.order_by(f'-{field}').values_list(field, flat=True).first()
            if ts:
                timestamps.append(ts)

        # Writing — scoped to unit
        writing_ts = WritingAttempt.objects.filter(
            user=user, content__unit=unit
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if writing_ts:
            timestamps.append(writing_ts)

        return max(timestamps) if timestamps else None

    def _get_in_progress_items(self, user, limit=5):
        in_progress = []

        # Grammar
        grammar_in_progress = GrammarTestAttempt.objects.filter(
            user=user, is_mastered=False
        ).values_list('focus_id', flat=True).distinct()[:2]
        for focus_id in grammar_in_progress:
            try:
                focus  = ChunkGrammarFocus.objects.get(id=focus_id)
                latest = GrammarTestAttempt.objects.filter(
                    user=user, focus=focus
                ).order_by('-created_at').first()
                in_progress.append({
                    'domain':   'grammar',
                    'id':       focus_id,
                    'title':    focus.focus_title,
                    'progress': (
                        f"Attempt {latest.attempt_number}/3"
                        if latest else "Started"
                    ),
                })
            except ChunkGrammarFocus.DoesNotExist:
                pass

        # Vocabulary
        vocab_in_progress = StudentVocabMastery.objects.filter(
            user=user, mastery_level__in=['learning', 'review']
        ).select_related('vocab_item')[:2]
        for mastery in vocab_in_progress:
            in_progress.append({
                'domain':   'vocabulary',
                'id':       mastery.vocab_item_id,
                'title':    mastery.vocab_item.word,
                'progress': (
                    f"{mastery.mastery_level.capitalize()} "
                    f"({mastery.accuracy_percentage:.0f}%)"
                ),
            })

        return in_progress[:limit]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        user = request.user

        grammar_mastery       = self._get_domain_mastery_percentage(
            user, GrammarTestAttempt, ChunkGrammarFocus
        )
        punctuation_mastery   = self._get_domain_mastery_percentage(
            user, PunctuationTestAttempt, ChunkPunctuationFocus
        )
        vocabulary_mastery    = self._get_vocabulary_mastery_percentage(user)
        comprehension_mastery = self._get_domain_mastery_percentage(
            user, ComprehensionTestAttempt, ChunkComprehensionFocus
        )
        writing_mastery       = self._get_writing_mastery_percentage(user)
        pronunciation_mastery = self._get_pronunciation_mastery_percentage(user)
        streak_days           = self._calculate_streak(user)
        recommendations       = self._get_recommendations(user, 1)
        next_step             = recommendations[0] if recommendations else None

        return Response({
            'streak_days':     streak_days,
            'overall_mastery': self._calculate_overall_mastery(user),
            'domains': {
                'grammar':       grammar_mastery,
                'punctuation':   punctuation_mastery,
                'vocabulary':    vocabulary_mastery,
                'comprehension': comprehension_mastery,
                'writing':       writing_mastery,
                'pronunciation': pronunciation_mastery,
            },
            'next_step': next_step,
        })

    def _get_domain_mastery_percentage(self, user, test_model, focus_model):
        total = focus_model.objects.count()
        if total == 0:
            return 0
        mastered = test_model.objects.filter(
            user=user, is_mastered=True
        ).values('focus').distinct().count()
        return (mastered / total * 100)

    def _get_vocabulary_mastery_percentage(self, user):
        total = VocabularyItem.objects.count()
        if total == 0:
            return 0
        mastered = StudentVocabMastery.objects.filter(
            user=user, mastery_level='mastered'
        ).count()
        return (mastered / total * 100)

    def _get_writing_mastery_percentage(self, user):
        """Writing mastery — new architecture."""
        year  = _get_current_writing_year()
        total = WritingStageContent.objects.filter(is_complete=True).count()
        if total == 0:
            return 0
        mastered = (
            WritingStageMastery.objects.filter(
                user=user, academic_year=year
            ).count()
            if year else 0
        )
        return (mastered / total * 100)

    def _get_pronunciation_mastery_percentage(self, user):
        total = PronunciationFocus.objects.count()
        if total == 0:
            return 0
        mastered = PronunciationMastery.objects.filter(
            user=user, is_mastered=True
        ).count()
        return (mastered / total * 100)


# ============================================================
# UNIT PROGRESS VIEWS
# ============================================================

class UnitProgressViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def detail(self, request):
        unit_id = request.query_params.get('unit_id')
        if not unit_id:
            return Response(
                {'error': 'unit_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unit = get_object_or_404(Unit, id=unit_id)
        user = request.user

        lessons = []
        for lesson in unit.lessons.all().order_by('number'):
            chunks        = lesson.chunks.all()
            total_chunks  = chunks.count()
            mastered_chunks = 0
            for chunk in chunks:
                if chunk.is_mastered_by(user):
                    mastered_chunks += 1
            lessons.append({
                'lesson_id':             lesson.id,
                'lesson_number':         lesson.number,
                'lesson_title':          lesson.title,
                'total_chunks':          total_chunks,
                'mastered_chunks':       mastered_chunks,
                'completion_percentage': (
                    (mastered_chunks / total_chunks * 100)
                    if total_chunks > 0 else 0
                ),
            })

        test_sessions = UnitTestSession.objects.filter(
            user=user, unit=unit
        ).order_by('-attempt_number')

        test_progress = {
            'attempts':          test_sessions.count(),
            'attempts_remaining': 3 - test_sessions.count(),
            'best_score': (
                test_sessions.order_by(
                    '-score_percentage'
                ).first().score_percentage
                if test_sessions.exists() else None
            ),
            'latest_score': (
                test_sessions.first().score_percentage
                if test_sessions.exists() else None
            ),
            'passed':   test_sessions.filter(passed=True).exists(),
            'sessions': UnitTestSessionListSerializer(
                test_sessions, many=True
            ).data,
        }

        chunks        = LessonChunk.objects.filter(lesson__unit=unit)
        domain_mastery = self._get_unit_domain_mastery(user, chunks, unit)
        last_activity  = self._get_unit_last_activity(user, unit, chunks)

        return Response({
            'unit_id':        unit.id,
            'unit_number':    unit.number,
            'unit_title':     unit.title,
            'total_lessons':  unit.lessons.count(),
            'lessons':        lessons,
            'test_progress':  test_progress,
            'domain_mastery': domain_mastery,
            'last_activity':  last_activity,
        })

    def _get_unit_domain_mastery(self, user, chunks, unit):
        mastery = {}

        grammar_focuses = ChunkGrammarFocus.objects.filter(chunk__in=chunks)
        if grammar_focuses.exists():
            total    = grammar_focuses.count()
            mastered = GrammarTestAttempt.objects.filter(
                user=user, focus__in=grammar_focuses, is_mastered=True
            ).values('focus').distinct().count()
            mastery['grammar'] = (mastered / total * 100) if total > 0 else 0

        punct_focuses = ChunkPunctuationFocus.objects.filter(chunk__in=chunks)
        if punct_focuses.exists():
            total    = punct_focuses.count()
            mastered = PunctuationTestAttempt.objects.filter(
                user=user, focus__in=punct_focuses, is_mastered=True
            ).values('focus').distinct().count()
            mastery['punctuation'] = (mastered / total * 100) if total > 0 else 0

        vocab_items = VocabularyItem.objects.filter(chunk__in=chunks)
        if vocab_items.exists():
            total    = vocab_items.count()
            mastered = StudentVocabMastery.objects.filter(
                user=user, vocab_item__in=vocab_items, mastery_level='mastered'
            ).count()
            mastery['vocabulary'] = (mastered / total * 100) if total > 0 else 0

        comp_focuses = ChunkComprehensionFocus.objects.filter(chunk__in=chunks)
        if comp_focuses.exists():
            total    = comp_focuses.count()
            mastered = ComprehensionTestAttempt.objects.filter(
                user=user, focus__in=comp_focuses, is_mastered=True
            ).values('focus').distinct().count()
            mastery['comprehension'] = (mastered / total * 100) if total > 0 else 0

        # Writing — new architecture, scoped to unit
        year = _get_current_writing_year()
        writing_contents = WritingStageContent.objects.filter(
            unit=unit, is_complete=True
        )
        if writing_contents.exists() and year:
            total    = writing_contents.count()
            mastered = WritingStageMastery.objects.filter(
                user=user,
                content__in=writing_contents,
                academic_year=year,
            ).count()
            mastery['writing'] = (mastered / total * 100) if total > 0 else 0

        pron_focuses = PronunciationFocus.objects.filter(chunk__in=chunks)
        if pron_focuses.exists():
            total    = pron_focuses.count()
            mastered = PronunciationMastery.objects.filter(
                user=user, focus__in=pron_focuses, is_mastered=True
            ).count()
            mastery['pronunciation'] = (mastered / total * 100) if total > 0 else 0

        return mastery

    def _get_unit_last_activity(self, user, unit, chunks):
        timestamps = []

        for qs, field in [
            (GrammarPracticeAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'attempted_at'),
            (PunctuationPracticeAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'created_at'),
            (VocabularyAttempt.objects.filter(
                user=user, vocab_item__chunk__in=chunks
            ), 'created_at'),
            (ComprehensionPracticeAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'attempted_at'),
            (PronunciationAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'created_at'),
            (UnitTestSession.objects.filter(
                user=user, unit=unit
            ), 'started_at'),
        ]:
            ts = qs.order_by(f'-{field}').values_list(field, flat=True).first()
            if ts:
                timestamps.append(ts)

        writing_ts = WritingAttempt.objects.filter(
            user=user, content__unit=unit
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if writing_ts:
            timestamps.append(writing_ts)

        return max(timestamps) if timestamps else None


# ============================================================
# LESSON PROGRESS VIEWS
# ============================================================

class LessonProgressViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def detail(self, request):
        lesson_id = request.query_params.get('lesson_id')
        if not lesson_id:
            return Response(
                {'error': 'lesson_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lesson = get_object_or_404(Lesson, id=lesson_id)
        user   = request.user

        chunks         = lesson.chunks.all().order_by('order')
        chunk_progress = []

        for chunk in chunks:
            is_mastered = chunk.is_mastered_by(user)
            status_data = chunk.get_mastery_status(user)
            chunk_progress.append({
                'chunk_id':    chunk.id,
                'order':       chunk.order,
                'mastered':    is_mastered,
                'next_domain': (
                    status_data.get('next_domain_to_work')
                    if status_data else None
                ),
                'estimated_time': chunk.estimated_time_minutes,
                'by_domain':   (
                    status_data.get('by_domain') if status_data else {}
                ),
            })

        total_chunks    = chunks.count()
        mastered_chunks = sum(1 for c in chunk_progress if c['mastered'])
        time_spent      = self._get_lesson_time_spent(user, lesson)
        last_activity   = self._get_lesson_last_activity(user, lesson)

        return Response({
            'lesson_id':             lesson.id,
            'lesson_number':         lesson.number,
            'lesson_title':          lesson.title,
            'total_chunks':          total_chunks,
            'mastered_chunks':       mastered_chunks,
            'completion_percentage': (
                (mastered_chunks / total_chunks * 100)
                if total_chunks > 0 else 0
            ),
            'estimated_total_minutes': lesson.chunks.aggregate(
                total=Sum('estimated_time_minutes')
            )['total'] or 0,
            'time_spent_minutes': time_spent,
            'chunk_progress':     chunk_progress,
            'last_activity':      last_activity,
            'next_chunk': next(
                (c for c in chunk_progress if not c['mastered']), None
            ),
        })

    def _get_lesson_time_spent(self, user, lesson):
        chunks        = lesson.chunks.all()
        total_seconds = 0

        total_seconds += GrammarPracticeAttempt.objects.filter(
            user=user, focus__chunk__in=chunks
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += PunctuationPracticeAttempt.objects.filter(
            user=user, focus__chunk__in=chunks
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += VocabularyAttempt.objects.filter(
            user=user, vocab_item__chunk__in=chunks
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += ComprehensionPracticeAttempt.objects.filter(
            user=user, focus__chunk__in=chunks
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += PronunciationAttempt.objects.filter(
            user=user, focus__chunk__in=chunks
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        # Writing is unit-level, not lesson-level

        return total_seconds // 60

    def _get_lesson_last_activity(self, user, lesson):
        chunks     = lesson.chunks.all()
        timestamps = []

        for qs, field in [
            (GrammarPracticeAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'attempted_at'),
            (PunctuationPracticeAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'created_at'),
            (VocabularyAttempt.objects.filter(
                user=user, vocab_item__chunk__in=chunks
            ), 'created_at'),
            (ComprehensionPracticeAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'attempted_at'),
            (PronunciationAttempt.objects.filter(
                user=user, focus__chunk__in=chunks
            ), 'created_at'),
        ]:
            ts = qs.order_by(f'-{field}').values_list(field, flat=True).first()
            if ts:
                timestamps.append(ts)

        return max(timestamps) if timestamps else None


# ============================================================
# ANALYTICS VIEWS
# ============================================================

class AnalyticsViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def class_overview(self, request):
        return Response({'message': 'Class analytics not implemented'})

    @action(detail=False, methods=['get'])
    def domain_performance(self, request):
        users        = User.objects.filter(is_staff=False)
        domain_stats = {
            'grammar':       {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
            'punctuation':   {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
            'vocabulary':    {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
            'comprehension': {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
            'writing':       {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
            'pronunciation': {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
        }
        return Response(domain_stats)