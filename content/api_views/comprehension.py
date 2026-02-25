# api_views/comprehension.py

"""
Comprehension domain views for practice, testing, and progress tracking.
Provides endpoints for comprehension learning with Bloom's taxonomy levels.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import models, transaction
from django.db.models import Q, Prefetch, Count, Avg, Max
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from content.models.comprehension import (
    ChunkComprehensionFocus, ComprehensionQuestion,
    ComprehensionPracticeAttempt, ComprehensionTestAttempt,
    ComprehensionQuestionAttempt, BloomLevel
)
from content.models.core import LessonChunk
from content.serializers.comprehension import (
    # Teaching layer
    ChunkComprehensionFocusSerializer, ChunkComprehensionFocusListSerializer,
    ComprehensionQuestionSerializer,
    
    # Practice layer
    ComprehensionPracticeAttemptSerializer, ComprehensionPracticeAttemptSubmitSerializer,
    
    # Test layer
    ComprehensionTestAttemptSerializer, ComprehensionTestAttemptSubmitSerializer,
    
    # Question attempts
    ComprehensionQuestionAttemptSerializer, ComprehensionQuestionAttemptDetailSerializer,
    
    # Progress tracking
    ComprehensionBloomLevelProgressSerializer, ComprehensionFocusProgressSerializer,
    
    # Bulk operations
    ComprehensionBulkQuestionCreateSerializer
)
from .base import (
    BaseViewSet, PracticeViewSet, TestViewSet, ProgressViewSet,
    UserFilterMixin, IsOwnerOrReadOnly, log_user_activity
)


# ============================================================
# TEACHING LAYER VIEWS
# ============================================================

class ChunkComprehensionFocusViewSet(BaseViewSet):
    """
    ViewSet for comprehension focuses within chunks.
    
    Provides:
    - List focuses for a chunk
    - Retrieve focus with questions
    - Filter by Bloom's level
    - Get practice/test statistics
    """
    
    queryset = ChunkComprehensionFocus.objects.all()
    serializer_class = ChunkComprehensionFocusSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'list' and self.request.GET.get('simple') == 'true':
            return ChunkComprehensionFocusListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Optimize queryset with filters and prefetches.
        """
        queryset = super().get_queryset()
        
        # Filter by chunk
        chunk_id = self.request.query_params.get('chunk_id')
        if chunk_id:
            queryset = queryset.filter(chunk_id=chunk_id)
        
        # Filter by Bloom's level
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        # Filter by depth level
        depth = self.request.query_params.get('depth')
        if depth:
            queryset = queryset.filter(depth_level=depth)
        
        # For detail view, prefetch questions
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('questions', queryset=ComprehensionQuestion.objects.all())
            )
        
        return queryset.order_by('sequence_order')
    
    @action(detail=False, methods=['get'])
    def bloom_levels(self, request):
        """
        Get all Bloom's taxonomy levels with counts.
        """
        levels = []
        for level_code, level_name in BloomLevel.choices:
            count = self.get_queryset().filter(level=level_code).count()
            levels.append({
                'code': level_code,
                'name': level_name,
                'count': count
            })
        return Response(levels)
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """
        Get all questions for this focus.
        """
        focus = self.get_object()
        questions = focus.questions.all().order_by('id')
        serializer = ComprehensionQuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get practice and test statistics for this focus.
        """
        focus = self.get_object()
        user = request.user
        
        # Practice stats
        practice_attempts = ComprehensionPracticeAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-attempted_at')
        
        # Test stats
        test_attempts = ComprehensionTestAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-created_at')
        
        stats = {
            'practice': {
                'total_attempts': practice_attempts.count(),
                'best_score': practice_attempts.aggregate(best=Max('score_percent'))['best'],
                'average_score': practice_attempts.aggregate(avg=Avg('score_percent'))['avg'],
                'last_attempt': ComprehensionPracticeAttemptSerializer(practice_attempts.first()).data if practice_attempts.exists() else None
            },
            'test': {
                'total_attempts': test_attempts.count(),
                'best_score': test_attempts.aggregate(best=Max('score_percent'))['best'],
                'average_score': test_attempts.aggregate(avg=Avg('score_percent'))['avg'],
                'is_mastered': test_attempts.filter(is_mastered=True).exists(),
                'last_attempt': ComprehensionTestAttemptSerializer(test_attempts.first()).data if test_attempts.exists() else None
            }
        }
        
        return Response(stats)


class ComprehensionQuestionViewSet(BaseViewSet):
    """
    ViewSet for comprehension questions.
    """
    
    queryset = ComprehensionQuestion.objects.all()
    serializer_class = ComprehensionQuestionSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        """
        Filter by focus, type, or difficulty.
        """
        queryset = super().get_queryset()
        
        focus_id = self.request.query_params.get('focus_id')
        if focus_id:
            queryset = queryset.filter(focus_id=focus_id)
        
        question_type = self.request.query_params.get('type')
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        return queryset


# ============================================================
# PRACTICE VIEWS
# ============================================================

class ComprehensionPracticeViewSet(PracticeViewSet):
    """
    ViewSet for comprehension practice attempts.
    
    Provides:
    - Submit practice attempt
    - List user's practice history
    - Get practice statistics by Bloom's level
    """
    
    queryset = ComprehensionPracticeAttempt.objects.all()
    serializer_class = ComprehensionPracticeAttemptSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return ComprehensionPracticeAttemptSubmitSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter to current user's attempts.
        """
        queryset = super().get_queryset()
        
        # Filter by focus
        focus_id = self.request.query_params.get('focus_id')
        if focus_id:
            queryset = queryset.filter(focus_id=focus_id)
        
        # Filter by Bloom's level (via focus)
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(focus__level=level)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        if from_date:
            queryset = queryset.filter(attempted_at__gte=from_date)
        
        to_date = self.request.query_params.get('to_date')
        if to_date:
            queryset = queryset.filter(attempted_at__lte=to_date)
        
        return queryset.select_related('focus')
    
    @transaction.atomic
    def create_attempt(self, request, focus, answers_data, **kwargs):
        """
        Create a new comprehension practice attempt.
        """
        # Get the focus object
        focus_obj = get_object_or_404(ChunkComprehensionFocus, id=focus)
        
        # Get questions for this focus
        questions = list(focus_obj.questions.all())
        
        # Calculate score
        correct_count = 0
        question_attempts = []
        
        for answer in answers_data:
            question_id = answer.get('question_id')
            selected = answer.get('selected_answer')
            open_ended = answer.get('open_ended_answer')
            
            try:
                question = next(q for q in questions if q.id == question_id)
                
                # Handle different question types
                is_correct = False
                if question.question_type == ComprehensionQuestion.TYPE_OPEN_ENDED:
                    # Open-ended questions don't have automatic scoring
                    is_correct = None  # Will be scored by teacher/AI later
                else:
                    is_correct = (selected == question.correct_answer)
                
                if is_correct:
                    correct_count += 1
                
                # Record question attempt
                question_attempt = ComprehensionQuestionAttempt.objects.create(
                    user=request.user,
                    question=question,
                    practice_attempt=None,  # Will update after practice attempt created
                    cycle_number=kwargs.get('cycle_number', 1),
                    attempt_number=kwargs.get('attempt_number', 1),
                    selected_answer=selected or '',
                    open_ended_answer=open_ended,
                    is_correct=is_correct if is_correct is not None else False,
                    time_taken_seconds=answer.get('time_taken_seconds')
                )
                question_attempts.append(question_attempt)
                
            except StopIteration:
                continue
        
        # Calculate score percentage (excluding open-ended from automatic scoring)
        scored_questions = [q for q in questions 
                           if q.question_type != ComprehensionQuestion.TYPE_OPEN_ENDED]
        total_scored = len(scored_questions)
        score_percent = int((correct_count / total_scored) * 100) if total_scored > 0 else 0
        
        # Create practice attempt
        attempt = ComprehensionPracticeAttempt.objects.create(
            user=request.user,
            focus=focus_obj,
            attempt_number=kwargs.get('attempt_number'),
            cycle_number=kwargs.get('cycle_number'),
            score_percent=score_percent,
            correct_answers=correct_count,
            total_questions=len(questions),
            questions_data={
                'answers': answers_data,
                'questions': [{'id': q.id, 'text': q.question_text, 'type': q.question_type} 
                            for q in questions]
            }
        )
        
        # Update question attempts with practice attempt reference
        for qa in question_attempts:
            qa.practice_attempt = attempt
            qa.save()
        
        log_user_activity(
            request.user,
            'comprehension_practice_completed',
            {
                'focus_id': focus,
                'level': focus_obj.level,
                'score': score_percent,
                'attempt_number': kwargs.get('attempt_number'),
                'cycle_number': kwargs.get('cycle_number')
            }
        )
        
        return attempt
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get practice summary statistics.
        """
        user = request.user
        attempts = self.get_queryset()
        
        summary = {
            'total_attempts': attempts.count(),
            'average_score': attempts.aggregate(avg=Avg('score_percent'))['avg'],
            'passed_attempts': attempts.filter(is_passed=True).count(),
            'by_bloom_level': []
        }
        
        # Group by Bloom's level
        for level_code, level_name in BloomLevel.choices:
            level_attempts = attempts.filter(focus__level=level_code)
            if level_attempts.exists():
                summary['by_bloom_level'].append({
                    'level': level_code,
                    'name': level_name,
                    'attempts': level_attempts.count(),
                    'average_score': level_attempts.aggregate(avg=Avg('score_percent'))['avg']
                })
        
        return Response(summary)
    
    @action(detail=True, methods=['get'])
    def question_attempts(self, request, pk=None):
        """
        Get all question attempts for a practice attempt.
        """
        attempt = self.get_object()
        question_attempts = attempt.question_attempts.all()
        serializer = ComprehensionQuestionAttemptSerializer(question_attempts, many=True)
        return Response(serializer.data)


# ============================================================
# TEST VIEWS
# ============================================================

class ComprehensionTestViewSet(TestViewSet):
    """
    ViewSet for comprehension test attempts.
    
    Provides:
    - Submit test attempt
    - List user's test history
    - Get mastery status by Bloom's level
    """
    
    queryset = ComprehensionTestAttempt.objects.all()
    serializer_class = ComprehensionTestAttemptSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return ComprehensionTestAttemptSubmitSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter to current user's attempts.
        """
        queryset = super().get_queryset()
        
        # Filter by focus
        focus_id = self.request.query_params.get('focus_id')
        if focus_id:
            queryset = queryset.filter(focus_id=focus_id)
        
        # Filter by Bloom's level
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(focus__level=level)
        
        # Filter by mastery status
        mastered = self.request.query_params.get('mastered')
        if mastered is not None:
            is_mastered = mastered.lower() == 'true'
            queryset = queryset.filter(is_mastered=is_mastered)
        
        return queryset.select_related('focus')
    
    @transaction.atomic
    def create_test_attempt(self, request, **kwargs):
        """
        Create a new comprehension test attempt.
        """
        focus_id = request.data.get('focus_id')
        answers_data = request.data.get('answers', [])
        
        # Get the focus object
        focus_obj = get_object_or_404(ChunkComprehensionFocus, id=focus_id)
        
        # Get questions for this focus
        questions = list(focus_obj.questions.all())
        
        # Calculate score
        correct_count = 0
        question_attempts = []
        
        for answer in answers_data:
            question_id = answer.get('question_id')
            selected = answer.get('selected_answer')
            open_ended = answer.get('open_ended_answer')
            
            try:
                question = next(q for q in questions if q.id == question_id)
                
                # Handle different question types
                is_correct = False
                if question.question_type == ComprehensionQuestion.TYPE_OPEN_ENDED:
                    # Open-ended questions will be scored by teacher/AI later
                    is_correct = None
                else:
                    is_correct = (selected == question.correct_answer)
                
                if is_correct:
                    correct_count += 1
                
                # Record question attempt
                question_attempt = ComprehensionQuestionAttempt.objects.create(
                    user=request.user,
                    question=question,
                    test_attempt=None,  # Will update after test attempt created
                    cycle_number=kwargs.get('cycle_number', 1),
                    attempt_number=kwargs.get('attempt_number', 1),
                    selected_answer=selected or '',
                    open_ended_answer=open_ended,
                    is_correct=is_correct if is_correct is not None else False,
                    time_taken_seconds=answer.get('time_taken_seconds')
                )
                question_attempts.append(question_attempt)
                
            except StopIteration:
                continue
        
        # Calculate score percentage (excluding open-ended from automatic scoring)
        scored_questions = [q for q in questions 
                           if q.question_type != ComprehensionQuestion.TYPE_OPEN_ENDED]
        total_scored = len(scored_questions)
        score_percent = int((correct_count / total_scored) * 100) if total_scored > 0 else 0
        
        # Create test attempt
        attempt = ComprehensionTestAttempt.objects.create(
            user=request.user,
            focus=focus_obj,
            attempt_number=kwargs.get('attempt_number'),
            cycle_number=kwargs.get('cycle_number'),
            score_percent=score_percent,
            correct_answers=correct_count,
            total_questions=len(questions),
            questions_data={
                'answers': answers_data,
                'questions': [{'id': q.id, 'text': q.question_text, 'type': q.question_type} 
                            for q in questions]
            }
        )
        
        # Update question attempts with test attempt reference
        for qa in question_attempts:
            qa.test_attempt = attempt
            qa.save()
        
        log_user_activity(
            request.user,
            'comprehension_test_completed',
            {
                'focus_id': focus_id,
                'level': focus_obj.level,
                'score': score_percent,
                'mastered': attempt.is_mastered,
                'attempt_number': kwargs.get('attempt_number'),
                'cycle_number': kwargs.get('cycle_number')
            }
        )
        
        return attempt
    
    @action(detail=False, methods=['get'])
    def mastery_summary(self, request):
        """
        Get mastery summary across Bloom's levels.
        """
        user = request.user
        
        # Get all focuses
        all_focuses = ChunkComprehensionFocus.objects.all()
        
        # Get mastered focuses
        mastered_focuses = self.get_queryset().filter(
            is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        
        summary = {
            'total_focuses': all_focuses.count(),
            'mastered_count': len(mastered_focuses),
            'mastery_percentage': (len(mastered_focuses) / all_focuses.count() * 100) if all_focuses.exists() else 0,
            'by_bloom_level': [],
            'recently_mastered': []
        }
        
        # Breakdown by Bloom's level
        for level_code, level_name in BloomLevel.choices:
            level_focuses = all_focuses.filter(level=level_code)
            level_mastered = mastered_focuses.filter(focus__level=level_code).count() if hasattr(mastered_focuses, 'filter') else 0
            
            summary['by_bloom_level'].append({
                'level': level_code,
                'name': level_name,
                'total_focuses': level_focuses.count(),
                'mastered_count': level_mastered,
                'mastery_percentage': (level_mastered / level_focuses.count() * 100) if level_focuses.exists() else 0
            })
        
        # Get recently mastered (last 7 days)
        recent = self.get_queryset().filter(
            is_mastered=True,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('focus')[:5]
        
        for attempt in recent:
            summary['recently_mastered'].append({
                'focus_id': attempt.focus_id,
                'focus_title': attempt.focus.focus_title,
                'level': attempt.focus.level,
                'mastered_at': attempt.created_at,
                'score': attempt.score_percent
            })
        
        return Response(summary)
    
    @action(detail=True, methods=['get'])
    def question_attempts(self, request, pk=None):
        """
        Get all question attempts for a test attempt.
        """
        attempt = self.get_object()
        question_attempts = attempt.question_attempts.all()
        serializer = ComprehensionQuestionAttemptDetailSerializer(question_attempts, many=True)
        return Response(serializer.data)


# ============================================================
# QUESTION ATTEMPT VIEWS
# ============================================================

class ComprehensionQuestionAttemptViewSet(BaseViewSet, UserFilterMixin):
    """
    ViewSet for comprehension question attempts (analytics).
    """
    
    queryset = ComprehensionQuestionAttempt.objects.all()
    serializer_class = ComprehensionQuestionAttemptSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """
        Return detailed serializer for retrieve action.
        """
        if self.action == 'retrieve':
            return ComprehensionQuestionAttemptDetailSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter by various parameters for analytics.
        """
        queryset = super().get_queryset()
        
        # Filter by question
        question_id = self.request.query_params.get('question_id')
        if question_id:
            queryset = queryset.filter(question_id=question_id)
        
        # Filter by Bloom's level (via question's focus)
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(question__focus__level=level)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        if from_date:
            queryset = queryset.filter(attempted_at__gte=from_date)
        
        to_date = self.request.query_params.get('to_date')
        if to_date:
            queryset = queryset.filter(attempted_at__lte=to_date)
        
        # Filter by correctness
        correct = self.request.query_params.get('correct')
        if correct is not None:
            is_correct = correct.lower() == 'true'
            queryset = queryset.filter(is_correct=is_correct)
        
        return queryset.select_related('question', 'question__focus')
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get analytics for question attempts.
        """
        queryset = self.get_queryset()
        
        total = queryset.count()
        correct = queryset.filter(is_correct=True).count()
        
        analytics = {
            'total_attempts': total,
            'correct_attempts': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0,
            'average_time': queryset.aggregate(avg=Avg('time_taken_seconds'))['avg'],
            'by_bloom_level': [],
            'by_question_type': []
        }
        
        # Group by Bloom's level
        for level_code, level_name in BloomLevel.choices:
            level_attempts = queryset.filter(question__focus__level=level_code)
            if level_attempts.exists():
                level_correct = level_attempts.filter(is_correct=True).count()
                analytics['by_bloom_level'].append({
                    'level': level_code,
                    'name': level_name,
                    'total_attempts': level_attempts.count(),
                    'correct_attempts': level_correct,
                    'accuracy': (level_correct / level_attempts.count() * 100)
                })
        
        # Group by question type
        question_types = dict(ComprehensionQuestion.QUESTION_TYPES)
        for type_code, type_name in question_types.items():
            type_attempts = queryset.filter(question__question_type=type_code)
            if type_attempts.exists():
                type_correct = type_attempts.filter(is_correct=True).count()
                analytics['by_question_type'].append({
                    'type': type_code,
                    'name': type_name,
                    'total_attempts': type_attempts.count(),
                    'correct_attempts': type_correct,
                    'accuracy': (type_correct / type_attempts.count() * 100)
                })
        
        return Response(analytics)


# ============================================================
# PROGRESS VIEWS
# ============================================================

class ComprehensionProgressViewSet(ProgressViewSet):
    """
    ViewSet for comprehension progress tracking.
    """
    
    serializer_class = ComprehensionBloomLevelProgressSerializer
    
    def get_user_progress(self, user):
        """
        Get comprehension progress for user.
        """
        # Get all focuses grouped by Bloom's level
        progress_data = []
        
        for level_code, level_name in BloomLevel.choices:
            # Focuses at this level
            focuses = ChunkComprehensionFocus.objects.filter(level=level_code)
            total_focuses = focuses.count()
            
            # Practice attempts at this level
            practice_attempts = ComprehensionPracticeAttempt.objects.filter(
                user=user,
                focus__in=focuses
            )
            
            # Test attempts at this level
            test_attempts = ComprehensionTestAttempt.objects.filter(
                user=user,
                focus__in=focuses
            )
            
            # Mastered focuses at this level
            mastered_focuses = test_attempts.filter(
                is_mastered=True
            ).values_list('focus_id', flat=True).distinct()
            mastered_count = len(mastered_focuses)
            
            # In-progress focuses (attempted but not mastered)
            attempted_focuses = test_attempts.values_list('focus_id', flat=True).distinct()
            in_progress_count = len(set(attempted_focuses) - set(mastered_focuses))
            
            # Not started
            not_started_count = total_focuses - len(attempted_focuses)
            
            progress_data.append({
                'level': level_code,
                'level_display': level_name,
                'total_focuses': total_focuses,
                'mastered_focuses': mastered_count,
                'in_progress_focuses': in_progress_count,
                'not_started_focuses': not_started_count,
                'mastery_percentage': (mastered_count / total_focuses * 100) if total_focuses > 0 else 0,
                'practice_attempts': practice_attempts.count(),
                'average_practice_score': practice_attempts.aggregate(avg=Avg('score_percent'))['avg'],
                'test_attempts': test_attempts.count(),
                'average_test_score': test_attempts.aggregate(avg=Avg('score_percent'))['avg']
            })
        
        return progress_data
    
    @action(detail=False, methods=['get'])
    def focus_progress(self, request):
        """
        Get progress for specific comprehension focuses.
        """
        user = request.user
        focus_ids = request.query_params.getlist('focus_ids')
        
        if not focus_ids:
            return Response(
                {'error': 'focus_ids parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        focuses = ChunkComprehensionFocus.objects.filter(id__in=focus_ids)
        progress_data = []
        
        for focus in focuses:
            # Practice tracking
            practice_attempts = ComprehensionPracticeAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-cycle_number', '-attempt_number')
            
            latest_practice = practice_attempts.first()
            
            # Test tracking
            test_attempts = ComprehensionTestAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-cycle_number', '-attempt_number')
            
            latest_test = test_attempts.first()
            
            # Question-level analytics
            question_attempts = ComprehensionQuestionAttempt.objects.filter(
                user=user,
                question__focus=focus
            )
            
            questions_correct = {}
            questions_incorrect = {}
            
            for qa in question_attempts:
                qid = qa.question_id
                if qa.is_correct:
                    questions_correct[qid] = questions_correct.get(qid, 0) + 1
                else:
                    questions_incorrect[qid] = questions_incorrect.get(qid, 0) + 1
            
            # Determine next action
            next_action = 'practice'
            if latest_test and latest_test.is_mastered:
                next_action = 'mastered'
            elif latest_practice and latest_practice.is_passed:
                next_action = 'test'
            elif not latest_practice:
                next_action = 'practice'
            
            progress_data.append({
                'focus_id': focus.id,
                'focus_title': focus.focus_title,
                'level': focus.level,
                'depth_level': focus.depth_level,
                'current_practice_cycle': latest_practice.cycle_number if latest_practice else 1,
                'current_practice_attempt': latest_practice.attempt_number if latest_practice else 0,
                'practice_passed_in_cycle': latest_practice.is_passed if latest_practice else False,
                'practice_attempts_remaining': 3 - (latest_practice.attempt_number if latest_practice else 0),
                'current_test_cycle': latest_test.cycle_number if latest_test else 1,
                'current_test_attempt': latest_test.attempt_number if latest_test else 0,
                'is_mastered': latest_test.is_mastered if latest_test else False,
                'test_attempts_remaining': 3 - (latest_test.attempt_number if latest_test else 0),
                'questions_correct': questions_correct,
                'questions_incorrect': questions_incorrect,
                'next_action': next_action
            })
        
        return Response(progress_data)


# ============================================================
# BULK OPERATION VIEWS
# ============================================================

class ComprehensionBulkOperationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for bulk operations on comprehension data.
    Admin-only endpoints for content management.
    """
    
    permission_classes = [IsAuthenticated]  # Add admin check
    
    @action(detail=False, methods=['post'])
    def create_questions(self, request):
        """
        Bulk create comprehension questions for a focus.
        """
        serializer = ComprehensionBulkQuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        focus_id = serializer.validated_data['focus_id']
        questions_data = serializer.validated_data['questions']
        
        focus = get_object_or_404(ChunkComprehensionFocus, id=focus_id)
        
        created_questions = []
        with transaction.atomic():
            for q_data in questions_data:
                # Handle options (can be list or pipe-separated string)
                options = q_data.get('options', '')
                if isinstance(options, list):
                    options = '\n'.join(options)
                
                question = ComprehensionQuestion.objects.create(
                    focus=focus,
                    question_text=q_data['question_text'],
                    options=options,
                    correct_answer=q_data.get('correct_answer', ''),
                    question_type=q_data.get('question_type', 'mcq'),
                    difficulty=q_data.get('difficulty', 3),
                    explanation=q_data.get('explanation', '')
                )
                created_questions.append(question.id)
        
        log_user_activity(
            request.user,
            'bulk_create_comprehension_questions',
            {
                'focus_id': focus_id,
                'count': len(created_questions)
            }
        )
        
        return Response({
            'success': True,
            'message': f'Created {len(created_questions)} questions',
            'question_ids': created_questions
        }, status=status.HTTP_201_CREATED)