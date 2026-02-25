# api_views/punctuation.py

"""
Punctuation domain views for practice, testing, and progress tracking.
Provides endpoints for punctuation mark learning and assessment.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import models, transaction
from django.db.models import Q, Prefetch, Count, Avg, Max
from django.utils import timezone
from django.shortcuts import get_object_or_404

from content.models.punctuation import (
    PunctuationMark, PunctuationRule, PunctuationExample,
    ChunkPunctuationFocus, ChunkPunctuationFocusRule,
    PunctuationPracticeAttempt, PunctuationTestAttempt,
    PunctuationQuestion
)
from content.models.core import LessonChunk
from content.serializers.punctuation import (
    # Knowledge layer
    PunctuationMarkSerializer, PunctuationMarkDetailSerializer,
    PunctuationRuleSerializer, PunctuationRuleDetailSerializer,
    PunctuationExampleSerializer,
    
    # Teaching layer
    ChunkPunctuationFocusSerializer, ChunkPunctuationFocusListSerializer,
    ChunkPunctuationFocusRuleSerializer,
    PunctuationQuestionSerializer,
    
    # Practice layer
    PunctuationPracticeAttemptSerializer, PunctuationPracticeAttemptSubmitSerializer,
    
    # Test layer
    PunctuationTestAttemptSerializer, PunctuationTestAttemptSubmitSerializer,
    
    # Progress tracking
    PunctuationMarkProgressSerializer, PunctuationFocusProgressSerializer,
    
    # Bulk operations
    PunctuationBulkQuestionCreateSerializer, PunctuationBulkFocusRuleCreateSerializer
)
from .base import (
    BaseViewSet, PracticeViewSet, TestViewSet, ProgressViewSet,
    UserFilterMixin, IsOwnerOrReadOnly, log_user_activity
)


# ============================================================
# KNOWLEDGE LAYER VIEWS
# ============================================================

class PunctuationMarkViewSet(BaseViewSet):
    """
    ViewSet for viewing punctuation marks (knowledge layer).
    
    Provides:
    - List all punctuation marks
    - Retrieve mark with rules and examples
    - Get marks in curriculum order
    """
    
    queryset = PunctuationMark.objects.all()
    serializer_class = PunctuationMarkSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'retrieve':
            return PunctuationMarkDetailSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Optimize queryset with prefetches.
        """
        queryset = super().get_queryset()
        
        # For detail view, prefetch rules and examples
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('rules', queryset=PunctuationRule.objects.all()),
                Prefetch('rules__examples', queryset=PunctuationExample.objects.all())
            )
        
        return queryset.order_by('order_index')
    
    @action(detail=True, methods=['get'])
    def rules(self, request, pk=None):
        """
        Get all rules for this punctuation mark.
        """
        mark = self.get_object()
        rules = mark.rules.all()
        serializer = PunctuationRuleSerializer(rules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def teaching_instances(self, request, pk=None):
        """
        Get all chunks where this punctuation mark is taught.
        """
        mark = self.get_object()
        focuses = ChunkPunctuationFocus.objects.filter(
            mark=mark
        ).select_related('chunk__lesson')
        
        data = [
            {
                'focus_id': f.id,
                'chunk_id': f.chunk.id,
                'lesson_id': f.chunk.lesson.id,
                'lesson_title': f.chunk.lesson.title,
                'focus_title': f.focus_title,
                'depth_level': f.depth_level
            }
            for f in focuses
        ]
        
        return Response(data)


class PunctuationRuleViewSet(BaseViewSet):
    """
    ViewSet for viewing punctuation rules.
    """
    
    queryset = PunctuationRule.objects.all()
    serializer_class = PunctuationRuleSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'retrieve':
            return PunctuationRuleDetailSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter by mark if provided.
        """
        queryset = super().get_queryset()
        
        mark_id = self.request.query_params.get('mark_id')
        if mark_id:
            queryset = queryset.filter(mark_id=mark_id)
        
        # For detail view, prefetch examples
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('examples')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def examples(self, request, pk=None):
        """
        Get all examples for this rule.
        """
        rule = self.get_object()
        examples = rule.examples.all()
        serializer = PunctuationExampleSerializer(examples, many=True)
        return Response(serializer.data)


class PunctuationExampleViewSet(BaseViewSet):
    """
    ViewSet for viewing punctuation examples.
    """
    
    queryset = PunctuationExample.objects.all()
    serializer_class = PunctuationExampleSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        """
        Filter by rule if provided.
        """
        queryset = super().get_queryset()
        
        rule_id = self.request.query_params.get('rule_id')
        if rule_id:
            queryset = queryset.filter(rule_id=rule_id)
        
        return queryset


# ============================================================
# TEACHING LAYER VIEWS
# ============================================================

class ChunkPunctuationFocusViewSet(BaseViewSet):
    """
    ViewSet for punctuation focuses within chunks.
    
    Provides:
    - List focuses for a chunk
    - Retrieve focus with questions and rules
    - Get practice/test statistics
    """
    
    queryset = ChunkPunctuationFocus.objects.all()
    serializer_class = ChunkPunctuationFocusSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list' and self.request.GET.get('simple') == 'true':
            return ChunkPunctuationFocusListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Optimize queryset with prefetches.
        """
        queryset = super().get_queryset()
        
        # Filter by chunk if provided
        chunk_id = self.request.query_params.get('chunk_id')
        if chunk_id:
            queryset = queryset.filter(chunk_id=chunk_id)
        
        # Filter by mark if provided
        mark_id = self.request.query_params.get('mark_id')
        if mark_id:
            queryset = queryset.filter(mark_id=mark_id)
        
        # For detail view, prefetch questions and rules
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('questions', queryset=PunctuationQuestion.objects.all()),
                Prefetch('focus_rules', queryset=ChunkPunctuationFocusRule.objects.select_related('rule'))
            )
        
        return queryset.order_by('sequence_order')
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """
        Get all questions for this focus.
        """
        focus = self.get_object()
        questions = focus.questions.all().order_by('id')
        serializer = PunctuationQuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rules(self, request, pk=None):
        """
        Get all rules linked to this focus.
        """
        focus = self.get_object()
        focus_rules = focus.focus_rules.all().order_by('order')
        serializer = ChunkPunctuationFocusRuleSerializer(focus_rules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get practice and test statistics for this focus.
        """
        focus = self.get_object()
        user = request.user
        
        # Practice stats
        practice_attempts = PunctuationPracticeAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-created_at')
        
        # Test stats
        test_attempts = PunctuationTestAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-created_at')
        
        stats = {
            'practice': {
                'total_attempts': practice_attempts.count(),
                'best_score': practice_attempts.aggregate(best=Max('score_percent'))['best'],
                'average_score': practice_attempts.aggregate(avg=Avg('score_percent'))['avg'],
                'last_attempt': PunctuationPracticeAttemptSerializer(practice_attempts.first()).data if practice_attempts.exists() else None
            },
            'test': {
                'total_attempts': test_attempts.count(),
                'best_score': test_attempts.aggregate(best=Max('score_percent'))['best'],
                'average_score': test_attempts.aggregate(avg=Avg('score_percent'))['avg'],
                'is_mastered': test_attempts.filter(is_mastered=True).exists(),
                'last_attempt': PunctuationTestAttemptSerializer(test_attempts.first()).data if test_attempts.exists() else None
            }
        }
        
        return Response(stats)


class ChunkPunctuationFocusRuleViewSet(BaseViewSet):
    """
    ViewSet for focus-rule mappings.
    """
    
    queryset = ChunkPunctuationFocusRule.objects.all()
    serializer_class = ChunkPunctuationFocusRuleSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        """
        Filter by focus if provided.
        """
        queryset = super().get_queryset()
        
        focus_id = self.request.query_params.get('focus_id')
        if focus_id:
            queryset = queryset.filter(focus_id=focus_id)
        
        return queryset.order_by('order')


class PunctuationQuestionViewSet(BaseViewSet):
    """
    ViewSet for punctuation questions.
    """
    
    queryset = PunctuationQuestion.objects.all()
    serializer_class = PunctuationQuestionSerializer
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

class PunctuationPracticeViewSet(PracticeViewSet):
    """
    ViewSet for punctuation practice attempts.
    
    Provides:
    - Submit practice attempt
    - List user's practice history
    - Get practice statistics
    """
    
    queryset = PunctuationPracticeAttempt.objects.all()
    serializer_class = PunctuationPracticeAttemptSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return PunctuationPracticeAttemptSubmitSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter to current user's attempts.
        """
        queryset = super().get_queryset()
        
        # Filter by focus if provided
        focus_id = self.request.query_params.get('focus_id')
        if focus_id:
            queryset = queryset.filter(focus_id=focus_id)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        if from_date:
            queryset = queryset.filter(created_at__gte=from_date)
        
        to_date = self.request.query_params.get('to_date')
        if to_date:
            queryset = queryset.filter(created_at__lte=to_date)
        
        return queryset
    
    @transaction.atomic
    def create_attempt(self, request, focus, answers_data, **kwargs):
        """
        Create a new punctuation practice attempt.
        """
        # Get the focus object
        focus_obj = get_object_or_404(ChunkPunctuationFocus, id=focus)
        
        # Get questions for this focus
        questions = list(focus_obj.questions.all())
        
        # Calculate score
        correct_count = 0
        
        for answer in answers_data:
            question_id = answer.get('question_id')
            selected = answer.get('selected_answer')
            
            try:
                question = next(q for q in questions if q.id == question_id)
                is_correct = (selected == question.correct_answer)
                
                if is_correct:
                    correct_count += 1
                
            except StopIteration:
                continue
        
        # Calculate score percentage
        total_questions = len(questions)
        score_percent = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
        
        # Create practice attempt
        attempt = PunctuationPracticeAttempt.objects.create(
            user=request.user,
            focus=focus_obj,
            attempt_number=kwargs.get('attempt_number'),
            cycle_number=kwargs.get('cycle_number'),
            score_percent=score_percent,
            is_passed=(score_percent == 100),
            questions_data={
                'answers': answers_data,
                'questions': [{'id': q.id, 'text': q.question_text} for q in questions]
            }
        )
        
        log_user_activity(
            request.user,
            'punctuation_practice_completed',
            {
                'focus_id': focus,
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
            'by_mark': []
        }
        
        # Group by punctuation mark
        focus_ids = attempts.values_list('focus', flat=True).distinct()
        for focus_id in focus_ids[:5]:  # Top 5 focuses
            focus_attempts = attempts.filter(focus_id=focus_id)
            focus = ChunkPunctuationFocus.objects.select_related('mark').get(id=focus_id)
            
            summary['by_mark'].append({
                'mark_id': focus.mark.id,
                'mark_symbol': focus.mark.symbol,
                'focus_id': focus_id,
                'focus_title': focus.focus_title,
                'attempts': focus_attempts.count(),
                'best_score': focus_attempts.aggregate(best=Max('score_percent'))['best'],
                'average_score': focus_attempts.aggregate(avg=Avg('score_percent'))['avg']
            })
        
        return Response(summary)


# ============================================================
# TEST VIEWS
# ============================================================

class PunctuationTestViewSet(TestViewSet):
    """
    ViewSet for punctuation test attempts.
    
    Provides:
    - Submit test attempt
    - List user's test history
    - Get mastery status
    """
    
    queryset = PunctuationTestAttempt.objects.all()
    serializer_class = PunctuationTestAttemptSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return PunctuationTestAttemptSubmitSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter to current user's attempts.
        """
        queryset = super().get_queryset()
        
        # Filter by focus if provided
        focus_id = self.request.query_params.get('focus_id')
        if focus_id:
            queryset = queryset.filter(focus_id=focus_id)
        
        # Filter by mastery status
        mastered = self.request.query_params.get('mastered')
        if mastered is not None:
            is_mastered = mastered.lower() == 'true'
            queryset = queryset.filter(is_mastered=is_mastered)
        
        return queryset
    
    @transaction.atomic
    def create_test_attempt(self, request, **kwargs):
        """
        Create a new punctuation test attempt.
        """
        focus_id = request.data.get('focus_id')
        answers_data = request.data.get('answers', [])
        
        # Get the focus object
        focus_obj = get_object_or_404(ChunkPunctuationFocus, id=focus_id)
        
        # Get questions for this focus
        questions = list(focus_obj.questions.all())
        
        # Calculate score
        correct_count = 0
        
        for answer in answers_data:
            question_id = answer.get('question_id')
            selected = answer.get('selected_answer')
            
            try:
                question = next(q for q in questions if q.id == question_id)
                is_correct = (selected == question.correct_answer)
                
                if is_correct:
                    correct_count += 1
                
            except StopIteration:
                continue
        
        # Calculate score percentage
        total_questions = len(questions)
        score_percent = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
        
        # Create test attempt
        attempt = PunctuationTestAttempt.objects.create(
            user=request.user,
            focus=focus_obj,
            attempt_number=kwargs.get('attempt_number'),
            cycle_number=kwargs.get('cycle_number'),
            score_percent=score_percent,
            correct_answers=correct_count,
            total_questions=total_questions,
            questions_data={
                'answers': answers_data,
                'questions': [{'id': q.id, 'text': q.question_text} for q in questions]
            }
        )
        
        log_user_activity(
            request.user,
            'punctuation_test_completed',
            {
                'focus_id': focus_id,
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
        Get mastery summary across all punctuation focuses.
        """
        user = request.user
        
        # Get all focuses
        all_focuses = ChunkPunctuationFocus.objects.all()
        
        # Get mastered focuses
        mastered_focuses = self.get_queryset().filter(
            is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        
        # Get in-progress focuses
        attempted_focuses = self.get_queryset().values_list('focus_id', flat=True).distinct()
        in_progress = set(attempted_focuses) - set(mastered_focuses)
        
        # Group by punctuation mark
        by_mark = []
        marks = PunctuationMark.objects.all()
        
        for mark in marks:
            mark_focuses = all_focuses.filter(mark=mark)
            mark_mastered = mastered_focuses.filter(focus__mark=mark).count() if hasattr(mastered_focuses, 'filter') else 0
            
            by_mark.append({
                'mark_id': mark.id,
                'mark_symbol': mark.symbol,
                'mark_name': mark.name,
                'total_focuses': mark_focuses.count(),
                'mastered_count': mark_mastered,
                'mastery_percentage': (mark_mastered / mark_focuses.count() * 100) if mark_focuses.exists() else 0
            })
        
        summary = {
            'total_focuses': all_focuses.count(),
            'mastered_count': len(mastered_focuses),
            'in_progress_count': len(in_progress),
            'not_started_count': all_focuses.count() - len(attempted_focuses),
            'mastery_percentage': (len(mastered_focuses) / all_focuses.count() * 100) if all_focuses.exists() else 0,
            'by_mark': by_mark,
            'recently_mastered': []
        }
        
        # Get recently mastered (last 7 days)
        recent = self.get_queryset().filter(
            is_mastered=True,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('focus', 'focus__mark')[:5]
        
        for attempt in recent:
            summary['recently_mastered'].append({
                'focus_id': attempt.focus_id,
                'focus_title': attempt.focus.focus_title,
                'mark_symbol': attempt.focus.mark.symbol,
                'mastered_at': attempt.created_at,
                'score': attempt.score_percent
            })
        
        return Response(summary)


# ============================================================
# PROGRESS VIEWS
# ============================================================

class PunctuationProgressViewSet(ProgressViewSet):
    """
    ViewSet for punctuation progress tracking.
    """
    
    serializer_class = PunctuationMarkProgressSerializer
    
    def get_user_progress(self, user):
        """
        Get punctuation progress for user.
        """
        # Get all marks
        marks = PunctuationMark.objects.all().order_by('order_index')
        
        progress_data = []
        
        for mark in marks:
            # Get focuses for this mark
            focuses = ChunkPunctuationFocus.objects.filter(mark=mark)
            
            # Calculate practice stats
            practice_attempts = PunctuationPracticeAttempt.objects.filter(
                user=user,
                focus__in=focuses
            )
            
            # Calculate test stats
            test_attempts = PunctuationTestAttempt.objects.filter(
                user=user,
                focus__in=focuses
            )
            
            # Calculate mastery
            mastered_focuses = test_attempts.filter(
                is_mastered=True
            ).values_list('focus_id', flat=True).distinct()
            
            total_focuses = focuses.count()
            mastered_count = len(mastered_focuses)
            
            # Last attempted
            last_practice = practice_attempts.order_by('-created_at').first()
            last_test = test_attempts.order_by('-created_at').first()
            
            last_attempted = None
            if last_practice and last_test:
                last_attempted = max(last_practice.created_at, last_test.created_at)
            elif last_practice:
                last_attempted = last_practice.created_at
            elif last_test:
                last_attempted = last_test.created_at
            
            progress_data.append({
                'mark_id': mark.id,
                'mark_symbol': mark.symbol,
                'mark_name': mark.name,
                'total_focuses': total_focuses,
                'mastered_focuses': mastered_count,
                'in_progress_focuses': practice_attempts.values_list('focus', flat=True).distinct().count() - mastered_count,
                'not_started_focuses': total_focuses - practice_attempts.values_list('focus', flat=True).distinct().count(),
                'mastery_percentage': (mastered_count / total_focuses * 100) if total_focuses > 0 else 0,
                'practice_attempts': practice_attempts.count(),
                'average_practice_score': practice_attempts.aggregate(avg=Avg('score_percent'))['avg'],
                'test_attempts': test_attempts.count(),
                'average_test_score': test_attempts.aggregate(avg=Avg('score_percent'))['avg'],
                'last_activity': last_attempted
            })
        
        return progress_data
    
    @action(detail=False, methods=['get'])
    def focus_progress(self, request):
        """
        Get progress for specific punctuation focuses.
        """
        user = request.user
        focus_ids = request.query_params.getlist('focus_ids')
        
        if not focus_ids:
            return Response(
                {'error': 'focus_ids parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        focuses = ChunkPunctuationFocus.objects.filter(id__in=focus_ids).select_related('mark')
        progress_data = []
        
        for focus in focuses:
            # Practice tracking
            practice_attempts = PunctuationPracticeAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-cycle_number', '-attempt_number')
            
            latest_practice = practice_attempts.first()
            
            # Test tracking
            test_attempts = PunctuationTestAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-cycle_number', '-attempt_number')
            
            latest_test = test_attempts.first()
            
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
                'mark_symbol': focus.mark.symbol,
                'depth_level': focus.depth_level,
                'current_practice_cycle': latest_practice.cycle_number if latest_practice else 1,
                'current_practice_attempt': latest_practice.attempt_number if latest_practice else 0,
                'practice_passed_in_cycle': latest_practice.is_passed if latest_practice else False,
                'practice_attempts_remaining': 3 - (latest_practice.attempt_number if latest_practice else 0),
                'current_test_cycle': latest_test.cycle_number if latest_test else 1,
                'current_test_attempt': latest_test.attempt_number if latest_test else 0,
                'is_mastered': latest_test.is_mastered if latest_test else False,
                'test_attempts_remaining': 3 - (latest_test.attempt_number if latest_test else 0),
                'next_action': next_action
            })
        
        return Response(progress_data)


# ============================================================
# BULK OPERATION VIEWS
# ============================================================

class PunctuationBulkOperationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for bulk operations on punctuation data.
    Admin-only endpoints for content management.
    """
    
    permission_classes = [IsAuthenticated]  # Add admin check
    
    @action(detail=False, methods=['post'])
    def create_questions(self, request):
        """
        Bulk create punctuation questions for a focus.
        """
        serializer = PunctuationBulkQuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        focus_id = serializer.validated_data['focus_id']
        questions_data = serializer.validated_data['questions']
        
        focus = get_object_or_404(ChunkPunctuationFocus, id=focus_id)
        
        created_questions = []
        with transaction.atomic():
            for q_data in questions_data:
                # Handle pipe-separated options
                options = q_data.get('options', '')
                if isinstance(options, list):
                    options = ' | '.join(options)
                
                question = PunctuationQuestion.objects.create(
                    focus=focus,
                    question_text=q_data['question_text'],
                    options=options,
                    correct_answer=q_data['correct_answer'],
                    question_type=q_data.get('question_type', 'mcq'),
                    difficulty=q_data.get('difficulty', 3),
                    explanation=q_data.get('explanation', '')
                )
                created_questions.append(question.id)
        
        log_user_activity(
            request.user,
            'bulk_create_punctuation_questions',
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
    
    @action(detail=False, methods=['post'])
    def link_rules(self, request):
        """
        Bulk link rules to a focus.
        """
        serializer = PunctuationBulkFocusRuleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        focus_id = serializer.validated_data['focus_id']
        rule_ids = serializer.validated_data['rule_ids']
        
        focus = get_object_or_404(ChunkPunctuationFocus, id=focus_id)
        
        created_links = []
        with transaction.atomic():
            # Delete existing links
            ChunkPunctuationFocusRule.objects.filter(focus=focus).delete()
            
            # Create new links
            for order, rule_id in enumerate(rule_ids, start=1):
                rule = get_object_or_404(PunctuationRule, id=rule_id)
                link = ChunkPunctuationFocusRule.objects.create(
                    focus=focus,
                    rule=rule,
                    order=order
                )
                created_links.append(link.id)
        
        log_user_activity(
            request.user,
            'bulk_link_punctuation_rules',
            {
                'focus_id': focus_id,
                'rule_count': len(rule_ids)
            }
        )
        
        return Response({
            'success': True,
            'message': f'Linked {len(created_links)} rules to focus',
            'link_ids': created_links
        }, status=status.HTTP_201_CREATED)