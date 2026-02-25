# api_views/grammar.py

"""
Grammar domain views for practice, testing, and progress tracking.
Provides endpoints for grammar concept learning and assessment.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import models, transaction
from django.db.models import Q, Prefetch, Count, Avg, Max
from django.utils import timezone
from django.shortcuts import get_object_or_404

from content.models.grammar import (
    GrammarConcept, GrammarRule, GrammarExample,
    ChunkGrammarFocus, GrammarQuestion,
    GrammarPracticeAttempt, GrammarTestAttempt,
    GrammarQuestionAttempt
)
from content.models.core import LessonChunk
from content.serializers.grammar import (
    # Knowledge layer
    GrammarConceptSerializer, GrammarConceptListSerializer,
    GrammarRuleSerializer, GrammarExampleSerializer,
    
    # Teaching layer
    ChunkGrammarFocusSerializer, ChunkGrammarFocusListSerializer,
    GrammarQuestionSerializer,
    
    # Practice layer
    GrammarPracticeAttemptSerializer, GrammarPracticeAttemptSubmitSerializer,
    
    # Test layer
    GrammarTestAttemptSerializer, GrammarTestAttemptSubmitSerializer,
    
    # Question attempts
    GrammarQuestionAttemptSerializer, GrammarQuestionAttemptDetailSerializer,
    
    # Progress tracking
    GrammarConceptProgressSerializer, GrammarFocusProgressSerializer,
    
    # Bulk operations
    GrammarBulkQuestionCreateSerializer
)
from .base import (
    BaseViewSet, PracticeViewSet, TestViewSet, ProgressViewSet,
    UserFilterMixin, IsOwnerOrReadOnly, log_user_activity
)


# ============================================================
# KNOWLEDGE LAYER VIEWS
# ============================================================

class GrammarConceptViewSet(BaseViewSet):
    """
    ViewSet for viewing grammar concepts (knowledge layer).
    
    Provides:
    - List all grammar concepts
    - Retrieve concept with rules and examples
    - Get concepts by category
    - Get concept progression order
    """
    
    queryset = GrammarConcept.objects.all()
    serializer_class = GrammarConceptSerializer
    lookup_field = 'pk'
    lookup_fields = ['pk', 'slug']  # Allow lookup by slug
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return GrammarConceptListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Optimize queryset with prefetches.
        """
        queryset = super().get_queryset()
        
        # Filter by category if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # For detail view, prefetch rules and examples
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('rules', queryset=GrammarRule.objects.all().order_by('order')),
                Prefetch('rules__examples', queryset=GrammarExample.objects.all())
            )
        
        return queryset.order_by('order_index')
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Get all unique concept categories.
        """
        categories = GrammarConcept.objects.values_list('category', flat=True).distinct().order_by('category')
        return Response(list(categories))
    
    @action(detail=False, methods=['get'])
    def progression(self, request):
        """
        Get concepts in curriculum progression order.
        """
        concepts = self.get_queryset().order_by('order_index')
        serializer = GrammarConceptListSerializer(concepts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def teaching_instances(self, request, pk=None):
        """
        Get all chunks where this concept is taught.
        """
        concept = self.get_object()
        focuses = concept.teaching_instances.all().select_related('chunk__lesson')
        
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


class GrammarRuleViewSet(BaseViewSet):
    """
    ViewSet for viewing grammar rules.
    """
    
    queryset = GrammarRule.objects.all()
    serializer_class = GrammarRuleSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        """
        Filter by concept if provided.
        """
        queryset = super().get_queryset()
        
        concept_id = self.request.query_params.get('concept_id')
        if concept_id:
            queryset = queryset.filter(concept_id=concept_id)
        
        return queryset.order_by('order')


class GrammarExampleViewSet(BaseViewSet):
    """
    ViewSet for viewing grammar examples.
    """
    
    queryset = GrammarExample.objects.all()
    serializer_class = GrammarExampleSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        """
        Filter by rule if provided.
        """
        queryset = super().get_queryset()
        
        rule_id = self.request.query_params.get('rule_id')
        if rule_id:
            queryset = queryset.filter(rule_id=rule_id)
        
        return queryset.order_by('order')


# ============================================================
# TEACHING LAYER VIEWS
# ============================================================

class ChunkGrammarFocusViewSet(BaseViewSet):
    """
    ViewSet for grammar focuses within chunks.
    
    Provides:
    - List focuses for a chunk
    - Retrieve focus with questions
    - Get practice/test statistics
    """
    
    queryset = ChunkGrammarFocus.objects.all()
    serializer_class = ChunkGrammarFocusSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list' and self.request.GET.get('simple') == 'true':
            return ChunkGrammarFocusListSerializer
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
        
        # Prefetch questions for detail view
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('questions', queryset=GrammarQuestion.objects.all())
            )
        
        return queryset.order_by('sequence_order')
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """
        Get all questions for this focus.
        """
        focus = self.get_object()
        questions = focus.questions.all().order_by('id')
        serializer = GrammarQuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get practice and test statistics for this focus.
        """
        focus = self.get_object()
        user = request.user
        
        # Practice stats
        practice_attempts = GrammarPracticeAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-created_at')
        
        # Test stats
        test_attempts = GrammarTestAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-created_at')
        
        stats = {
            'practice': {
                'total_attempts': practice_attempts.count(),
                'best_score': practice_attempts.aggregate(best=Max('score_percent'))['best'],
                'average_score': practice_attempts.aggregate(avg=Avg('score_percent'))['avg'],
                'last_attempt': GrammarPracticeAttemptSerializer(practice_attempts.first()).data if practice_attempts.exists() else None
            },
            'test': {
                'total_attempts': test_attempts.count(),
                'best_score': test_attempts.aggregate(best=Max('score_percent'))['best'],
                'average_score': test_attempts.aggregate(avg=Avg('score_percent'))['avg'],
                'is_mastered': test_attempts.filter(is_mastered=True).exists(),
                'last_attempt': GrammarTestAttemptSerializer(test_attempts.first()).data if test_attempts.exists() else None
            }
        }
        
        return Response(stats)


