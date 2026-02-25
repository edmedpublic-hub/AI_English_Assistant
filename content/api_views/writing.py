# api_views/writing.py

"""
Writing domain views for practice, testing, and progress tracking.
Provides endpoints for writing tasks at chunk and unit levels.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import models, transaction
from django.db.models import Q, Prefetch, Count, Avg, Max, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from content.models.writing import (
    ChunkWritingFocus, UnitWritingTask, WritingPrompt,
    WritingPracticeAttempt, WritingTestAttempt
)
from content.models.core import LessonChunk, Unit
from content.serializers.writing import (
    # Chunk-level
    ChunkWritingFocusSerializer, ChunkWritingFocusListSerializer,
    
    # Unit-level
    UnitWritingTaskSerializer, UnitWritingTaskListSerializer,
    
    # Prompts
    WritingPromptSerializer, WritingPromptListSerializer,
    WritingPromptMobileSerializer,
    
    # Practice layer
    WritingPracticeAttemptSerializer, WritingPracticeAttemptSubmitSerializer,
    WritingPracticeAttemptMobileSerializer,
    
    # Test layer
    WritingTestAttemptSerializer, WritingTestAttemptSubmitSerializer,
    WritingTestAttemptMobileSerializer,
    
    # Progress tracking
    WritingProgressSummarySerializer, WritingFocusProgressSerializer,
    WritingTaskProgressSerializer,
    
    # Bulk operations
    WritingBulkPromptCreateSerializer
)
from .base import (
    BaseViewSet, PracticeViewSet, TestViewSet, ProgressViewSet,
    UserFilterMixin, IsOwnerOrReadOnly, log_user_activity
)


# ============================================================
# CHUNK-LEVEL WRITING FOCUS VIEWS
# ============================================================

class ChunkWritingFocusViewSet(BaseViewSet):
    """
    ViewSet for chunk-level writing focuses.
    
    Provides:
    - List focuses for a chunk
    - Retrieve focus with prompts
    - Get practice/test statistics
    """
    
    queryset = ChunkWritingFocus.objects.all()
    serializer_class = ChunkWritingFocusSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list' and self.request.GET.get('simple') == 'true':
            return ChunkWritingFocusListSerializer
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
        
        # Filter by depth level
        depth = self.request.query_params.get('depth')
        if depth:
            queryset = queryset.filter(depth_level=depth)
        
        # For detail view, prefetch prompts
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('prompts', queryset=WritingPrompt.objects.all())
            )
        
        return queryset.order_by('sequence_order')
    
    @action(detail=True, methods=['get'])
    def prompts(self, request, pk=None):
        """
        Get all prompts for this focus.
        """
        focus = self.get_object()
        prompts = focus.prompts.all()
        serializer = WritingPromptSerializer(prompts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get practice and test statistics for this focus.
        """
        focus = self.get_object()
        user = request.user
        
        # Practice stats
        practice_attempts = WritingPracticeAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-created_at')
        
        # Test stats
        test_attempts = WritingTestAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-created_at')
        
        stats = {
            'practice': {
                'total_attempts': practice_attempts.count(),
                'best_score': practice_attempts.aggregate(best=Max('keyword_match_score'))['best'],
                'average_score': practice_attempts.aggregate(avg=Avg('keyword_match_score'))['avg'],
                'last_attempt': WritingPracticeAttemptSerializer(practice_attempts.first()).data if practice_attempts.exists() else None
            },
            'test': {
                'total_attempts': test_attempts.count(),
                'best_score': test_attempts.aggregate(best=Max('overall_score'))['best'],
                'average_score': test_attempts.aggregate(avg=Avg('overall_score'))['avg'],
                'is_mastered': test_attempts.filter(is_mastered=True).exists(),
                'last_attempt': WritingTestAttemptSerializer(test_attempts.first()).data if test_attempts.exists() else None
            }
        }
        
        return Response(stats)


# ============================================================
# UNIT-LEVEL WRITING TASK VIEWS
# ============================================================

