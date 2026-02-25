# api_views/progress.py

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
from django.contrib.auth import get_user_model

from content.serializers.progress import (
    # Domain-specific progress
    GrammarProgressSerializer, PunctuationProgressSerializer,
    VocabularyProgressSerializer, ComprehensionProgressSerializer,
    WritingProgressSerializer, PronunciationProgressSerializer,
    UnitTestProgressSerializer,
    
    # Overall dashboard
    OverallProgressSerializer, DomainProgressMobileSerializer,
    DashboardMobileSerializer,
    
    # Unit/Lesson progress
    UnitProgressDetailSerializer, LessonProgressSerializer
)
from .base import BaseViewSet, ProgressViewSet, log_user_activity
from .testing import UnitTestSessionListSerializer

User = get_user_model()


# ============================================================
# DASHBOARD VIEWS
# ============================================================

class DashboardViewSet(viewsets.GenericViewSet):
    """
    Main dashboard view aggregating all progress data.
    Provides comprehensive overview of student performance.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on request.
        """
        if self.request.GET.get('mobile') == 'true':
            return DashboardMobileSerializer
        return OverallProgressSerializer
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Get complete dashboard overview.
        """
        user = request.user
        
        # Get domain progress data
        grammar = GrammarProgressSerializer(user=user).data
        punctuation = PunctuationProgressSerializer(user=user).data
        vocabulary = VocabularyProgressSerializer(user=user).data
        comprehension = ComprehensionProgressSerializer(user=user).data
        writing = WritingProgressSerializer(user=user).data
        pronunciation = PronunciationProgressSerializer(user=user).data
        unit_tests = UnitTestProgressSerializer(user=user).data
        
        # Calculate overall mastery
        overall_mastery = self._calculate_overall_mastery(user)
        
        # Get recent activity
        recent_activity = self._get_recent_activity(user)
        
        # Get recommendations
        recommendations = self._get_recommendations(user)
        
        # Get upcoming tests
        upcoming_tests = self._get_upcoming_tests(user)
        
        # Get unit progress
        unit_progress = self._get_unit_progress(user)
        
        # Get streak days
        streak_days = self._calculate_streak(user)
        
        # Total time spent
        total_time_hours = self._calculate_total_time(user)
        
        if request.GET.get('mobile') == 'true':
            # Mobile dashboard - lightweight
            data = {
                'streak_days': streak_days,
                'overall_mastery': overall_mastery,
                'grammar': {
                    'mastery_percentage': grammar.get('mastery_percentage', 0),
                    'needs_review_count': grammar.get('needs_review_count', 0),
                    'last_activity': grammar.get('last_activity')
                },
                'punctuation': {
                    'mastery_percentage': punctuation.get('mastery_percentage', 0),
                    'needs_review_count': punctuation.get('needs_review_count', 0),
                    'last_activity': punctuation.get('last_activity')
                },
                'vocabulary': {
                    'mastery_percentage': vocabulary.get('mastery_percentage', 0),
                    'needs_review_count': vocabulary.get('needs_review_count', 0),
                    'last_activity': vocabulary.get('last_activity')
                },
                'comprehension': {
                    'mastery_percentage': comprehension.get('mastery_percentage', 0),
                    'needs_review_count': comprehension.get('needs_review_count', 0),
                    'last_activity': comprehension.get('last_activity')
                },
                'writing': {
                    'mastery_percentage': writing.get('chunk_mastery_percentage', 0),
                    'needs_review_count': writing.get('needs_review_count', 0),
                    'last_activity': writing.get('last_activity')
                },
                'pronunciation': {
                    'mastery_percentage': pronunciation.get('mastery_percentage', 0),
                    'needs_review_count': pronunciation.get('needs_review_count', 0),
                    'last_activity': pronunciation.get('last_activity')
                },
                'recent_activity': recent_activity[:5],
                'next_steps': recommendations[:3],
                'in_progress': self._get_in_progress_items(user)[:3]
            }
        else:
            # Full dashboard
            data = {
                'student_id': user.id,
                'student_name': user.get_full_name() or user.username,
                'overall_mastery': overall_mastery,
                'total_practices': self._calculate_total_practices(user),
                'total_time_spent_hours': total_time_hours,
                'streak_days': streak_days,
                'grammar': grammar,
                'punctuation': punctuation,
                'vocabulary': vocabulary,
                'comprehension': comprehension,
                'writing': writing,
                'pronunciation': pronunciation,
                'unit_tests': unit_tests,
                'recent_activity': recent_activity,
                'recommended_focus': recommendations,
                'upcoming_tests': upcoming_tests,
                'unit_progress': unit_progress
            }
        
        log_user_activity(user, 'view_dashboard', {'mobile': request.GET.get('mobile') == 'true'})
        
        return Response(data)
    
    def _calculate_overall_mastery(self, user):
        """Calculate overall mastery percentage across all domains."""
        # Get total focuses/items per domain
        total_grammar = ChunkGrammarFocus.objects.count()
        total_punctuation = ChunkPunctuationFocus.objects.count()
        total_vocab = VocabularyItem.objects.count()
        total_comprehension = ChunkComprehensionFocus.objects.count()
        total_writing_chunk = ChunkWritingFocus.objects.count()
        total_pronunciation = PronunciationFocus.objects.count()
        
        # Get mastered counts
        mastered_grammar = GrammarTestAttempt.objects.filter(
            user=user, is_mastered=True
        ).values('focus').distinct().count()
        
        mastered_punctuation = PunctuationTestAttempt.objects.filter(
            user=user, is_mastered=True
        ).values('focus').distinct().count()
        
        mastered_vocab = StudentVocabMastery.objects.filter(
            user=user, mastery_level='mastered'
        ).count()
        
        mastered_comprehension = ComprehensionTestAttempt.objects.filter(
            user=user, is_mastered=True
        ).values('focus').distinct().count()
        
        mastered_writing = WritingTestAttempt.objects.filter(
            user=user, focus__isnull=False, is_mastered=True
        ).values('focus').distinct().count()
        
        mastered_pronunciation = PronunciationMastery.objects.filter(
            user=user, is_mastered=True
        ).count()
        
        # Calculate percentages
        grammar_pct = (mastered_grammar / total_grammar * 100) if total_grammar > 0 else 0
        punctuation_pct = (mastered_punctuation / total_punctuation * 100) if total_punctuation > 0 else 0
        vocab_pct = (mastered_vocab / total_vocab * 100) if total_vocab > 0 else 0
        comprehension_pct = (mastered_comprehension / total_comprehension * 100) if total_comprehension > 0 else 0
        writing_pct = (mastered_writing / total_writing_chunk * 100) if total_writing_chunk > 0 else 0
        pronunciation_pct = (mastered_pronunciation / total_pronunciation * 100) if total_pronunciation > 0 else 0
        
        # Average all percentages
        percentages = [
            grammar_pct, punctuation_pct, vocab_pct,
            comprehension_pct, writing_pct, pronunciation_pct
        ]
        valid_percentages = [p for p in percentages if p > 0]
        
        if not valid_percentages:
            return 0
        
        return sum(valid_percentages) / len(valid_percentages)
    
    def _calculate_total_practices(self, user):
        """Calculate total practice attempts across all domains."""
        total = 0
        total += GrammarPracticeAttempt.objects.filter(user=user).count()
        total += PunctuationPracticeAttempt.objects.filter(user=user).count()
        total += VocabularyAttempt.objects.filter(user=user).count()
        total += ComprehensionPracticeAttempt.objects.filter(user=user).count()
        total += WritingPracticeAttempt.objects.filter(user=user).count()
        total += PronunciationAttempt.objects.filter(user=user).count()
        return total
    
    def _calculate_total_time(self, user):
        """Calculate total time spent in hours."""
        total_seconds = 0
        
        # Grammar time
        grammar_seconds = GrammarPracticeAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += grammar_seconds
        
        # Punctuation time
        punct_seconds = PunctuationPracticeAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += punct_seconds
        
        # Vocabulary time
        vocab_seconds = VocabularyAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += vocab_seconds
        
        # Comprehension time
        comp_seconds = ComprehensionPracticeAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += comp_seconds
        
        # Writing time
        writing_seconds = WritingPracticeAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_spent_seconds'))['total'] or 0
        total_seconds += writing_seconds
        
        # Test time
        test_seconds = UnitTestSession.objects.filter(
            user=user,
            completed_at__isnull=False
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += test_seconds
        
        return total_seconds / 3600  # Convert to hours
    
    def _calculate_streak(self, user):
        """Calculate current activity streak in days."""
        from django.db.models.functions import TruncDate
        
        # Get all activity dates
        activity_dates = set()
        
        # Grammar practice
        grammar_dates = GrammarPracticeAttempt.objects.filter(
            user=user
        ).annotate(date=TruncDate('attempted_at')).values_list('date', flat=True)
        activity_dates.update(grammar_dates)
        
        # Punctuation practice
        punct_dates = PunctuationPracticeAttempt.objects.filter(
            user=user
        ).annotate(date=TruncDate('created_at')).values_list('date', flat=True)
        activity_dates.update(punct_dates)
        
        # Vocabulary attempts
        vocab_dates = VocabularyAttempt.objects.filter(
            user=user
        ).annotate(date=TruncDate('created_at')).values_list('date', flat=True)
        activity_dates.update(vocab_dates)
        
        # Comprehension practice
        comp_dates = ComprehensionPracticeAttempt.objects.filter(
            user=user
        ).annotate(date=TruncDate('attempted_at')).values_list('date', flat=True)
        activity_dates.update(comp_dates)
        
        # Writing practice
        writing_dates = WritingPracticeAttempt.objects.filter(
            user=user
        ).annotate(date=TruncDate('created_at')).values_list('date', flat=True)
        activity_dates.update(writing_dates)
        
        # Pronunciation attempts
        pron_dates = PronunciationAttempt.objects.filter(
            user=user
        ).annotate(date=TruncDate('created_at')).values_list('date', flat=True)
        activity_dates.update(pron_dates)
        
        # Test sessions
        test_dates = UnitTestSession.objects.filter(
            user=user
        ).annotate(date=TruncDate('started_at')).values_list('date', flat=True)
        activity_dates.update(test_dates)
        
        if not activity_dates:
            return 0
        
        # Sort dates and calculate streak
        sorted_dates = sorted(activity_dates, reverse=True)
        today = timezone.now().date()
        
        streak = 0
        current_date = today
        
        while current_date in sorted_dates:
            streak += 1
            current_date -= timedelta(days=1)
        
        return streak
    
    def _get_recent_activity(self, user, limit=20):
        """Get recent activity across all domains."""
        activities = []
        
        # Grammar practice
        for attempt in GrammarPracticeAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-attempted_at')[:5]:
            activities.append({
                'id': attempt.id,
                'type': 'grammar_practice',
                'domain': 'grammar',
                'title': attempt.focus.focus_title if attempt.focus else 'Grammar Practice',
                'score': attempt.score_percent,
                'passed': attempt.is_passed,
                'timestamp': attempt.attempted_at,
                'description': f"Grammar practice: {attempt.score_percent}%"
            })
        
        # Grammar tests
        for attempt in GrammarTestAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-created_at')[:5]:
            activities.append({
                'id': attempt.id,
                'type': 'grammar_test',
                'domain': 'grammar',
                'title': attempt.focus.focus_title if attempt.focus else 'Grammar Test',
                'score': attempt.score_percent,
                'mastered': attempt.is_mastered,
                'timestamp': attempt.created_at,
                'description': f"Grammar test: {attempt.score_percent}%"
            })
        
        # Punctuation practice
        for attempt in PunctuationPracticeAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-created_at')[:5]:
            activities.append({
                'id': attempt.id,
                'type': 'punctuation_practice',
                'domain': 'punctuation',
                'title': attempt.focus.focus_title if attempt.focus else 'Punctuation Practice',
                'score': attempt.score_percent,
                'passed': attempt.is_passed,
                'timestamp': attempt.created_at,
                'description': f"Punctuation practice: {attempt.score_percent}%"
            })
        
        # Punctuation tests
        for attempt in PunctuationTestAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-created_at')[:5]:
            activities.append({
                'id': attempt.id,
                'type': 'punctuation_test',
                'domain': 'punctuation',
                'title': attempt.focus.focus_title if attempt.focus else 'Punctuation Test',
                'score': attempt.score_percent,
                'mastered': attempt.is_mastered,
                'timestamp': attempt.created_at,
                'description': f"Punctuation test: {attempt.score_percent}%"
            })
        
        # Vocabulary attempts
        for attempt in VocabularyAttempt.objects.filter(
            user=user
        ).select_related('vocab_item').order_by('-created_at')[:5]:
            activities.append({
                'id': attempt.id,
                'type': 'vocabulary',
                'domain': 'vocabulary',
                'title': attempt.vocab_item.word if attempt.vocab_item else 'Vocabulary',
                'correct': attempt.is_correct,
                'timestamp': attempt.created_at,
                'description': f"Vocabulary: {attempt.vocab_item.word} - {'correct' if attempt.is_correct else 'incorrect'}"
            })
        
        # Comprehension practice
        for attempt in ComprehensionPracticeAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-attempted_at')[:5]:
            activities.append({
                'id': attempt.id,
                'type': 'comprehension_practice',
                'domain': 'comprehension',
                'title': attempt.focus.focus_title if attempt.focus else 'Comprehension Practice',
                'score': attempt.score_percent,
                'passed': attempt.is_passed,
                'timestamp': attempt.attempted_at,
                'description': f"Comprehension practice: {attempt.score_percent}%"
            })
        
        # Comprehension tests
        for attempt in ComprehensionTestAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-created_at')[:5]:
            activities.append({
                'id': attempt.id,
                'type': 'comprehension_test',
                'domain': 'comprehension',
                'title': attempt.focus.focus_title if attempt.focus else 'Comprehension Test',
                'score': attempt.score_percent,
                'mastered': attempt.is_mastered,
                'timestamp': attempt.created_at,
                'description': f"Comprehension test: {attempt.score_percent}%"
            })
        
        # Writing practice
        for attempt in WritingPracticeAttempt.objects.filter(
            user=user
        ).select_related('focus', 'prompt').order_by('-created_at')[:5]:
            activities.append({
                'id': attempt.id,
                'type': 'writing_practice',
                'domain': 'writing',
                'title': attempt.focus.focus_title if attempt.focus else 'Writing Practice',
                'score': attempt.keyword_match_score,
                'passed': attempt.is_passed,
                'timestamp': attempt.created_at,
                'description': f"Writing practice: {attempt.keyword_match_score}%"
            })
        
        # Writing tests
        for attempt in WritingTestAttempt.objects.filter(
            user=user
        ).select_related('focus', 'task', 'prompt').order_by('-created_at')[:5]:
            context = 'chunk' if attempt.focus else 'unit'
            title = attempt.focus.focus_title if attempt.focus else (attempt.task.task_title if attempt.task else 'Writing Test')
            activities.append({
                'id': attempt.id,
                'type': 'writing_test',
                'domain': 'writing',
                'title': title,
                'score': attempt.overall_score,
                'mastered': attempt.is_mastered,
                'context': context,
                'timestamp': attempt.created_at,
                'description': f"Writing test ({context}): {attempt.overall_score}%"
            })
        
        # Pronunciation attempts
        for attempt in PronunciationAttempt.objects.filter(
            user=user
        ).select_related('focus').order_by('-created_at')[:5]:
            activities.append({
                'id': attempt.id,
                'type': 'pronunciation',
                'domain': 'pronunciation',
                'title': attempt.focus.focus_title if attempt.focus else 'Pronunciation',
                'score': attempt.ai_score,
                'passed': attempt.is_passed,
                'attempt_type': attempt.attempt_type,
                'timestamp': attempt.created_at,
                'description': f"Pronunciation ({attempt.attempt_type}): {attempt.ai_score}%"
            })
        
        # Unit tests
        for session in UnitTestSession.objects.filter(
            user=user
        ).select_related('unit').order_by('-started_at')[:5]:
            activities.append({
                'id': session.id,
                'type': 'unit_test',
                'domain': 'unit_test',
                'title': f"Unit {session.unit.number}: {session.unit.title}",
                'score': session.score_percentage,
                'passed': session.passed,
                'attempt_number': session.attempt_number,
                'timestamp': session.started_at,
                'description': f"Unit test: {session.score_percentage:.1f}%"
            })
        
        # Sort by timestamp and return
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]
    
    def _get_recommendations(self, user, limit=5):
        """Generate personalized recommendations."""
        recommendations = []
        
        # Check grammar focuses needing review
        grammar_failures = GrammarTestAttempt.objects.filter(
            user=user,
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
        
        # Check punctuation focuses needing review
        punct_failures = PunctuationTestAttempt.objects.filter(
            user=user,
            is_mastered=False
        ).order_by('-created_at').values_list('focus_id', flat=True).distinct()[:3]
        
        for focus_id in punct_failures:
            try:
                focus = ChunkPunctuationFocus.objects.get(id=focus_id)
                recommendations.append({
                    'domain': 'punctuation',
                    'type': 'focus',
                    'id': focus_id,
                    'title': focus.focus_title,
                    'reason': 'Needs review (test failed)',
                    'priority': 'high'
                })
            except ChunkPunctuationFocus.DoesNotExist:
                pass
        
        # Check vocabulary items needing review
        vocab_review = StudentVocabMastery.objects.filter(
            user=user,
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
        
        # Check comprehension focuses needing review
        comp_failures = ComprehensionTestAttempt.objects.filter(
            user=user,
            is_mastered=False
        ).order_by('-created_at').values_list('focus_id', flat=True).distinct()[:3]
        
        for focus_id in comp_failures:
            try:
                focus = ChunkComprehensionFocus.objects.get(id=focus_id)
                recommendations.append({
                    'domain': 'comprehension',
                    'type': 'focus',
                    'id': focus_id,
                    'title': focus.focus_title,
                    'level': focus.get_level_display(),
                    'reason': f"{focus.get_level_display()} level needs work",
                    'priority': 'medium'
                })
            except ChunkComprehensionFocus.DoesNotExist:
                pass
        
        # Check writing focuses needing review
        writing_failures = WritingTestAttempt.objects.filter(
            user=user,
            focus__isnull=False,
            is_mastered=False
        ).order_by('-created_at').values_list('focus_id', flat=True).distinct()[:2]
        
        for focus_id in writing_failures:
            try:
                focus = ChunkWritingFocus.objects.get(id=focus_id)
                recommendations.append({
                    'domain': 'writing',
                    'type': 'focus',
                    'id': focus_id,
                    'title': focus.focus_title,
                    'reason': 'Writing practice needed',
                    'priority': 'medium'
                })
            except ChunkWritingFocus.DoesNotExist:
                pass
        
        # Check pronunciation focuses needing review
        pron_review = PronunciationMastery.objects.filter(
            user=user,
            is_mastered=False
        ).filter(
            Q(last_attempted__lt=timezone.now() - timedelta(days=7)) |
            Q(last_attempted__isnull=True)
        ).select_related('focus')[:2]
        
        for mastery in pron_review:
            recommendations.append({
                'domain': 'pronunciation',
                'type': 'focus',
                'id': mastery.focus_id,
                'title': mastery.focus.focus_title,
                'reason': 'Not practiced recently',
                'priority': 'low'
            })
        
        # Check unit tests not passed
        units_failed = UnitTestSession.objects.filter(
            user=user,
            passed=False
        ).values_list('unit_id', flat=True).distinct()[:2]
        
        for unit_id in units_failed:
            try:
                unit = Unit.objects.get(id=unit_id)
                attempts_used = UnitTestSession.objects.filter(
                    user=user,
                    unit_id=unit_id
                ).count()
                
                if attempts_used < 3:
                    recommendations.append({
                        'domain': 'unit_test',
                        'type': 'unit',
                        'id': unit_id,
                        'title': f"Unit {unit.number}: {unit.title}",
                        'reason': f'Failed test (attempt {attempts_used + 1}/3)',
                        'priority': 'highest'
                    })
            except Unit.DoesNotExist:
                pass
        
        # Sort by priority
        priority_order = {'highest': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return recommendations[:limit]
    
    def _get_upcoming_tests(self, user, limit=5):
        """Identify upcoming unit tests."""
        upcoming = []
        
        # Get all units
        units = Unit.objects.all().order_by('number')
        
        for unit in units:
            sessions = UnitTestSession.objects.filter(user=user, unit=unit)
            
            if not sessions.exists():
                # Not attempted yet
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
        
        return upcoming[:limit]
    
    def _get_unit_progress(self, user):
        """Get progress for all units."""
        units = Unit.objects.all().order_by('number')
        progress = []
        
        for unit in units:
            # Count lessons in unit
            total_lessons = unit.lessons.count()
            completed_lessons = 0
            
            for lesson in unit.lessons.all():
                # Check if all chunks in lesson are mastered
                chunks = lesson.chunks.all()
                if chunks.exists() and all(chunk.is_mastered_by(user) for chunk in chunks):
                    completed_lessons += 1
            
            # Get test info
            test_sessions = UnitTestSession.objects.filter(user=user, unit=unit)
            test_score = None
            test_passed = None
            if test_sessions.exists():
                best = test_sessions.order_by('-score_percentage').first()
                test_score = best.score_percentage
                test_passed = best.passed
            
            # Get last activity
            last_activity = self._get_unit_last_activity(user, unit)
            
            progress.append({
                'unit_id': unit.id,
                'unit_title': unit.title,
                'unit_number': unit.number,
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'completion_percentage': (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0,
                'test_score': test_score,
                'test_passed': test_passed,
                'last_activity': last_activity
            })
        
        return progress
    
    def _get_unit_last_activity(self, user, unit):
        """Get most recent activity timestamp for a unit."""
        chunks = LessonChunk.objects.filter(lesson__unit=unit)
        
        timestamps = []
        
        # Grammar practice
        grammar_time = GrammarPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        if grammar_time:
            timestamps.append(grammar_time)
        
        # Punctuation practice
        punct_time = PunctuationPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if punct_time:
            timestamps.append(punct_time)
        
        # Vocabulary attempts
        vocab_time = VocabularyAttempt.objects.filter(
            user=user,
            vocab_item__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if vocab_time:
            timestamps.append(vocab_time)
        
        # Comprehension practice
        comp_time = ComprehensionPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        if comp_time:
            timestamps.append(comp_time)
        
        # Writing practice
        writing_time = WritingPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if writing_time:
            timestamps.append(writing_time)
        
        # Pronunciation attempts
        pron_time = PronunciationAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if pron_time:
            timestamps.append(pron_time)
        
        # Test sessions
        test_time = UnitTestSession.objects.filter(
            user=user,
            unit=unit
        ).order_by('-started_at').values_list('started_at', flat=True).first()
        if test_time:
            timestamps.append(test_time)
        
        if timestamps:
            return max(timestamps)
        return None
    
    def _get_in_progress_items(self, user, limit=5):
        """Get items currently in progress."""
        in_progress = []
        
        # Grammar focuses in progress
        grammar_in_progress = GrammarTestAttempt.objects.filter(
            user=user,
            is_mastered=False
        ).values_list('focus_id', flat=True).distinct()[:2]
        
        for focus_id in grammar_in_progress:
            try:
                focus = ChunkGrammarFocus.objects.get(id=focus_id)
                latest = GrammarTestAttempt.objects.filter(
                    user=user, focus=focus
                ).order_by('-created_at').first()
                
                in_progress.append({
                    'domain': 'grammar',
                    'id': focus_id,
                    'title': focus.focus_title,
                    'progress': f"Attempt {latest.attempt_number}/3" if latest else "Started"
                })
            except ChunkGrammarFocus.DoesNotExist:
                pass
        
        # Vocabulary items in progress
        vocab_in_progress = StudentVocabMastery.objects.filter(
            user=user,
            mastery_level__in=['learning', 'review']
        ).select_related('vocab_item')[:2]
        
        for mastery in vocab_in_progress:
            in_progress.append({
                'domain': 'vocabulary',
                'id': mastery.vocab_item_id,
                'title': mastery.vocab_item.word,
                'progress': f"{mastery.mastery_level.capitalize()} ({mastery.accuracy_percentage:.0f}%)"
            })
        
        return in_progress[:limit]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get quick progress summary for mobile home screen.
        """
        user = request.user
        
        # Get domain mastery percentages
        grammar_mastery = self._get_domain_mastery_percentage(
            user, 
            GrammarTestAttempt,
            ChunkGrammarFocus
        )
        
        punctuation_mastery = self._get_domain_mastery_percentage(
            user,
            PunctuationTestAttempt,
            ChunkPunctuationFocus
        )
        
        vocabulary_mastery = self._get_vocabulary_mastery_percentage(user)
        
        comprehension_mastery = self._get_domain_mastery_percentage(
            user,
            ComprehensionTestAttempt,
            ChunkComprehensionFocus
        )
        
        writing_mastery = self._get_writing_mastery_percentage(user)
        
        pronunciation_mastery = self._get_pronunciation_mastery_percentage(user)
        
        # Get streak
        streak_days = self._calculate_streak(user)
        
        # Get next recommended item
        recommendations = self._get_recommendations(user, 1)
        next_step = recommendations[0] if recommendations else None
        
        summary = {
            'streak_days': streak_days,
            'overall_mastery': self._calculate_overall_mastery(user),
            'domains': {
                'grammar': grammar_mastery,
                'punctuation': punctuation_mastery,
                'vocabulary': vocabulary_mastery,
                'comprehension': comprehension_mastery,
                'writing': writing_mastery,
                'pronunciation': pronunciation_mastery
            },
            'next_step': next_step
        }
        
        return Response(summary)
    
    def _get_domain_mastery_percentage(self, user, test_model, focus_model):
        """Calculate mastery percentage for a domain."""
        total = focus_model.objects.count()
        if total == 0:
            return 0
        
        mastered = test_model.objects.filter(
            user=user,
            is_mastered=True
        ).values('focus').distinct().count()
        
        return (mastered / total * 100)
    
    def _get_vocabulary_mastery_percentage(self, user):
        """Calculate vocabulary mastery percentage."""
        total = VocabularyItem.objects.count()
        if total == 0:
            return 0
        
        mastered = StudentVocabMastery.objects.filter(
            user=user,
            mastery_level='mastered'
        ).count()
        
        return (mastered / total * 100)
    
    def _get_writing_mastery_percentage(self, user):
        """Calculate writing mastery percentage."""
        total = ChunkWritingFocus.objects.count()
        if total == 0:
            return 0
        
        mastered = WritingTestAttempt.objects.filter(
            user=user,
            focus__isnull=False,
            is_mastered=True
        ).values('focus').distinct().count()
        
        return (mastered / total * 100)
    
    def _get_pronunciation_mastery_percentage(self, user):
        """Calculate pronunciation mastery percentage."""
        total = PronunciationFocus.objects.count()
        if total == 0:
            return 0
        
        mastered = PronunciationMastery.objects.filter(
            user=user,
            is_mastered=True
        ).count()
        
        return (mastered / total * 100)