class GrammarQuestionViewSet(BaseViewSet):
    """
    ViewSet for grammar questions.
    """
    
    queryset = GrammarQuestion.objects.all()
    serializer_class = GrammarQuestionSerializer
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

class GrammarPracticeViewSet(PracticeViewSet):
    """
    ViewSet for grammar practice attempts.
    
    Provides:
    - Submit practice attempt
    - List user's practice history
    - Get practice statistics
    """
    
    queryset = GrammarPracticeAttempt.objects.all()
    serializer_class = GrammarPracticeAttemptSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return GrammarPracticeAttemptSubmitSerializer
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
        Create a new grammar practice attempt.
        """
        # Get the focus object
        focus_obj = get_object_or_404(ChunkGrammarFocus, id=focus)
        
        # Get questions for this focus
        questions = list(focus_obj.questions.all())
        
        # Calculate score
        correct_count = 0
        question_attempts = []
        
        for answer in answers_data:
            question_id = answer.get('question_id')
            selected = answer.get('selected_answer')
            
            try:
                question = next(q for q in questions if q.id == question_id)
                is_correct = (selected == question.correct_answer)
                
                if is_correct:
                    correct_count += 1
                
                # Record question attempt
                question_attempt = GrammarQuestionAttempt.objects.create(
                    user=request.user,
                    question_id=question_id,
                    practice_attempt=None,  # Will update after practice attempt created
                    selected_answer=selected,
                    is_correct=is_correct,
                    time_taken_seconds=answer.get('time_taken_seconds')
                )
                question_attempts.append(question_attempt)
                
            except StopIteration:
                continue
        
        # Calculate score percentage
        total_questions = len(questions)
        score_percent = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
        
        # Create practice attempt
        attempt = GrammarPracticeAttempt.objects.create(
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
        
        # Update question attempts with practice attempt reference
        for qa in question_attempts:
            qa.practice_attempt = attempt
            qa.save()
        
        log_user_activity(
            request.user,
            'grammar_practice_completed',
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
            'by_focus': []
        }
        
        # Group by focus
        focus_ids = attempts.values_list('focus', flat=True).distinct()
        for focus_id in focus_ids[:5]:  # Top 5 focuses
            focus_attempts = attempts.filter(focus_id=focus_id)
            focus = ChunkGrammarFocus.objects.get(id=focus_id)
            
            summary['by_focus'].append({
                'focus_id': focus_id,
                'focus_title': focus.focus_title,
                'attempts': focus_attempts.count(),
                'best_score': focus_attempts.aggregate(best=Max('score_percent'))['best'],
                'average_score': focus_attempts.aggregate(avg=Avg('score_percent'))['avg']
            })
        
        return Response(summary)
    
    @action(detail=True, methods=['get'])
    def question_attempts(self, request, pk=None):
        """
        Get all question attempts for a practice attempt.
        """
        attempt = self.get_object()
        question_attempts = attempt.question_attempts.all()
        serializer = GrammarQuestionAttemptSerializer(question_attempts, many=True)
        return Response(serializer.data)


# ============================================================
# TEST VIEWS
# ============================================================

class GrammarTestViewSet(TestViewSet):
    """
    ViewSet for grammar test attempts.
    
    Provides:
    - Submit test attempt
    - List user's test history
    - Get mastery status
    """
    
    queryset = GrammarTestAttempt.objects.all()
    serializer_class = GrammarTestAttemptSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return GrammarTestAttemptSubmitSerializer
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
        Create a new grammar test attempt.
        """
        focus_id = request.data.get('focus_id')
        answers_data = request.data.get('answers', [])
        
        # Get the focus object
        focus_obj = get_object_or_404(ChunkGrammarFocus, id=focus_id)
        
        # Get questions for this focus
        questions = list(focus_obj.questions.all())
        
        # Calculate score
        correct_count = 0
        question_attempts = []
        
        for answer in answers_data:
            question_id = answer.get('question_id')
            selected = answer.get('selected_answer')
            
            try:
                question = next(q for q in questions if q.id == question_id)
                is_correct = (selected == question.correct_answer)
                
                if is_correct:
                    correct_count += 1
                
                # Record question attempt
                question_attempt = GrammarQuestionAttempt.objects.create(
                    user=request.user,
                    question_id=question_id,
                    test_attempt=None,  # Will update after test attempt created
                    selected_answer=selected,
                    is_correct=is_correct,
                    time_taken_seconds=answer.get('time_taken_seconds')
                )
                question_attempts.append(question_attempt)
                
            except StopIteration:
                continue
        
        # Calculate score percentage
        total_questions = len(questions)
        score_percent = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
        
        # Create test attempt
        attempt = GrammarTestAttempt.objects.create(
            user=request.user,
            focus=focus_obj,
            attempt_number=kwargs.get('attempt_number'),
            cycle_number=kwargs.get('cycle_number'),
            score_percent=score_percent,
            correct_answers=correct_count,
            total_questions=total_questions,
            questions_snapshot={
                'answers': answers_data,
                'questions': [{'id': q.id, 'text': q.question_text} for q in questions]
            }
        )
        
        # Update question attempts with test attempt reference
        for qa in question_attempts:
            qa.test_attempt = attempt
            qa.save()
        
        log_user_activity(
            request.user,
            'grammar_test_completed',
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
        Get mastery summary across all focuses.
        """
        user = request.user
        
        # Get all focuses
        all_focuses = ChunkGrammarFocus.objects.all()
        
        # Get mastered focuses
        mastered_focuses = self.get_queryset().filter(
            is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        
        # Get in-progress focuses
        attempted_focuses = self.get_queryset().values_list('focus_id', flat=True).distinct()
        in_progress = set(attempted_focuses) - set(mastered_focuses)
        
        summary = {
            'total_focuses': all_focuses.count(),
            'mastered_count': len(mastered_focuses),
            'in_progress_count': len(in_progress),
            'not_started_count': all_focuses.count() - len(attempted_focuses),
            'mastery_percentage': (len(mastered_focuses) / all_focuses.count() * 100) if all_focuses.exists() else 0,
            'recently_mastered': []
        }
        
        # Get recently mastered (last 7 days)
        recent = self.get_queryset().filter(
            is_mastered=True,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('focus')[:5]
        
        for attempt in recent:
            summary['recently_mastered'].append({
                'focus_id': attempt.focus_id,
                'focus_title': attempt.focus.focus_title,
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
        serializer = GrammarQuestionAttemptDetailSerializer(question_attempts, many=True)
        return Response(serializer.data)


# ============================================================
# QUESTION ATTEMPT VIEWS
# ============================================================

class GrammarQuestionAttemptViewSet(BaseViewSet, UserFilterMixin):
    """
    ViewSet for grammar question attempts (analytics).
    """
    
    queryset = GrammarQuestionAttempt.objects.all()
    serializer_class = GrammarQuestionAttemptSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """
        Return detailed serializer for retrieve action.
        """
        if self.action == 'retrieve':
            return GrammarQuestionAttemptDetailSerializer
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
        
        return queryset
    
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
            'by_question': []
        }
        
        # Group by question
        question_ids = queryset.values_list('question', flat=True).distinct()[:10]
        for qid in question_ids:
            q_attempts = queryset.filter(question_id=qid)
            q_correct = q_attempts.filter(is_correct=True).count()
            
            try:
                question = GrammarQuestion.objects.get(id=qid)
                analytics['by_question'].append({
                    'question_id': qid,
                    'question_text': question.question_text[:100],
                    'total_attempts': q_attempts.count(),
                    'correct_attempts': q_correct,
                    'accuracy': (q_correct / q_attempts.count() * 100) if q_attempts.exists() else 0
                })
            except GrammarQuestion.DoesNotExist:
                continue
        
        return Response(analytics)


# ============================================================
# PROGRESS VIEWS
# ============================================================

class GrammarProgressViewSet(ProgressViewSet):
    """
    ViewSet for grammar progress tracking.
    """
    
    serializer_class = GrammarConceptProgressSerializer
    
    def get_user_progress(self, user):
        """
        Get grammar progress for user.
        """
        # Get all concepts
        concepts = GrammarConcept.objects.all().order_by('order_index')
        
        progress_data = []
        
        for concept in concepts:
            # Get focuses for this concept
            focuses = concept.teaching_instances.all()
            
            # Calculate practice stats
            practice_attempts = GrammarPracticeAttempt.objects.filter(
                user=user,
                focus__in=focuses
            )
            
            # Calculate test stats
            test_attempts = GrammarTestAttempt.objects.filter(
                user=user,
                focus__in=focuses
            )
            
            # Check if mastered
            mastered = test_attempts.filter(is_mastered=True).exists()
            
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
                'concept_id': concept.id,
                'concept_name': concept.name,
                'category': concept.category,
                'practice_attempts': practice_attempts.count(),
                'best_practice_score': practice_attempts.aggregate(best=Max('score_percent'))['best'],
                'latest_practice_score': practice_attempts.first().score_percent if practice_attempts.exists() else None,
                'test_attempts': test_attempts.count(),
                'best_test_score': test_attempts.aggregate(best=Max('score_percent'))['best'],
                'is_mastered': mastered,
                'mastery_status': 'mastered' if mastered else ('in_progress' if test_attempts.exists() else 'not_started'),
                'last_attempted': last_attempted
            })
        
        return progress_data
    
    @action(detail=False, methods=['get'])
    def focus_progress(self, request):
        """
        Get progress for specific grammar focuses.
        """
        user = request.user
        focus_ids = request.query_params.getlist('focus_ids')
        
        if not focus_ids:
            return Response(
                {'error': 'focus_ids parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        focuses = ChunkGrammarFocus.objects.filter(id__in=focus_ids)
        progress_data = []
        
        for focus in focuses:
            # Practice tracking
            practice_attempts = GrammarPracticeAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-cycle_number', '-attempt_number')
            
            latest_practice = practice_attempts.first()
            
            # Test tracking
            test_attempts = GrammarTestAttempt.objects.filter(
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

class GrammarBulkOperationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for bulk operations on grammar data.
    Admin-only endpoints for content management.
    """
    
    permission_classes = [IsAuthenticated]  # Add admin check
    
    @action(detail=False, methods=['post'])
    def create_questions(self, request):
        """
        Bulk create grammar questions for a focus.
        """
        serializer = GrammarBulkQuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        focus_id = serializer.validated_data['focus_id']
        questions_data = serializer.validated_data['questions']
        
        focus = get_object_or_404(ChunkGrammarFocus, id=focus_id)
        
        created_questions = []
        with transaction.atomic():
            for q_data in questions_data:
                question = GrammarQuestion.objects.create(
                    focus=focus,
                    question_text=q_data['question_text'],
                    options=q_data.get('options', ''),
                    correct_answer=q_data['correct_answer'],
                    question_type=q_data.get('question_type', 'mcq'),
                    difficulty=q_data.get('difficulty', 3),
                    explanation=q_data.get('explanation', '')
                )
                created_questions.append(question.id)
        
        log_user_activity(
            request.user,
            'bulk_create_grammar_questions',
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