class UnitWritingTaskViewSet(BaseViewSet):
    """
    ViewSet for unit-level writing tasks.
    
    Provides:
    - List tasks for a unit
    - Retrieve task with prompts
    - Get test statistics
    - Filter by stage (paragraph, essay, etc.)
    """
    
    queryset = UnitWritingTask.objects.all()
    serializer_class = UnitWritingTaskSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list' and self.request.GET.get('simple') == 'true':
            return UnitWritingTaskListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Optimize queryset with filters and prefetches.
        """
        queryset = super().get_queryset()
        
        # Filter by unit
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        
        # Filter by stage
        stage = self.request.query_params.get('stage')
        if stage:
            queryset = queryset.filter(stage=stage)
        
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        # For detail view, prefetch prompts
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('prompts', queryset=WritingPrompt.objects.all())
            )
        
        return queryset.order_by('order')
    
    @action(detail=False, methods=['get'])
    def stages(self, request):
        """
        Get all writing stages with counts.
        """
        stages = []
        for stage_code, stage_name in UnitWritingTask.STAGE_CHOICES:
            count = self.get_queryset().filter(stage=stage_code).count()
            stages.append({
                'code': stage_code,
                'name': stage_name,
                'count': count
            })
        return Response(stages)
    
    @action(detail=True, methods=['get'])
    def prompts(self, request, pk=None):
        """
        Get all prompts for this task.
        """
        task = self.get_object()
        prompts = task.prompts.all()
        serializer = WritingPromptSerializer(prompts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get test statistics for this task.
        """
        task = self.get_object()
        user = request.user
        
        # Test stats
        test_attempts = WritingTestAttempt.objects.filter(
            user=user,
            task=task
        ).order_by('-created_at')
        
        stats = {
            'test': {
                'total_attempts': test_attempts.count(),
                'best_score': test_attempts.aggregate(best=Max('overall_score'))['best'],
                'average_score': test_attempts.aggregate(avg=Avg('overall_score'))['avg'],
                'is_mastered': test_attempts.filter(is_mastered=True).exists(),
                'last_attempt': WritingTestAttemptSerializer(test_attempts.first()).data if test_attempts.exists() else None
            }
        }
        
        return Response(stats)


# ============================================================
# WRITING PROMPT VIEWS
# ============================================================

