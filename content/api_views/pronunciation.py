# api_views/pronunciation.py

"""
Pronunciation domain views for practice, mastery tracking, and progress monitoring.
Provides endpoints for pronunciation learning with AI feedback integration.
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
import json
import base64
from django.core.files.base import ContentFile

from content.models.pronunciation import (
    PronunciationFocus,
    PronunciationAttempt,
    PronunciationMastery
)
from content.models.core import LessonChunk
from content.serializers.pronunciation import (
    # Teaching layer
    PronunciationFocusSerializer, PronunciationFocusListSerializer,
    
    # Attempts
    PronunciationAttemptSerializer, PronunciationAttemptSubmitSerializer,
    PronunciationAttemptMobileSerializer,
    
    # Mastery
    PronunciationMasterySerializer, PronunciationMasteryUpdateSerializer,
    PronunciationMasteryMobileSerializer,
    
    # Progress tracking
    PronunciationProgressSummarySerializer, PronunciationFocusProgressSerializer,
    
    # Bulk operations
    PronunciationBulkFocusCreateSerializer,
    
    # Audio processing
    PronunciationAudioAnalysisSerializer, PronunciationFeedbackSerializer
)
from .base import (
    BaseViewSet, PracticeViewSet, ProgressViewSet,
    UserFilterMixin, IsOwnerOrReadOnly, log_user_activity
)


# ============================================================
# TEACHING LAYER VIEWS
# ============================================================

class PronunciationFocusViewSet(BaseViewSet):
    """
    ViewSet for pronunciation focuses within chunks.
    
    Provides:
    - List focuses for a chunk
    - Retrieve focus details
    - Get attempt statistics and mastery status
    """
    
    queryset = PronunciationFocus.objects.all()
    serializer_class = PronunciationFocusSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'list' and self.request.GET.get('simple') == 'true':
            return PronunciationFocusListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Optimize queryset with filters.
        """
        queryset = super().get_queryset()
        
        # Filter by chunk
        chunk_id = self.request.query_params.get('chunk_id')
        if chunk_id:
            queryset = queryset.filter(chunk_id=chunk_id)
        
        return queryset.order_by('sequence_order')
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get attempt statistics for this focus.
        """
        focus = self.get_object()
        user = request.user
        
        # Get all attempts
        attempts = PronunciationAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-created_at')
        
        # Get mastery record
        try:
            mastery = PronunciationMastery.objects.get(
                user=user,
                focus=focus
            )
            mastery_data = PronunciationMasterySerializer(mastery).data
        except PronunciationMastery.DoesNotExist:
            mastery_data = None
        
        # Separate practice and test attempts
        practice_attempts = attempts.filter(attempt_type='practice')
        test_attempts = attempts.filter(attempt_type='test')
        
        stats = {
            'total_attempts': attempts.count(),
            'practice_attempts': practice_attempts.count(),
            'test_attempts': test_attempts.count(),
            'best_score': attempts.aggregate(best=Max('ai_score'))['best'],
            'average_score': attempts.aggregate(avg=Avg('ai_score'))['avg'],
            'passed_attempts': attempts.filter(ai_score__gte=90).count(),
            'mastery': mastery_data,
            'last_attempt': PronunciationAttemptSerializer(attempts.first()).data if attempts.exists() else None
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def attempts(self, request, pk=None):
        """
        Get all attempts for this focus.
        """
        focus = self.get_object()
        user = request.user
        
        attempts = PronunciationAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-created_at')
        
        serializer = PronunciationAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


# ============================================================
# PRONUNCIATION ATTEMPT VIEWS
# ============================================================

class PronunciationAttemptViewSet(PracticeViewSet):
    """
    ViewSet for pronunciation attempts.
    
    Provides:
    - Submit audio recording for AI analysis
    - List user's attempt history
    - Get attempt statistics
    - Mobile-optimized endpoints
    """
    
    queryset = PronunciationAttempt.objects.all()
    serializer_class = PronunciationAttemptSerializer
    lookup_field = 'pk'
    
    # Override max attempts - pronunciation uses 3 attempts per cycle
    max_attempts_per_cycle = 3
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'create':
            return PronunciationAttemptSubmitSerializer
        
        if self.action == 'list' and self.request.GET.get('mobile') == 'true':
            return PronunciationAttemptMobileSerializer
        
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
        
        # Filter by attempt type
        attempt_type = self.request.query_params.get('type')
        if attempt_type:
            queryset = queryset.filter(attempt_type=attempt_type)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        if from_date:
            queryset = queryset.filter(created_at__gte=from_date)
        
        to_date = self.request.query_params.get('to_date')
        if to_date:
            queryset = queryset.filter(created_at__lte=to_date)
        
        return queryset.select_related('focus')
    
    def get_current_cycle_info(self, user, focus):
        """
        Get current cycle and attempt number for a focus.
        """
        # Get latest attempt
        latest = PronunciationAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-cycle_number', '-attempt_number').first()
        
        if not latest:
            return {
                'cycle_number': 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle
            }
        
        # Check if passed (score >= 90)
        if latest.is_passed:
            return {
                'cycle_number': latest.cycle_number + 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle
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
    
    def validate_attempt_allowed(self, user, focus):
        """
        Validate that user is allowed to make another attempt.
        """
        info = self.get_current_cycle_info(user, focus)
        
        if info['attempts_remaining'] < 0:
            raise ValidationError(
                f"No attempts remaining in current cycle. "
                f"Maximum {self.max_attempts_per_cycle} attempts allowed."
            )
        
        return info
    
    @transaction.atomic
    def create_attempt(self, request, focus, **kwargs):
        """
        Create a new pronunciation attempt with audio processing.
        """
        focus_obj = get_object_or_404(PronunciationFocus, id=focus)
        
        # Handle audio file
        recording = kwargs.get('recording')
        
        # If recording is base64 encoded string, convert to file
        if isinstance(recording, str) and recording.startswith('data:audio'):
            format, imgstr = recording.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f"pronunciation_{focus}_{timezone.now().timestamp()}.{ext}"
            )
            recording = data
        
        # Create attempt
        attempt = PronunciationAttempt.objects.create(
            user=request.user,
            focus=focus_obj,
            chunk=focus_obj.chunk,  # For backward compatibility
            attempt_number=kwargs.get('attempt_number'),
            cycle_number=kwargs.get('cycle_number'),
            recording=recording,
            attempt_type=kwargs.get('attempt_type', 'practice')
        )
        
        # TODO: Integrate with AI service for pronunciation analysis
        # This would be an async task in production
        # For now, we'll simulate AI processing
        attempt = self._process_with_ai(attempt)
        
        # Update mastery record
        self._update_mastery(request.user, focus_obj, attempt)
        
        log_user_activity(
            request.user,
            'pronunciation_attempt_completed',
            {
                'focus_id': focus,
                'score': attempt.ai_score,
                'attempt_type': attempt.attempt_type,
                'attempt_number': kwargs.get('attempt_number'),
                'cycle_number': kwargs.get('cycle_number')
            }
        )
        
        return attempt
    
    def _process_with_ai(self, attempt):
        """
        Simulate AI processing of pronunciation.
        In production, this would call an external AI service.
        """
        # Simulate AI analysis
        import random
        
        # Generate random score between 60-100 for demo
        attempt.ai_score = random.randint(60, 100)
        
        # Generate feedback based on score
        if attempt.ai_score >= 90:
            attempt.ai_feedback = "Excellent pronunciation! Your intonation and stress patterns are perfect."
        elif attempt.ai_score >= 75:
            attempt.ai_feedback = "Good job! A few minor issues with vowel sounds, but overall very clear."
        elif attempt.ai_score >= 60:
            attempt.ai_feedback = "Getting there. Focus on word stress and practice the problematic sounds."
        else:
            attempt.ai_feedback = "Keep practicing. Try to slow down and focus on each sound individually."
        
        attempt.save()
        return attempt
    
    def _update_mastery(self, user, focus, attempt):
        """
        Update or create mastery record based on attempt.
        """
        mastery, created = PronunciationMastery.objects.get_or_create(
            user=user,
            focus=focus
        )
        
        # Update statistics
        mastery.total_attempts += 1
        mastery.last_score = attempt.ai_score
        mastery.last_attempted = attempt.created_at
        
        if mastery.best_score is None or attempt.ai_score > mastery.best_score:
            mastery.best_score = attempt.ai_score
        
        # Check if mastered (score >= 90)
        if attempt.ai_score >= 90 and not mastery.is_mastered:
            mastery.is_mastered = True
            mastery.mastered_at = attempt.created_at
        
        mastery.save()
    
    def create(self, request, *args, **kwargs):
        """
        Create a new pronunciation attempt.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Get focus
            focus_id = serializer.validated_data.get('focus_id')
            chunk_id = serializer.validated_data.get('chunk_id')
            
            # Resolve focus from chunk if needed
            if not focus_id and chunk_id:
                # Get first focus for this chunk (for backward compatibility)
                chunk = get_object_or_404(LessonChunk, id=chunk_id)
                focus = chunk.pronunciation_focuses.first()
                if focus:
                    focus_id = focus.id
                else:
                    raise ValidationError("No pronunciation focus found for this chunk")
            
            # Check if user can attempt
            info = self.validate_attempt_allowed(request.user, focus_id)
            
            # Create the attempt
            attempt = self.create_attempt(
                request=request,
                focus=focus_id,
                recording=serializer.validated_data.get('recording'),
                attempt_type=serializer.validated_data.get('attempt_type', 'practice'),
                attempt_number=info['attempt_number'],
                cycle_number=info['cycle_number']
            )
            
            return Response({
                'success': True,
                'attempt_id': attempt.id,
                'score': attempt.ai_score,
                'feedback': attempt.ai_feedback,
                'is_passed': attempt.is_passed,
                'cycle_number': info['cycle_number'],
                'attempt_number': info['attempt_number'],
                'attempts_remaining': info['attempts_remaining'],
                'message': 'Pronunciation attempt processed successfully'
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            log_user_activity(
                request.user,
                'pronunciation_attempt_error',
                {'error': str(e)}
            )
            return Response({
                'success': False,
                'error': 'Failed to process pronunciation attempt'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get practice summary statistics.
        """
        user = request.user
        attempts = self.get_queryset()
        
        total = attempts.count()
        passed = attempts.filter(ai_score__gte=90).count()
        practice = attempts.filter(attempt_type='practice')
        tests = attempts.filter(attempt_type='test')
        
        summary = {
            'total_attempts': total,
            'passed_attempts': passed,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'average_score': attempts.aggregate(avg=Avg('ai_score'))['avg'],
            'best_score': attempts.aggregate(best=Max('ai_score'))['best'],
            'practice_attempts': practice.count(),
            'test_attempts': tests.count(),
            'average_practice_score': practice.aggregate(avg=Avg('ai_score'))['avg'],
            'average_test_score': tests.aggregate(avg=Avg('ai_score'))['avg'],
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['post'])
    def simulate_ai_analysis(self, request):
        """
        Simulate AI analysis for testing purposes.
        In production, this would be handled by a background task.
        """
        attempt_id = request.data.get('attempt_id')
        if not attempt_id:
            return Response(
                {'error': 'attempt_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            attempt = PronunciationAttempt.objects.get(id=attempt_id)
            attempt = self._process_with_ai(attempt)
            
            return Response({
                'success': True,
                'attempt_id': attempt.id,
                'score': attempt.ai_score,
                'feedback': attempt.ai_feedback
            })
            
        except PronunciationAttempt.DoesNotExist:
            return Response(
                {'error': 'Attempt not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============================================================
# MASTERY VIEWS
# ============================================================

class PronunciationMasteryViewSet(BaseViewSet, UserFilterMixin):
    """
    ViewSet for pronunciation mastery tracking.
    
    Provides:
    - List user's mastery records
    - Get mastery statistics
    - Update mastery (admin only)
    - Mobile-optimized endpoints
    """
    
    queryset = PronunciationMastery.objects.all()
    serializer_class = PronunciationMasterySerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'list' and self.request.GET.get('mobile') == 'true':
            return PronunciationMasteryMobileSerializer
        
        if self.action in ['partial_update', 'update']:
            return PronunciationMasteryUpdateSerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter to current user and add optimizations.
        """
        queryset = super().get_queryset()
        
        # Filter by focus
        focus_id = self.request.query_params.get('focus_id')
        if focus_id:
            queryset = queryset.filter(focus_id=focus_id)
        
        # Filter by mastery status
        mastered = self.request.query_params.get('mastered')
        if mastered is not None:
            is_mastered = mastered.lower() == 'true'
            queryset = queryset.filter(is_mastered=is_mastered)
        
        return queryset.select_related('focus')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get mastery summary statistics.
        """
        user = request.user
        mastery_records = self.get_queryset()
        
        total_focuses = PronunciationFocus.objects.count()
        
        summary = {
            'total_focuses': total_focuses,
            'mastered_count': mastery_records.filter(is_mastered=True).count(),
            'in_progress_count': mastery_records.filter(
                is_mastered=False,
                total_attempts__gt=0
            ).count(),
            'not_started_count': total_focuses - mastery_records.count(),
            'mastery_percentage': (
                mastery_records.filter(is_mastered=True).count() / total_focuses * 100
            ) if total_focuses > 0 else 0,
            'average_best_score': mastery_records.aggregate(avg=Avg('best_score'))['avg'],
            'recently_mastered': []
        }
        
        # Get recently mastered (last 7 days)
        recent = mastery_records.filter(
            is_mastered=True,
            mastered_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('focus')[:5]
        
        for mastery in recent:
            summary['recently_mastered'].append({
                'focus_id': mastery.focus_id,
                'focus_title': mastery.focus.focus_title,
                'best_score': mastery.best_score,
                'mastered_at': mastery.mastered_at
            })
        
        return Response(summary)


# ============================================================
# PROGRESS VIEWS
# ============================================================

class PronunciationProgressViewSet(ProgressViewSet):
    """
    ViewSet for pronunciation progress tracking.
    """
    
    serializer_class = PronunciationProgressSummarySerializer
    
    def get_user_progress(self, user):
        """
        Get pronunciation progress for user.
        """
        # Get all focuses
        total_focuses = PronunciationFocus.objects.count()
        
        # Get mastery records
        mastery_records = PronunciationMastery.objects.filter(user=user)
        mastered = mastery_records.filter(is_mastered=True)
        in_progress = mastery_records.filter(is_mastered=False, total_attempts__gt=0)
        
        # Get attempts
        attempts = PronunciationAttempt.objects.filter(user=user)
        practice_attempts = attempts.filter(attempt_type='practice')
        test_attempts = attempts.filter(attempt_type='test')
        
        # Calculate statistics
        total_attempts = attempts.count()
        avg_score = attempts.aggregate(avg=Avg('ai_score'))['avg']
        best_score = mastery_records.aggregate(best=Max('best_score'))['best']
        
        # Get recently mastered
        recently_mastered = mastered.filter(
            mastered_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('focus')[:5]
        
        # Determine needs review
        needs_review = []
        now = timezone.now()
        for mastery in in_progress:
            if mastery.last_attempted:
                days_since = (now - mastery.last_attempted).days
                if days_since >= 7:  # Needs review if not practiced for a week
                    needs_review.append(mastery)
        
        progress_data = {
            'total_focuses': total_focuses,
            'mastered_focuses': mastered.count(),
            'in_progress_focuses': in_progress.count(),
            'not_started_focuses': total_focuses - mastery_records.count(),
            'mastery_percentage': (mastered.count() / total_focuses * 100) if total_focuses > 0 else 0,
            
            'total_attempts': total_attempts,
            'average_score': avg_score,
            'best_score': best_score,
            
            'practice_attempts': practice_attempts.count(),
            'test_attempts': test_attempts.count(),
            
            'total_time_spent': 0,  # Pronunciation attempts don't track time in models
            
            'last_activity': attempts.order_by('-created_at').first().created_at if attempts.exists() else None,
            
            'recently_mastered': PronunciationMasterySerializer(recently_mastered, many=True).data,
            'needs_review_count': len(needs_review)
        }
        
        return progress_data
    
    @action(detail=False, methods=['get'])
    def focus_progress(self, request):
        """
        Get progress for specific pronunciation focuses.
        """
        user = request.user
        focus_ids = request.query_params.getlist('focus_ids')
        
        if not focus_ids:
            return Response(
                {'error': 'focus_ids parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        focuses = PronunciationFocus.objects.filter(id__in=focus_ids)
        progress_data = []
        
        for focus in focuses:
            # Get mastery
            try:
                mastery = PronunciationMastery.objects.get(
                    user=user,
                    focus=focus
                )
            except PronunciationMastery.DoesNotExist:
                mastery = None
            
            # Get attempts
            attempts = PronunciationAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-created_at')
            
            latest_attempt = attempts.first()
            
            # Calculate current cycle info
            if latest_attempt:
                current_cycle = latest_attempt.cycle_number
                current_attempt = latest_attempt.attempt_number
                
                if latest_attempt.is_passed:
                    attempts_remaining = 3
                else:
                    attempts_remaining = 3 - latest_attempt.attempt_number
            else:
                current_cycle = 1
                current_attempt = 0
                attempts_remaining = 3
            
            # Determine next action
            if mastery and mastery.is_mastered:
                next_action = 'mastered'
            elif latest_attempt and latest_attempt.is_passed:
                next_action = 'test'
            else:
                next_action = 'practice'
            
            progress_data.append({
                'focus_id': focus.id,
                'focus_title': focus.focus_title,
                'sequence_order': focus.sequence_order,
                'current_cycle': current_cycle,
                'current_attempt': current_attempt,
                'attempts_remaining': attempts_remaining,
                'best_score': mastery.best_score if mastery else None,
                'last_score': mastery.last_score if mastery else None,
                'average_score': attempts.aggregate(avg=Avg('ai_score'))['avg'],
                'is_mastered': mastery.is_mastered if mastery else False,
                'mastery_threshold_reached': latest_attempt.is_passed if latest_attempt else False,
                'last_attempted': latest_attempt.created_at if latest_attempt else None,
                'first_attempted': attempts.last().created_at if attempts.exists() else None,
                'next_action': next_action,
                'suggested_focus': None  # Can be implemented based on performance
            })
        
        return Response(progress_data)


# ============================================================
# AUDIO PROCESSING VIEWS
# ============================================================

class PronunciationAudioViewSet(viewsets.GenericViewSet):
    """
    ViewSet for audio processing and analysis.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """
        Analyze pronunciation audio without saving attempt.
        Used for real-time feedback during practice.
        """
        audio_file = request.FILES.get('audio')
        focus_id = request.data.get('focus_id')
        
        if not audio_file or not focus_id:
            return Response(
                {'error': 'audio file and focus_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simulate AI analysis
        import random
        
        analysis = {
            'score': random.randint(60, 100),
            'feedback': {
                'overall': "Good pronunciation with minor issues.",
                'strengths': ['Clear consonants', 'Good rhythm'],
                'weaknesses': ['Vowel length', 'Word stress'],
                'phonemes': {
                    'correct': ['/p/', '/t/', '/k/'],
                    'incorrect': ['/θ/', '/ð/']
                }
            },
            'detailed_scores': {
                'accuracy': random.randint(60, 100),
                'fluency': random.randint(60, 100),
                'intonation': random.randint(60, 100)
            }
        }
        
        return Response(analysis)
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload audio file for later processing.
        """
        audio_file = request.FILES.get('audio')
        focus_id = request.data.get('focus_id')
        attempt_type = request.data.get('attempt_type', 'practice')
        
        if not audio_file or not focus_id:
            return Response(
                {'error': 'audio file and focus_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create a pending attempt
        focus = get_object_or_404(PronunciationFocus, id=focus_id)
        
        attempt = PronunciationAttempt.objects.create(
            user=request.user,
            focus=focus,
            chunk=focus.chunk,
            recording=audio_file,
            attempt_type=attempt_type,
            attempt_number=1,  # Will be updated after validation
            cycle_number=1
        )
        
        return Response({
            'success': True,
            'attempt_id': attempt.id,
            'message': 'Audio uploaded successfully, processing will complete shortly'
        }, status=status.HTTP_201_CREATED)


# ============================================================
# BULK OPERATION VIEWS
# ============================================================

class PronunciationBulkOperationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for bulk operations on pronunciation data.
    Admin-only endpoints for content management.
    """
    
    permission_classes = [IsAuthenticated]  # Add admin check
    
    @action(detail=False, methods=['post'])
    def create_focuses(self, request):
        """
        Bulk create pronunciation focuses for a chunk.
        """
        serializer = PronunciationBulkFocusCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        chunk_id = serializer.validated_data['chunk_id']
        focuses_data = serializer.validated_data['focuses']
        
        chunk = get_object_or_404(LessonChunk, id=chunk_id)
        
        created_focuses = []
        with transaction.atomic():
            for f_data in focuses_data:
                focus = PronunciationFocus.objects.create(
                    chunk=chunk,
                    focus_title=f_data['focus_title'],
                    focus_description=f_data.get('focus_description', ''),
                    sequence_order=f_data['sequence_order']
                )
                created_focuses.append(focus.id)
        
        log_user_activity(
            request.user,
            'bulk_create_pronunciation_focuses',
            {
                'chunk_id': chunk_id,
                'count': len(created_focuses)
            }
        )
        
        return Response({
            'success': True,
            'message': f'Created {len(created_focuses)} pronunciation focuses',
            'focus_ids': created_focuses
        }, status=status.HTTP_201_CREATED)