# ============================================================
# UNIT PROGRESS VIEWS
# ============================================================

class UnitProgressViewSet(viewsets.GenericViewSet):
    """
    ViewSet for unit-level progress tracking.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def detail(self, request):
        """
        Get detailed progress for a specific unit.
        """
        unit_id = request.query_params.get('unit_id')
        if not unit_id:
            return Response(
                {'error': 'unit_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        unit = get_object_or_404(Unit, id=unit_id)
        user = request.user
        
        # Get lesson progress
        lessons = []
        for lesson in unit.lessons.all().order_by('number'):
            chunks = lesson.chunks.all()
            total_chunks = chunks.count()
            mastered_chunks = 0
            
            for chunk in chunks:
                if chunk.is_mastered_by(user):
                    mastered_chunks += 1
            
            lessons.append({
                'lesson_id': lesson.id,
                'lesson_number': lesson.number,
                'lesson_title': lesson.title,
                'total_chunks': total_chunks,
                'mastered_chunks': mastered_chunks,
                'completion_percentage': (mastered_chunks / total_chunks * 100) if total_chunks > 0 else 0
            })
        
        # Get test progress
        test_sessions = UnitTestSession.objects.filter(
            user=user,
            unit=unit
        ).order_by('-attempt_number')
        
        test_progress = {
            'attempts': test_sessions.count(),
            'attempts_remaining': 3 - test_sessions.count(),
            'best_score': test_sessions.order_by('-score_percentage').first().score_percentage if test_sessions.exists() else None,
            'latest_score': test_sessions.first().score_percentage if test_sessions.exists() else None,
            'passed': test_sessions.filter(passed=True).exists(),
            'sessions': UnitTestSessionListSerializer(test_sessions, many=True).data
        }
        
        # Get domain mastery within unit
        chunks = LessonChunk.objects.filter(lesson__unit=unit)
        domain_mastery = self._get_unit_domain_mastery(user, chunks)
        
        # Get last activity
        last_activity = self._get_unit_last_activity(user, unit)
        
        data = {
            'unit_id': unit.id,
            'unit_number': unit.number,
            'unit_title': unit.title,
            'total_lessons': unit.lessons.count(),
            'lessons': lessons,
            'test_progress': test_progress,
            'domain_mastery': domain_mastery,
            'last_activity': last_activity
        }
        
        return Response(data)
    
    def _get_unit_domain_mastery(self, user, chunks):
        """Get domain mastery percentages within a unit."""
        mastery = {}
        
        # Grammar
        grammar_focuses = ChunkGrammarFocus.objects.filter(chunk__in=chunks)
        if grammar_focuses.exists():
            total = grammar_focuses.count()
            mastered = GrammarTestAttempt.objects.filter(
                user=user,
                focus__in=grammar_focuses,
                is_mastered=True
            ).values('focus').distinct().count()
            mastery['grammar'] = (mastered / total * 100) if total > 0 else 0
        
        # Punctuation
        punct_focuses = ChunkPunctuationFocus.objects.filter(chunk__in=chunks)
        if punct_focuses.exists():
            total = punct_focuses.count()
            mastered = PunctuationTestAttempt.objects.filter(
                user=user,
                focus__in=punct_focuses,
                is_mastered=True
            ).values('focus').distinct().count()
            mastery['punctuation'] = (mastered / total * 100) if total > 0 else 0
        
        # Vocabulary
        vocab_items = VocabularyItem.objects.filter(chunk__in=chunks)
        if vocab_items.exists():
            total = vocab_items.count()
            mastered = StudentVocabMastery.objects.filter(
                user=user,
                vocab_item__in=vocab_items,
                mastery_level='mastered'
            ).count()
            mastery['vocabulary'] = (mastered / total * 100) if total > 0 else 0
        
        # Comprehension
        comp_focuses = ChunkComprehensionFocus.objects.filter(chunk__in=chunks)
        if comp_focuses.exists():
            total = comp_focuses.count()
            mastered = ComprehensionTestAttempt.objects.filter(
                user=user,
                focus__in=comp_focuses,
                is_mastered=True
            ).values('focus').distinct().count()
            mastery['comprehension'] = (mastered / total * 100) if total > 0 else 0
        
        # Writing (chunk-level)
        writing_focuses = ChunkWritingFocus.objects.filter(chunk__in=chunks)
        if writing_focuses.exists():
            total = writing_focuses.count()
            mastered = WritingTestAttempt.objects.filter(
                user=user,
                focus__in=writing_focuses,
                is_mastered=True
            ).values('focus').distinct().count()
            mastery['writing'] = (mastered / total * 100) if total > 0 else 0
        
        # Pronunciation
        pron_focuses = PronunciationFocus.objects.filter(chunk__in=chunks)
        if pron_focuses.exists():
            total = pron_focuses.count()
            mastered = PronunciationMastery.objects.filter(
                user=user,
                focus__in=pron_focuses,
                is_mastered=True
            ).count()
            mastery['pronunciation'] = (mastered / total * 100) if total > 0 else 0
        
        return mastery
    
    def _get_unit_last_activity(self, user, unit):
        """Get most recent activity timestamp for a unit."""
        chunks = LessonChunk.objects.filter(lesson__unit=unit)
        
        timestamps = []
        
        # Grammar practice
        grammar_time = GrammarPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        if grammar_time:
            timestamps.append(grammar_time)
        
        # Punctuation practice
        punct_time = PunctuationPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if punct_time:
            timestamps.append(punct_time)
        
        # Vocabulary attempts
        vocab_time = VocabularyAttempt.objects.filter(
            user=user,
            vocab_item__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if vocab_time:
            timestamps.append(vocab_time)
        
        # Comprehension practice
        comp_time = ComprehensionPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        if comp_time:
            timestamps.append(comp_time)
        
        # Writing practice
        writing_time = WritingPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if writing_time:
            timestamps.append(writing_time)
        
        # Pronunciation attempts
        pron_time = PronunciationAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if pron_time:
            timestamps.append(pron_time)
        
        # Test sessions
        test_time = UnitTestSession.objects.filter(
            user=user,
            unit=unit
        ).order_by('-started_at').values_list('started_at', flat=True).first()
        if test_time:
            timestamps.append(test_time)
        
        if timestamps:
            return max(timestamps)
        return None


# ============================================================
# LESSON PROGRESS VIEWS
# ============================================================

class LessonProgressViewSet(viewsets.GenericViewSet):
    """
    ViewSet for lesson-level progress tracking.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def detail(self, request):
        """
        Get detailed progress for a specific lesson.
        """
        lesson_id = request.query_params.get('lesson_id')
        if not lesson_id:
            return Response(
                {'error': 'lesson_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lesson = get_object_or_404(Lesson, id=lesson_id)
        user = request.user
        
        # Get chunk progress
        chunks = lesson.chunks.all().order_by('order')
        chunk_progress = []
        
        for chunk in chunks:
            is_mastered = chunk.is_mastered_by(user)
            status = chunk.get_mastery_status(user)
            
            chunk_progress.append({
                'chunk_id': chunk.id,
                'order': chunk.order,
                'mastered': is_mastered,
                'next_domain': status.get('next_domain_to_work') if status else None,
                'estimated_time': chunk.estimated_time_minutes,
                'by_domain': status.get('by_domain') if status else {}
            })
        
        # Calculate overall progress
        total_chunks = chunks.count()
        mastered_chunks = sum(1 for c in chunk_progress if c['mastered'])
        
        # Get time spent
        time_spent = self._get_lesson_time_spent(user, lesson)
        
        # Get last activity
        last_activity = self._get_lesson_last_activity(user, lesson)
        
        data = {
            'lesson_id': lesson.id,
            'lesson_number': lesson.number,
            'lesson_title': lesson.title,
            'total_chunks': total_chunks,
            'mastered_chunks': mastered_chunks,
            'completion_percentage': (mastered_chunks / total_chunks * 100) if total_chunks > 0 else 0,
            'estimated_total_minutes': lesson.chunks.aggregate(total=Sum('estimated_time_minutes'))['total'] or 0,
            'time_spent_minutes': time_spent,
            'chunk_progress': chunk_progress,
            'last_activity': last_activity,
            'next_chunk': next(
                (c for c in chunk_progress if not c['mastered']),
                None
            )
        }
        
        return Response(data)
    
    def _get_lesson_time_spent(self, user, lesson):
        """Calculate total minutes spent on a lesson."""
        chunks = lesson.chunks.all()
        total_seconds = 0
        
        # Grammar practice time
        grammar_time = GrammarPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += grammar_time
        
        # Punctuation practice time
        punct_time = PunctuationPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += punct_time
        
        # Vocabulary time
        vocab_time = VocabularyAttempt.objects.filter(
            user=user,
            vocab_item__chunk__in=chunks
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += vocab_time
        
        # Comprehension time
        comp_time = ComprehensionPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += comp_time
        
        # Writing time
        writing_time = WritingPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).aggregate(total=Sum('time_spent_seconds'))['total'] or 0
        total_seconds += writing_time
        
        # Pronunciation time
        pron_time = PronunciationAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).aggregate(total=Sum('time_taken_seconds'))['total'] or 0
        total_seconds += pron_time
        
        return total_seconds // 60
    
    def _get_lesson_last_activity(self, user, lesson):
        """Get most recent activity timestamp for a lesson."""
        chunks = lesson.chunks.all()
        timestamps = []
        
        # Grammar practice
        grammar_time = GrammarPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        if grammar_time:
            timestamps.append(grammar_time)
        
        # Punctuation practice
        punct_time = PunctuationPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if punct_time:
            timestamps.append(punct_time)
        
        # Vocabulary attempts
        vocab_time = VocabularyAttempt.objects.filter(
            user=user,
            vocab_item__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if vocab_time:
            timestamps.append(vocab_time)
        
        # Comprehension practice
        comp_time = ComprehensionPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-attempted_at').values_list('attempted_at', flat=True).first()
        if comp_time:
            timestamps.append(comp_time)
        
        # Writing practice
        writing_time = WritingPracticeAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if writing_time:
            timestamps.append(writing_time)
        
        # Pronunciation attempts
        pron_time = PronunciationAttempt.objects.filter(
            user=user,
            focus__chunk__in=chunks
        ).order_by('-created_at').values_list('created_at', flat=True).first()
        if pron_time:
            timestamps.append(pron_time)
        
        if timestamps:
            return max(timestamps)
        return None


# ============================================================
# ANALYTICS VIEWS
# ============================================================

class AnalyticsViewSet(viewsets.GenericViewSet):
    """
    ViewSet for advanced analytics (teacher/admin only).
    """
    
    permission_classes = [IsAuthenticated]  # Add teacher/admin check
    
    @action(detail=False, methods=['get'])
    def class_overview(self, request):
        """
        Get overview of all students in a class.
        """
        # This would require class/group models
        # Placeholder for now
        return Response({
            'message': 'Class analytics not implemented'
        })
    
    @action(detail=False, methods=['get'])
    def domain_performance(self, request):
        """
        Get performance metrics by domain for all students.
        """
        # Aggregate across all users
        users = User.objects.filter(is_staff=False)
        
        domain_stats = {
            'grammar': {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
            'punctuation': {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
            'vocabulary': {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
            'comprehension': {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
            'writing': {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0},
            'pronunciation': {'total_attempts': 0, 'avg_score': 0, 'mastery_rate': 0}
        }
        
        # This would aggregate real data
        # Placeholder for now
        
        return Response(domain_stats)