class WritingPromptViewSet(BaseViewSet):
    """
    ViewSet for writing prompts.
    
    Provides:
    - List prompts for a focus or task
    - Retrieve prompt details
    - Mobile-optimized endpoint
    """
    
    queryset = WritingPrompt.objects.all()
    serializer_class = WritingPromptSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'list' and self.request.GET.get('mobile') == 'true':
            return WritingPromptMobileSerializer
        
        if self.action == 'mobile_list':
            return WritingPromptMobileSerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter by focus, task, or type.
        """
        queryset = super().get_queryset()
        
        # Filter by focus
        focus_id = self.request.query_params.get('focus_id')
        if focus_id:
            queryset = queryset.filter(focus_id=focus_id)
        
        # Filter by task
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        # Filter by prompt type
        prompt_type = self.request.query_params.get('type')
        if prompt_type:
            queryset = queryset.filter(prompt_type=prompt_type)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def mobile_list(self, request):
        """
        Lightweight prompt list for mobile.
        """
        focus_id = request.query_params.get('focus_id')
        task_id = request.query_params.get('task_id')
        
        if not focus_id and not task_id:
            return Response(
                {'error': 'Either focus_id or task_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prompts = self.get_queryset()
        serializer = WritingPromptMobileSerializer(prompts, many=True)
        return Response(serializer.data)


# ============================================================
# PRACTICE VIEWS
# ============================================================

class WritingPracticeViewSet(PracticeViewSet):
    """
    ViewSet for writing practice attempts (chunk-level).
    
    Provides:
    - Submit practice attempt
    - List user's practice history
    - Get practice statistics
    """
    
    queryset = WritingPracticeAttempt.objects.all()
    serializer_class = WritingPracticeAttemptSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'create':
            return WritingPracticeAttemptSubmitSerializer
        
        if self.action == 'list' and self.request.GET.get('mobile') == 'true':
            return WritingPracticeAttemptMobileSerializer
        
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
        
        # Filter by prompt
        prompt_id = self.request.query_params.get('prompt_id')
        if prompt_id:
            queryset = queryset.filter(prompt_id=prompt_id)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        if from_date:
            queryset = queryset.filter(created_at__gte=from_date)
        
        to_date = self.request.query_params.get('to_date')
        if to_date:
            queryset = queryset.filter(created_at__lte=to_date)
        
        return queryset.select_related('focus', 'prompt')
    
    @transaction.atomic
    def create_attempt(self, request, focus, answers_data, **kwargs):
        """
        Create a new writing practice attempt.
        """
        # Get the focus object
        focus_obj = get_object_or_404(ChunkWritingFocus, id=focus)
        
        # Get prompt from kwargs
        prompt_id = kwargs.get('prompt_id')
        prompt = get_object_or_404(WritingPrompt, id=prompt_id)
        
        # Get response text
        response_text = kwargs.get('response_text', '')
        
        # Calculate keyword match score if expected keywords exist
        keyword_match_score = None
        if prompt.expected_keywords:
            keywords = [k.strip().lower() for k in prompt.expected_keywords.split(',') if k.strip()]
            response_lower = response_text.lower()
            matched = sum(1 for k in keywords if k in response_lower)
            keyword_match_score = int((matched / len(keywords)) * 100) if keywords else None
        
        # Create practice attempt
        attempt = WritingPracticeAttempt.objects.create(
            user=request.user,
            focus=focus_obj,
            prompt=prompt,
            attempt_number=kwargs.get('attempt_number'),
            cycle_number=kwargs.get('cycle_number'),
            response_text=response_text,
            keyword_match_score=keyword_match_score,
            time_spent_seconds=kwargs.get('time_spent_seconds'),
            hints_used=kwargs.get('hints_used', 0)
        )
        
        log_user_activity(
            request.user,
            'writing_practice_completed',
            {
                'focus_id': focus,
                'prompt_id': prompt_id,
                'score': keyword_match_score,
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
        
        total_attempts = attempts.count()
        total_hints = attempts.aggregate(total=Sum('hints_used'))['total'] or 0
        
        summary = {
            'total_attempts': total_attempts,
            'average_score': attempts.aggregate(avg=Avg('keyword_match_score'))['avg'],
            'passed_attempts': attempts.filter(is_passed=True).count(),
            'total_hints_used': total_hints,
            'by_depth_level': []
        }
        
        # Group by depth level
        for depth in range(1, 6):
            depth_attempts = attempts.filter(focus__depth_level=depth)
            if depth_attempts.exists():
                summary['by_depth_level'].append({
                    'depth_level': depth,
                    'attempts': depth_attempts.count(),
                    'average_score': depth_attempts.aggregate(avg=Avg('keyword_match_score'))['avg']
                })
        
        return Response(summary)


# ============================================================
# TEST VIEWS
# ============================================================

class WritingTestViewSet(TestViewSet):
    """
    ViewSet for writing test attempts (both chunk and unit level).
    
    Provides:
    - Submit test attempt
    - List user's test history
    - Get mastery status
    """
    
    queryset = WritingTestAttempt.objects.all()
    serializer_class = WritingTestAttemptSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'create':
            return WritingTestAttemptSubmitSerializer
        
        if self.action == 'list' and self.request.GET.get('mobile') == 'true':
            return WritingTestAttemptMobileSerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter to current user's attempts.
        """
        queryset = super().get_queryset()
        
        # Filter by focus (chunk-level)
        focus_id = self.request.query_params.get('focus_id')
        if focus_id:
            queryset = queryset.filter(focus_id=focus_id)
        
        # Filter by task (unit-level)
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        # Filter by prompt
        prompt_id = self.request.query_params.get('prompt_id')
        if prompt_id:
            queryset = queryset.filter(prompt_id=prompt_id)
        
        # Filter by mastery status
        mastered = self.request.query_params.get('mastered')
        if mastered is not None:
            is_mastered = mastered.lower() == 'true'
            queryset = queryset.filter(is_mastered=is_mastered)
        
        return queryset.select_related('focus', 'task', 'prompt')
    
    def get_current_cycle_info(self, user, focus=None, task=None, unit=None):
        """
        Override to handle both focus and task.
        """
        model = self.get_queryset().model
        
        # Build filter based on what's provided
        filter_kwargs = {'user': user}
        if focus:
            filter_kwargs['focus'] = focus
        if task:
            filter_kwargs['task'] = task
        
        # Get latest attempt
        latest = model.objects.filter(**filter_kwargs).order_by(
            '-cycle_number', '-attempt_number'
        ).first()
        
        if not latest:
            return {
                'cycle_number': 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle
            }
        
        # Different mastery thresholds for chunk vs unit
        if latest.focus is not None:
            # Chunk-level: 100% required
            is_mastered = (latest.overall_score == 100)
        else:
            # Unit-level: 70% required
            is_mastered = (latest.overall_score >= 70)
        
        if is_mastered:
            return {
                'cycle_number': latest.cycle_number + 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle,
                'mastered': True
            }
        
        if latest.attempt_number >= self.max_attempts_per_cycle:
            return {
                'cycle_number': latest.cycle_number + 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle
            }
        
        remaining = self.max_attempts_per_cycle - latest.attempt_number
        return {
            'cycle_number': latest.cycle_number,
            'attempt_number': latest.attempt_number + 1,
            'attempts_remaining': remaining - 1
        }
    
    @transaction.atomic
    def create_test_attempt(self, request, **kwargs):
        """
        Create a new writing test attempt.
        """
        focus_id = request.data.get('focus_id')
        task_id = request.data.get('task_id')
        prompt_id = request.data.get('prompt_id')
        response_text = request.data.get('response_text', '')
        
        # Get prompt
        prompt = get_object_or_404(WritingPrompt, id=prompt_id)
        
        # Determine context (focus or task)
        focus_obj = None
        task_obj = None
        if focus_id:
            focus_obj = get_object_or_404(ChunkWritingFocus, id=focus_id)
        elif task_id:
            task_obj = get_object_or_404(UnitWritingTask, id=task_id)
        
        # Create test attempt
        attempt = WritingTestAttempt.objects.create(
            user=request.user,
            focus=focus_obj,
            task=task_obj,
            prompt=prompt,
            attempt_number=kwargs.get('attempt_number'),
            cycle_number=kwargs.get('cycle_number'),
            response_text=response_text,
            rubric_scores={},  # To be filled by teacher/AI later
            overall_score=0,  # To be scored later
            time_spent_seconds=request.data.get('time_spent_seconds')
        )
        
        log_user_activity(
            request.user,
            'writing_test_completed',
            {
                'focus_id': focus_id,
                'task_id': task_id,
                'prompt_id': prompt_id,
                'attempt_number': kwargs.get('attempt_number'),
                'cycle_number': kwargs.get('cycle_number')
            }
        )
        
        return attempt
    
    @action(detail=False, methods=['get'])
    def mastery_summary(self, request):
        """
        Get mastery summary for writing.
        """
        user = request.user
        
        # Chunk-level focuses
        chunk_focuses = ChunkWritingFocus.objects.all()
        chunk_mastered = self.get_queryset().filter(
            focus__isnull=False,
            is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        
        # Unit-level tasks
        unit_tasks = UnitWritingTask.objects.all()
        unit_mastered = self.get_queryset().filter(
            task__isnull=False,
            is_mastered=True
        ).values_list('task_id', flat=True).distinct()
        
        summary = {
            'chunk_level': {
                'total': chunk_focuses.count(),
                'mastered': len(chunk_mastered),
                'mastery_percentage': (len(chunk_mastered) / chunk_focuses.count() * 100) if chunk_focuses.exists() else 0
            },
            'unit_level': {
                'total': unit_tasks.count(),
                'mastered': len(unit_mastered),
                'mastery_percentage': (len(unit_mastered) / unit_tasks.count() * 100) if unit_tasks.exists() else 0
            },
            'by_stage': [],
            'recently_mastered': []
        }
        
        # Breakdown by writing stage
        for stage_code, stage_name in UnitWritingTask.STAGE_CHOICES:
            stage_tasks = unit_tasks.filter(stage=stage_code)
            stage_mastered = unit_tasks.filter(
                id__in=unit_mastered,
                stage=stage_code
            ).count()
            
            summary['by_stage'].append({
                'stage': stage_code,
                'name': stage_name,
                'total': stage_tasks.count(),
                'mastered': stage_mastered,
                'mastery_percentage': (stage_mastered / stage_tasks.count() * 100) if stage_tasks.exists() else 0
            })
        
        # Get recently mastered (last 7 days)
        recent = self.get_queryset().filter(
            is_mastered=True,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('focus', 'task')[:5]
        
        for attempt in recent:
            if attempt.focus:
                title = attempt.focus.focus_title
                context_type = 'chunk'
                item_id = attempt.focus.id
            else:
                title = attempt.task.task_title
                context_type = 'unit'
                item_id = attempt.task.id
            
            summary['recently_mastered'].append({
                'id': item_id,
                'title': title,
                'type': context_type,
                'score': attempt.overall_score,
                'mastered_at': attempt.created_at
            })
        
        return Response(summary)


# ============================================================
# PROGRESS VIEWS
# ============================================================

class WritingProgressViewSet(ProgressViewSet):
    """
    ViewSet for writing progress tracking.
    """
    
    serializer_class = WritingProgressSummarySerializer
    
    def get_user_progress(self, user):
        """
        Get writing progress for user.
        """
        # Chunk-level focuses
        chunk_focuses = ChunkWritingFocus.objects.all()
        chunk_practice = WritingPracticeAttempt.objects.filter(user=user)
        chunk_tests = WritingTestAttempt.objects.filter(user=user, focus__isnull=False)
        
        chunk_mastered = chunk_tests.filter(is_mastered=True).values_list('focus_id', flat=True).distinct()
        
        # Unit-level tasks
        unit_tasks = UnitWritingTask.objects.all()
        unit_tests = WritingTestAttempt.objects.filter(user=user, task__isnull=False)
        unit_mastered = unit_tests.filter(is_mastered=True).values_list('task_id', flat=True).distinct()
        
        # Practice stats
        total_practice = chunk_practice.count()
        avg_practice_score = chunk_practice.aggregate(avg=Avg('keyword_match_score'))['avg']
        
        # Test stats
        total_tests = chunk_tests.count() + unit_tests.count()
        all_tests = list(chunk_tests) + list(unit_tests)
        avg_test_score = sum(t.overall_score for t in all_tests) / len(all_tests) if all_tests else 0
        
        # Breakdown by stage
        by_stage = {}
        for stage_code, stage_name in UnitWritingTask.STAGE_CHOICES:
            stage_tasks = unit_tasks.filter(stage=stage_code)
            stage_mastered = unit_tasks.filter(
                id__in=unit_mastered,
                stage=stage_code
            ).count()
            
            by_stage[stage_code] = {
                'name': stage_name,
                'total': stage_tasks.count(),
                'mastered': stage_mastered,
                'percentage': (stage_mastered / stage_tasks.count() * 100) if stage_tasks.exists() else 0
            }
        
        # Recent activity
        recent_practice = chunk_practice.order_by('-created_at')[:5]
        recent_tests = WritingTestAttempt.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Calculate total time spent
        practice_time = chunk_practice.aggregate(total=Sum('time_spent_seconds'))['total'] or 0
        chunk_test_time = chunk_tests.aggregate(total=Sum('time_spent_seconds'))['total'] or 0
        unit_test_time = unit_tests.aggregate(total=Sum('time_spent_seconds'))['total'] or 0
        total_time_seconds = practice_time + chunk_test_time + unit_test_time
        
        # Determine last activity
        last_test = recent_tests.first()
        last_practice = recent_practice.first()
        last_activity = None
        if last_test and last_practice:
            last_activity = max(last_test.created_at, last_practice.created_at)
        elif last_test:
            last_activity = last_test.created_at
        elif last_practice:
            last_activity = last_practice.created_at
        
        progress_data = {
            'chunk_focuses_total': chunk_focuses.count(),
            'chunk_focuses_mastered': len(chunk_mastered),
            'chunk_mastery_percentage': (len(chunk_mastered) / chunk_focuses.count() * 100) if chunk_focuses.exists() else 0,
            
            'unit_tasks_total': unit_tasks.count(),
            'unit_tasks_mastered': len(unit_mastered),
            'unit_mastery_percentage': (len(unit_mastered) / unit_tasks.count() * 100) if unit_tasks.exists() else 0,
            
            'total_practice_attempts': total_practice,
            'average_practice_score': avg_practice_score,
            
            'total_test_attempts': total_tests,
            'average_test_score': avg_test_score,
            
            'by_stage': by_stage,
            
            'total_time_spent': total_time_seconds // 60,  # Convert to minutes
            
            'last_activity': last_activity,
            
            'recent_practice': WritingPracticeAttemptSerializer(recent_practice, many=True).data,
            'recent_tests': WritingTestAttemptSerializer(recent_tests, many=True).data
        }
        
        return progress_data
    
    @action(detail=False, methods=['get'])
    def focus_progress(self, request):
        """
        Get progress for specific writing focuses.
        """
        user = request.user
        focus_ids = request.query_params.getlist('focus_ids')
        
        if not focus_ids:
            return Response(
                {'error': 'focus_ids parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        focuses = ChunkWritingFocus.objects.filter(id__in=focus_ids)
        progress_data = []
        
        for focus in focuses:
            # Practice tracking
            practice_attempts = WritingPracticeAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-cycle_number', '-attempt_number')
            
            latest_practice = practice_attempts.first()
            
            # Test tracking
            test_attempts = WritingTestAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-cycle_number', '-attempt_number')
            
            latest_test = test_attempts.first()
            
            # Performance by prompt
            prompt_performance = {}
            for prompt in focus.prompts.all():
                prompt_attempts = practice_attempts.filter(prompt=prompt)
                if prompt_attempts.exists():
                    prompt_performance[prompt.id] = {
                        'attempts': prompt_attempts.count(),
                        'best_score': prompt_attempts.aggregate(best=Max('keyword_match_score'))['best'],
                        'average_score': prompt_attempts.aggregate(avg=Avg('keyword_match_score'))['avg']
                    }
            
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
                'prompt_performance': prompt_performance,
                'next_action': next_action
            })
        
        return Response(progress_data)
    
    @action(detail=False, methods=['get'])
    def task_progress(self, request):
        """
        Get progress for specific writing tasks.
        """
        user = request.user
        task_ids = request.query_params.getlist('task_ids')
        
        if not task_ids:
            return Response(
                {'error': 'task_ids parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = UnitWritingTask.objects.filter(id__in=task_ids)
        progress_data = []
        
        for task in tasks:
            # Test tracking
            test_attempts = WritingTestAttempt.objects.filter(
                user=user,
                task=task
            ).order_by('-cycle_number', '-attempt_number')
            
            latest_test = test_attempts.first()
            
            # Best performance
            best_attempt = test_attempts.order_by('-overall_score').first()
            
            # Rubric performance (if any scores exist)
            rubric_performance = {}
            for attempt in test_attempts:
                if attempt.rubric_scores:
                    for criterion, score in attempt.rubric_scores.items():
                        if criterion not in rubric_performance:
                            rubric_performance[criterion] = []
                        rubric_performance[criterion].append(score)
            
            # Average rubric scores
            avg_rubric = {}
            for criterion, scores in rubric_performance.items():
                avg_rubric[criterion] = sum(scores) / len(scores)
            
            # Determine next action
            next_action = 'test'
            improvement_areas = []
            
            if latest_test and latest_test.is_mastered:
                next_action = 'mastered'
            elif avg_rubric:
                # Find lowest scoring criteria
                sorted_criteria = sorted(avg_rubric.items(), key=lambda x: x[1])
                improvement_areas = [c[0] for c in sorted_criteria[:2]]
            
            progress_data.append({
                'task_id': task.id,
                'task_title': task.task_title,
                'stage': task.stage,
                'difficulty_level': task.difficulty_level,
                'current_test_cycle': latest_test.cycle_number if latest_test else 1,
                'current_test_attempt': latest_test.attempt_number if latest_test else 0,
                'is_mastered': latest_test.is_mastered if latest_test else False,
                'test_attempts_remaining': 3 - (latest_test.attempt_number if latest_test else 0),
                'best_score': best_attempt.overall_score if best_attempt else None,
                'best_score_date': best_attempt.created_at if best_attempt else None,
                'rubric_performance': avg_rubric,
                'next_action': next_action,
                'improvement_areas': improvement_areas
            })
        
        return Response(progress_data)


# ============================================================
# BULK OPERATION VIEWS
# ============================================================

class WritingBulkOperationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for bulk operations on writing data.
    Admin-only endpoints for content management.
    """
    
    permission_classes = [IsAuthenticated]  # Add admin check
    
    @action(detail=False, methods=['post'])
    def create_prompts(self, request):
        """
        Bulk create writing prompts for a focus or task.
        """
        serializer = WritingBulkPromptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        focus_id = serializer.validated_data.get('focus_id')
        task_id = serializer.validated_data.get('task_id')
        prompts_data = serializer.validated_data['prompts']
        
        focus_obj = None
        task_obj = None
        
        if focus_id:
            focus_obj = get_object_or_404(ChunkWritingFocus, id=focus_id)
        elif task_id:
            task_obj = get_object_or_404(UnitWritingTask, id=task_id)
        
        created_prompts = []
        with transaction.atomic():
            for p_data in prompts_data:
                prompt = WritingPrompt.objects.create(
                    focus=focus_obj,
                    task=task_obj,
                    prompt_type=p_data['prompt_type'],
                    prompt_text=p_data['prompt_text'],
                    expected_keywords=p_data.get('expected_keywords', ''),
                    rubric=p_data.get('rubric', {})
                )
                created_prompts.append(prompt.id)
        
        log_user_activity(
            request.user,
            'bulk_create_writing_prompts',
            {
                'focus_id': focus_id,
                'task_id': task_id,
                'count': len(created_prompts)
            }
        )
        
        return Response({
            'success': True,
            'message': f'Created {len(created_prompts)} prompts',
            'prompt_ids': created_prompts
        }, status=status.HTTP_201_CREATED)