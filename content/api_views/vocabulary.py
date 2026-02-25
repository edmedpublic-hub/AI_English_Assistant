# api_views/vocabulary.py

"""
Vocabulary domain views for practice, mastery tracking, and progress monitoring.
Provides endpoints for vocabulary learning and assessment.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import models, transaction
from django.db.models import Q, Prefetch, Count, Avg, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from content.models.vocabulary import (
    VocabularyItem,
    VocabularyAttempt,
    StudentVocabMastery
)
from content.models.core import Lesson, LessonChunk
from content.serializers.vocabulary import (
    # Vocabulary items
    VocabularyItemSerializer, VocabularyItemListSerializer,
    VocabularyItemDetailSerializer, VocabularyItemMobileSerializer,
    
    # Attempts
    VocabularyAttemptSerializer, VocabularyAttemptSubmitSerializer,
    VocabularyBatchAttemptSubmitSerializer,
    
    # Mastery
    StudentVocabMasterySerializer, StudentVocabMasteryUpdateSerializer,
    StudentVocabMasteryMobileSerializer,
    
    # Progress tracking
    VocabularyProgressSummarySerializer, VocabularyItemProgressSerializer,
    VocabularySessionSummarySerializer,
    
    # Bulk operations
    VocabularyBulkCreateSerializer, VocabularyBulkMasteryUpdateSerializer
)
from .base import (
    BaseViewSet, PracticeViewSet, ProgressViewSet,
    UserFilterMixin, IsOwnerOrReadOnly, log_user_activity
)


# ============================================================
# VOCABULARY ITEM VIEWS
# ============================================================

class VocabularyItemViewSet(BaseViewSet):
    """
    ViewSet for viewing vocabulary items.
    
    Provides:
    - List vocabulary items with filtering
    - Retrieve single item with details
    - Get items by lesson or chunk
    - Mobile-optimized endpoints
    """
    
    queryset = VocabularyItem.objects.all()
    serializer_class = VocabularyItemSerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'list':
            if self.request.GET.get('mobile') == 'true':
                return VocabularyItemMobileSerializer
            return VocabularyItemListSerializer
        
        if self.action == 'retrieve':
            return VocabularyItemDetailSerializer
        
        if self.action == 'mobile_list':
            return VocabularyItemMobileSerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Optimize queryset with filters and prefetches.
        """
        queryset = super().get_queryset()
        
        # Filter by lesson
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        
        # Filter by chunk
        chunk_id = self.request.query_params.get('chunk_id')
        if chunk_id:
            queryset = queryset.filter(chunk_id=chunk_id)
        
        # Filter by part of speech
        pos = self.request.query_params.get('part_of_speech')
        if pos:
            queryset = queryset.filter(part_of_speech=pos)
        
        # Search by word or meaning
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(word__icontains=search) | 
                Q(meaning__icontains=search) |
                Q(urdu__icontains=search)
            )
        
        # For detail view, prefetch mastery and attempts
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'mastery_records',
                'attempts'
            )
        
        return queryset.order_by('lesson__id', 'word')
    
    @action(detail=False, methods=['get'])
    def mobile_list(self, request):
        """
        Ultra-lightweight vocabulary list for mobile flashcards.
        """
        lesson_id = request.query_params.get('lesson_id')
        if not lesson_id:
            return Response(
                {'error': 'lesson_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        items = self.get_queryset().filter(lesson_id=lesson_id)
        serializer = VocabularyItemMobileSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def parts_of_speech(self, request):
        """
        Get all unique parts of speech.
        """
        pos_choices = VocabularyItem.PARTS_OF_SPEECH
        return Response([
            {'code': code, 'name': name}
            for code, name in pos_choices
        ])
    
    @action(detail=True, methods=['get'])
    def mastery(self, request, pk=None):
        """
        Get mastery status for this vocabulary item.
        """
        item = self.get_object()
        user = request.user
        
        try:
            mastery = StudentVocabMastery.objects.get(
                user=user,
                vocab_item=item
            )
            serializer = StudentVocabMasterySerializer(mastery)
            return Response(serializer.data)
        except StudentVocabMastery.DoesNotExist:
            return Response({
                'vocab_item_id': item.id,
                'word': item.word,
                'mastery_level': 'new',
                'mastery_level_display': 'New',
                'accuracy_percentage': 0,
                'total_attempts': 0,
                'correct_attempts': 0,
                'last_practiced': None
            })
    
    @action(detail=True, methods=['get'])
    def attempts(self, request, pk=None):
        """
        Get attempt history for this vocabulary item.
        """
        item = self.get_object()
        user = request.user
        
        attempts = VocabularyAttempt.objects.filter(
            user=user,
            vocab_item=item
        ).order_by('-created_at')
        
        serializer = VocabularyAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


# ============================================================
# VOCABULARY PRACTICE VIEWS
# ============================================================

class VocabularyPracticeViewSet(PracticeViewSet):
    """
    ViewSet for vocabulary practice attempts.
    
    Provides:
    - Submit single practice attempt
    - Submit batch attempts (for flashcard sessions)
    - List user's practice history
    - Get practice statistics
    """
    
    queryset = VocabularyAttempt.objects.all()
    serializer_class = VocabularyAttemptSerializer
    lookup_field = 'pk'
    
    # Override max attempts - vocabulary uses spaced repetition, not cycle limits
    max_attempts_per_cycle = None
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return VocabularyAttemptSubmitSerializer
        
        if self.action == 'batch_submit':
            return VocabularyBatchAttemptSubmitSerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter to current user's attempts.
        """
        queryset = super().get_queryset()
        
        # Filter by vocabulary item
        item_id = self.request.query_params.get('item_id')
        if item_id:
            queryset = queryset.filter(vocab_item_id=item_id)
        
        # Filter by session
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        if from_date:
            queryset = queryset.filter(created_at__gte=from_date)
        
        to_date = self.request.query_params.get('to_date')
        if to_date:
            queryset = queryset.filter(created_at__lte=to_date)
        
        return queryset
    
    def get_current_cycle_info(self, user, item):
        """
        Override: Vocabulary uses spaced repetition, not strict cycles.
        Returns next review info instead.
        """
        try:
            mastery = StudentVocabMastery.objects.get(
                user=user,
                vocab_item_id=item
            )
            
            # Calculate days since last practice
            if mastery.last_practiced:
                days_since = (timezone.now() - mastery.last_practiced).days
                
                # Determine if ready for review based on mastery level
                if mastery.mastery_level == 'mastered':
                    ready = days_since >= 30
                elif mastery.mastery_level == 'review':
                    ready = days_since >= 1
                elif mastery.mastery_level == 'learning':
                    ready = days_since >= 3
                else:  # new
                    ready = True
            else:
                ready = True
                days_since = None
            
            return {
                'ready_for_review': ready,
                'mastery_level': mastery.mastery_level,
                'days_since_last': days_since,
                'total_attempts': mastery.total_attempts
            }
            
        except StudentVocabMastery.DoesNotExist:
            return {
                'ready_for_review': True,
                'mastery_level': 'new',
                'days_since_last': None,
                'total_attempts': 0
            }
    
    def validate_attempt_allowed(self, user, item):
        """
        Validate that item is ready for review.
        """
        info = self.get_current_cycle_info(user, item)
        
        if not info['ready_for_review']:
            days_remaining = {
                'mastered': 30,
                'review': 1,
                'learning': 3
            }.get(info['mastery_level'], 0)
            
            days_since = info['days_since_last'] or 0
            remaining = days_remaining - days_since
            
            raise ValidationError(
                f"This item is not ready for review. "
                f"Next review in {remaining} days."
            )
        
        return info
    
    def create_attempt(self, request, item, **kwargs):
        """
        Create a single vocabulary practice attempt.
        """
        item_obj = get_object_or_404(VocabularyItem, id=item)
        is_correct = kwargs.get('is_correct')
        session_id = kwargs.get('session_id')
        time_taken = kwargs.get('time_taken_seconds')
        
        # Get or create mastery record
        mastery, created = StudentVocabMastery.objects.get_or_create(
            user=request.user,
            vocab_item=item_obj
        )
        
        # Update mastery based on response
        with transaction.atomic():
            # Create attempt
            attempt = VocabularyAttempt.objects.create(
                user=request.user,
                vocab_item=item_obj,
                session_id=session_id,
                cycle_number=kwargs.get('cycle_number', 1),
                is_correct=is_correct,
                time_taken_seconds=time_taken
            )
            
            # Update mastery statistics
            mastery.total_attempts += 1
            if is_correct:
                mastery.correct_attempts += 1
            mastery.last_practiced = timezone.now()
            
            # Update mastery level based on spaced repetition algorithm
            self._update_mastery_level(mastery)
            
            mastery.save()
        
        log_user_activity(
            request.user,
            'vocabulary_practice',
            {
                'item_id': item,
                'word': item_obj.word,
                'correct': is_correct,
                'session_id': session_id
            }
        )
        
        return attempt
    
    def _update_mastery_level(self, mastery):
        """
        Update mastery level based on performance and spaced repetition.
        """
        accuracy = mastery.accuracy_percentage
        
        # Simple algorithm - can be made more sophisticated
        if mastery.total_attempts >= 5 and accuracy >= 90:
            mastery.mastery_level = 'mastered'
        elif mastery.total_attempts >= 3:
            if accuracy >= 80:
                mastery.mastery_level = 'learning'
            elif accuracy <= 50:
                mastery.mastery_level = 'review'
            else:
                mastery.mastery_level = 'learning'
        elif mastery.total_attempts >= 1:
            if accuracy >= 70:
                mastery.mastery_level = 'learning'
            else:
                mastery.mastery_level = 'review'
    
    def create(self, request, *args, **kwargs):
        """
        Create a single practice attempt.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            item_id = serializer.validated_data.get('vocab_item_id')
            
            # Check if item is ready for review
            info = self.validate_attempt_allowed(request.user, item_id)
            
            # Create the attempt
            attempt = self.create_attempt(
                request=request,
                item=item_id,
                is_correct=serializer.validated_data.get('is_correct'),
                session_id=serializer.validated_data.get('session_id'),
                time_taken_seconds=serializer.validated_data.get('time_taken_seconds'),
                cycle_number=serializer.validated_data.get('cycle_number', 1)
            )
            
            # Get updated mastery
            mastery = StudentVocabMastery.objects.get(
                user=request.user,
                vocab_item_id=item_id
            )
            
            return Response({
                'success': True,
                'attempt_id': attempt.id,
                'correct': attempt.is_correct,
                'mastery_level': mastery.mastery_level,
                'mastery_level_display': mastery.get_mastery_level_display(),
                'accuracy': mastery.accuracy_percentage,
                'total_attempts': mastery.total_attempts,
                'message': 'Practice attempt recorded successfully'
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            log_user_activity(request.user, 'vocabulary_practice_error', {'error': str(e)})
            return Response({
                'success': False,
                'error': 'Failed to record practice attempt'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def batch_submit(self, request):
        """
        Submit multiple practice attempts from a flashcard session.
        """
        serializer = VocabularyBatchAttemptSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_id = serializer.validated_data['session_id']
        attempts_data = serializer.validated_data['attempts']
        
        results = []
        with transaction.atomic():
            for attempt_data in attempts_data:
                try:
                    attempt = self.create_attempt(
                        request=request,
                        item=attempt_data['vocab_item_id'],
                        is_correct=attempt_data['is_correct'],
                        session_id=session_id,
                        time_taken_seconds=attempt_data.get('time_taken_seconds'),
                        cycle_number=1
                    )
                    
                    mastery = StudentVocabMastery.objects.get(
                        user=request.user,
                        vocab_item_id=attempt_data['vocab_item_id']
                    )
                    
                    results.append({
                        'vocab_item_id': attempt_data['vocab_item_id'],
                        'success': True,
                        'attempt_id': attempt.id,
                        'mastery_level': mastery.mastery_level,
                        'accuracy': mastery.accuracy_percentage
                    })
                    
                except Exception as e:
                    results.append({
                        'vocab_item_id': attempt_data['vocab_item_id'],
                        'success': False,
                        'error': str(e)
                    })
        
        # Calculate session summary
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        
        log_user_activity(
            request.user,
            'vocabulary_batch_practice',
            {
                'session_id': session_id,
                'total_attempts': total,
                'successful': successful
            }
        )
        
        return Response({
            'success': True,
            'session_id': session_id,
            'total_attempts': total,
            'successful_attempts': successful,
            'results': results
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def session_summary(self, request):
        """
        Get summary of a practice session.
        """
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response(
                {'error': 'session_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attempts = self.get_queryset().filter(session_id=session_id)
        
        if not attempts.exists():
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        total = attempts.count()
        correct = attempts.filter(is_correct=True).count()
        
        # Get items practiced
        items_practiced = []
        for attempt in attempts.select_related('vocab_item').distinct('vocab_item'):
            mastery = StudentVocabMastery.objects.filter(
                user=request.user,
                vocab_item=attempt.vocab_item
            ).first()
            
            items_practiced.append({
                'item_id': attempt.vocab_item.id,
                'word': attempt.vocab_item.word,
                'attempts': attempts.filter(vocab_item=attempt.vocab_item).count(),
                'correct': attempts.filter(vocab_item=attempt.vocab_item, is_correct=True).count(),
                'mastery_level': mastery.mastery_level if mastery else 'new'
            })
        
        summary = {
            'session_id': session_id,
            'total_attempts': total,
            'correct_attempts': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0,
            'time_spent_seconds': attempts.aggregate(total=Sum('time_taken_seconds'))['total'],
            'items_practiced': items_practiced,
            'start_time': attempts.order_by('created_at').first().created_at,
            'end_time': attempts.order_by('-created_at').first().created_at
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get practice summary statistics.
        """
        user = request.user
        attempts = self.get_queryset()
        
        # Overall stats
        total = attempts.count()
        correct = attempts.filter(is_correct=True).count()
        
        # Last 7 days
        week_ago = timezone.now() - timezone.timedelta(days=7)
        week_attempts = attempts.filter(created_at__gte=week_ago)
        
        summary = {
            'total_attempts': total,
            'correct_attempts': correct,
            'overall_accuracy': (correct / total * 100) if total > 0 else 0,
            'unique_items': attempts.values('vocab_item').distinct().count(),
            'last_7_days': {
                'attempts': week_attempts.count(),
                'accuracy': (
                    week_attempts.filter(is_correct=True).count() / week_attempts.count() * 100
                ) if week_attempts.exists() else 0
            },
            'by_part_of_speech': []
        }
        
        # Group by part of speech
        for pos_code, pos_name in VocabularyItem.PARTS_OF_SPEECH:
            pos_attempts = attempts.filter(vocab_item__part_of_speech=pos_code)
            if pos_attempts.exists():
                pos_correct = pos_attempts.filter(is_correct=True).count()
                summary['by_part_of_speech'].append({
                    'part_of_speech': pos_code,
                    'name': pos_name,
                    'attempts': pos_attempts.count(),
                    'accuracy': (pos_correct / pos_attempts.count() * 100)
                })
        
        return Response(summary)


# ============================================================
# MASTERY VIEWS
# ============================================================

class StudentVocabMasteryViewSet(BaseViewSet, UserFilterMixin):
    """
    ViewSet for vocabulary mastery tracking.
    
    Provides:
    - List user's mastery records
    - Get items needing review
    - Update mastery levels (admin)
    - Mobile-optimized endpoints
    """
    
    queryset = StudentVocabMastery.objects.all()
    serializer_class = StudentVocabMasterySerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'list' and self.request.GET.get('mobile') == 'true':
            return StudentVocabMasteryMobileSerializer
        
        if self.action == 'needs_review' and self.request.GET.get('mobile') == 'true':
            return StudentVocabMasteryMobileSerializer
        
        if self.action in ['partial_update', 'update']:
            return StudentVocabMasteryUpdateSerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter to current user and add optimizations.
        """
        queryset = super().get_queryset()
        
        # Filter by mastery level
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(mastery_level=level)
        
        # Filter by vocabulary item
        item_id = self.request.query_params.get('item_id')
        if item_id:
            queryset = queryset.filter(vocab_item_id=item_id)
        
        # Select related for efficiency
        queryset = queryset.select_related('vocab_item')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def needs_review(self, request):
        """
        Get vocabulary items that need review today.
        Uses spaced repetition algorithm.
        """
        user = request.user
        mastery_records = self.get_queryset()
        
        needs_review = []
        now = timezone.now()
        
        for mastery in mastery_records:
            if not mastery.last_practiced:
                # New items need review
                needs_review.append(mastery)
                continue
            
            days_since = (now - mastery.last_practiced).days
            
            # Determine if needs review based on mastery level
            if mastery.mastery_level == 'mastered' and days_since >= 30:
                needs_review.append(mastery)
            elif mastery.mastery_level == 'review' and days_since >= 1:
                needs_review.append(mastery)
            elif mastery.mastery_level == 'learning' and days_since >= 3:
                needs_review.append(mastery)
        
        # Sort by priority (oldest first)
        needs_review.sort(key=lambda m: m.last_practiced or now)
        
        serializer = self.get_serializer(needs_review, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get mastery summary statistics.
        """
        user = request.user
        mastery_records = self.get_queryset()
        
        total_items = VocabularyItem.objects.count()
        
        summary = {
            'total_items': total_items,
            'mastered_count': mastery_records.filter(mastery_level='mastered').count(),
            'learning_count': mastery_records.filter(mastery_level='learning').count(),
            'review_count': mastery_records.filter(mastery_level='review').count(),
            'new_count': total_items - mastery_records.count(),
            'mastery_percentage': (
                mastery_records.filter(mastery_level='mastered').count() / total_items * 100
            ) if total_items > 0 else 0,
            'needs_review_count': len(self.needs_review(request).data),
            'by_part_of_speech': []
        }
        
        # Group by part of speech
        for pos_code, pos_name in VocabularyItem.PARTS_OF_SPEECH:
            pos_items = VocabularyItem.objects.filter(part_of_speech=pos_code)
            pos_mastery = mastery_records.filter(vocab_item__part_of_speech=pos_code)
            
            summary['by_part_of_speech'].append({
                'part_of_speech': pos_code,
                'name': pos_name,
                'total': pos_items.count(),
                'mastered': pos_mastery.filter(mastery_level='mastered').count(),
                'mastery_percentage': (
                    pos_mastery.filter(mastery_level='mastered').count() / pos_items.count() * 100
                ) if pos_items.exists() else 0
            })
        
        return Response(summary)
    
    @action(detail=False, methods=['post'])
    def reset_mastery(self, request):
        """
        Reset mastery for specified items (admin only).
        """
        # Check admin permission
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        item_ids = request.data.get('item_ids', [])
        user_id = request.data.get('user_id')
        
        if not item_ids or not user_id:
            return Response(
                {'error': 'item_ids and user_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Delete mastery records
            StudentVocabMastery.objects.filter(
                user_id=user_id,
                vocab_item_id__in=item_ids
            ).delete()
            
            # Delete attempt history
            VocabularyAttempt.objects.filter(
                user_id=user_id,
                vocab_item_id__in=item_ids
            ).delete()
        
        log_user_activity(
            request.user,
            'reset_vocabulary_mastery',
            {
                'target_user': user_id,
                'item_count': len(item_ids)
            }
        )
        
        return Response({
            'success': True,
            'message': f'Reset mastery for {len(item_ids)} items'
        })


# ============================================================
# PROGRESS VIEWS
# ============================================================

class VocabularyProgressViewSet(ProgressViewSet):
    """
    ViewSet for vocabulary progress tracking.
    """
    
    serializer_class = VocabularyProgressSummarySerializer
    
    def get_user_progress(self, user):
        """
        Get vocabulary progress summary for user.
        """
        # Get all items
        total_items = VocabularyItem.objects.count()
        
        # Get mastery records
        mastery_records = StudentVocabMastery.objects.filter(user=user)
        
        # Calculate distribution
        mastered_count = mastery_records.filter(mastery_level='mastered').count()
        learning_count = mastery_records.filter(mastery_level='learning').count()
        review_count = mastery_records.filter(mastery_level='review').count()
        new_count = total_items - mastery_records.count()
        
        # Get attempt stats
        attempts = VocabularyAttempt.objects.filter(user=user)
        total_attempts = attempts.count()
        correct_attempts = attempts.filter(is_correct=True).count()
        
        # Get recently mastered
        recently_mastered = mastery_records.filter(
            mastery_level='mastered',
            updated_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('vocab_item')[:5]
        
        # Get needs review
        needs_review = []
        now = timezone.now()
        for mastery in mastery_records.filter(mastery_level__in=['review', 'learning']):
            if mastery.last_practiced:
                days_since = (now - mastery.last_practiced).days
                if (mastery.mastery_level == 'review' and days_since >= 1) or \
                   (mastery.mastery_level == 'learning' and days_since >= 3):
                    needs_review.append(mastery)
        
        return {
            'total_items': total_items,
            'mastered_count': mastered_count,
            'learning_count': learning_count,
            'review_count': review_count,
            'new_count': new_count,
            'mastery_percentage': (mastered_count / total_items * 100) if total_items > 0 else 0,
            'total_attempts': total_attempts,
            'overall_accuracy': (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            'recently_mastered': StudentVocabMasterySerializer(recently_mastered, many=True).data,
            'needs_review': StudentVocabMasterySerializer(needs_review[:10], many=True).data,
            'last_activity': attempts.order_by('-created_at').first().created_at if attempts.exists() else None
        }
    
    @action(detail=False, methods=['get'])
    def item_progress(self, request):
        """
        Get detailed progress for specific vocabulary items.
        """
        user = request.user
        item_ids = request.query_params.getlist('item_ids')
        
        if not item_ids:
            return Response(
                {'error': 'item_ids parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        items = VocabularyItem.objects.filter(id__in=item_ids)
        progress_data = []
        
        for item in items:
            # Get mastery
            try:
                mastery = StudentVocabMastery.objects.get(
                    user=user,
                    vocab_item=item
                )
            except StudentVocabMastery.DoesNotExist:
                mastery = None
            
            # Get attempts
            attempts = VocabularyAttempt.objects.filter(
                user=user,
                vocab_item=item
            ).order_by('-created_at')
            
            # Calculate stats
            total_attempts = attempts.count()
            correct_attempts = attempts.filter(is_correct=True).count()
            
            # Determine next review
            next_review = None
            if mastery and mastery.last_practiced:
                if mastery.mastery_level == 'mastered':
                    next_review = mastery.last_practiced + timezone.timedelta(days=30)
                elif mastery.mastery_level == 'review':
                    next_review = mastery.last_practiced + timezone.timedelta(days=1)
                elif mastery.mastery_level == 'learning':
                    next_review = mastery.last_practiced + timezone.timedelta(days=3)
            
            progress_data.append({
                'vocab_item_id': item.id,
                'word': item.word,
                'part_of_speech': item.part_of_speech,
                'mastery_level': mastery.mastery_level if mastery else 'new',
                'accuracy': (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0,
                'total_attempts': total_attempts,
                'attempts_last_week': attempts.filter(
                    created_at__gte=timezone.now() - timezone.timedelta(days=7)
                ).count(),
                'first_attempted': attempts.last().created_at if attempts.exists() else None,
                'last_attempted': attempts.first().created_at if attempts.exists() else None,
                'needs_review': next_review and timezone.now() >= next_review if next_review else True,
                'next_review_date': next_review,
                'suggested_action': self._get_suggested_action(mastery, next_review)
            })
        
        return Response(progress_data)
    
    def _get_suggested_action(self, mastery, next_review):
        """
        Determine suggested action for a vocabulary item.
        """
        if not mastery:
            return 'practice_new'
        
        if mastery.mastery_level == 'mastered':
            if next_review and timezone.now() >= next_review:
                return 'review_mastered'
            return 'mastered'
        
        if mastery.mastery_level == 'review':
            return 'practice_review'
        
        if mastery.mastery_level == 'learning':
            return 'continue_practice'
        
        return 'practice_new'


# ============================================================
# FLASHCARD VIEWS
# ============================================================

class FlashcardViewSet(viewsets.GenericViewSet):
    """
    Specialized views for flashcard-style practice.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def deck(self, request):
        """
        Get a deck of flashcards for practice.
        Query params: ?count=20&level=review&lesson_id=1
        """
        user = request.user
        count = int(request.query_params.get('count', 20))
        level = request.query_params.get('level')  # review, learning, new, all
        lesson_id = request.query_params.get('lesson_id')
        
        # Base queryset
        if lesson_id:
            items = VocabularyItem.objects.filter(lesson_id=lesson_id)
        else:
            items = VocabularyItem.objects.all()
        
        # Filter by mastery level
        if level and level != 'all':
            if level == 'new':
                # Items with no mastery record
                mastered_ids = StudentVocabMastery.objects.filter(
                    user=user
                ).values_list('vocab_item_id', flat=True)
                items = items.exclude(id__in=mastered_ids)
            else:
                # Items at specific mastery level
                mastered_ids = StudentVocabMastery.objects.filter(
                    user=user,
                    mastery_level=level
                ).values_list('vocab_item_id', flat=True)
                items = items.filter(id__in=mastered_ids)
        
        # Prioritize items needing review
        needs_review_ids = []
        now = timezone.now()
        
        mastery_records = StudentVocabMastery.objects.filter(
            user=user,
            vocab_item__in=items
        ).select_related('vocab_item')
        
        for mastery in mastery_records:
            if mastery.last_practiced:
                days_since = (now - mastery.last_practiced).days
                if (mastery.mastery_level == 'mastered' and days_since >= 30) or \
                   (mastery.mastery_level == 'review' and days_since >= 1) or \
                   (mastery.mastery_level == 'learning' and days_since >= 3):
                    needs_review_ids.append(mastery.vocab_item_id)
        
        # Build deck: first items needing review, then random new items
        deck_ids = needs_review_ids[:count]
        
        if len(deck_ids) < count:
            # Add random items not in deck
            remaining = count - len(deck_ids)
            excluded_ids = deck_ids + list(mastery_records.exclude(
                vocab_item_id__in=deck_ids
            ).values_list('vocab_item_id', flat=True))
            
            random_items = items.exclude(
                id__in=excluded_ids
            ).order_by('?')[:remaining]
            
            deck_ids.extend([item.id for item in random_items])
        
        # Get full items
        deck = VocabularyItem.objects.filter(id__in=deck_ids)
        serializer = VocabularyItemMobileSerializer(deck, many=True)
        
        return Response({
            'deck_size': len(deck_ids),
            'cards': serializer.data,
            'session_id': f"flashcard_{timezone.now().timestamp()}"
        })
    
    @action(detail=False, methods=['post'])
    def submit_results(self, request):
        """
        Submit results of a flashcard session.
        """
        session_id = request.data.get('session_id')
        results = request.data.get('results', [])
        
        if not session_id or not results:
            return Response(
                {'error': 'session_id and results are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare batch data for practice viewset
        batch_data = {
            'session_id': session_id,
            'attempts': [
                {
                    'vocab_item_id': r['item_id'],
                    'is_correct': r['correct'],
                    'time_taken_seconds': r.get('time_taken')
                }
                for r in results
            ]
        }
        
        # Use VocabularyPracticeViewSet to process
        practice_viewset = VocabularyPracticeViewSet()
        practice_viewset.request = request
        practice_viewset.action = 'batch_submit'
        
        # Create a new request with batch data
        from django.test import RequestFactory
        factory = RequestFactory()
        mock_request = factory.post('/', batch_data, format='json')
        mock_request.user = request.user
        mock_request._dont_enforce_csrf_checks = True
        
        # Process using batch_submit
        response = practice_viewset.batch_submit(mock_request)
        
        return Response(response.data)


# ============================================================
# BULK OPERATION VIEWS (ADD THIS SECTION)
# ============================================================

class VocabularyBulkOperationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for bulk operations on vocabulary data.
    Admin-only endpoints for content management.
    """
    
    permission_classes = [IsAuthenticated]  # Add admin check later
    
    @action(detail=False, methods=['post'])
    def create_items(self, request):
        """
        Bulk create vocabulary items for a lesson.
        """
        serializer = VocabularyBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        lesson_id = serializer.validated_data['lesson_id']
        items_data = serializer.validated_data['items']
        
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        created_items = []
        with transaction.atomic():
            for item_data in items_data:
                item = VocabularyItem.objects.create(
                    lesson=lesson,
                    chunk_id=item_data.get('chunk_id'),
                    word=item_data['word'],
                    urdu=item_data.get('urdu', ''),
                    meaning=item_data.get('meaning', ''),
                    synonyms=item_data.get('synonyms', ''),
                    antonyms=item_data.get('antonyms', ''),
                    example_sentence=item_data.get('example_sentence', ''),
                    part_of_speech=item_data.get('part_of_speech', 'noun')
                )
                created_items.append(item.id)
        
        log_user_activity(
            request.user,
            'bulk_create_vocabulary_items',
            {
                'lesson_id': lesson_id,
                'count': len(created_items)
            }
        )
        
        return Response({
            'success': True,
            'message': f'Created {len(created_items)} vocabulary items',
            'item_ids': created_items
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def update_mastery(self, request):
        """
        Bulk update mastery levels for vocabulary items.
        """
        serializer = VocabularyBulkMasteryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updates = serializer.validated_data['updates']
        user_id = request.data.get('user_id')
        
        if not user_id:
            user_id = request.user.id
        
        updated_count = 0
        with transaction.atomic():
            for update_data in updates:
                mastery, created = StudentVocabMastery.objects.get_or_create(
                    user_id=user_id,
                    vocab_item_id=update_data['vocab_item_id']
                )
                mastery.mastery_level = update_data['mastery_level']
                mastery.save()
                updated_count += 1
        
        log_user_activity(
            request.user,
            'bulk_update_vocabulary_mastery',
            {
                'target_user': user_id,
                'count': updated_count
            }
        )
        
        return Response({
            'success': True,
            'message': f'Updated {updated_count} mastery records'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def assign_to_chunk(self, request):
        """
        Bulk assign vocabulary items to a chunk.
        """
        chunk_id = request.data.get('chunk_id')
        item_ids = request.data.get('item_ids', [])
        
        if not chunk_id or not item_ids:
            return Response(
                {'error': 'chunk_id and item_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        chunk = get_object_or_404(LessonChunk, id=chunk_id)
        
        updated_count = VocabularyItem.objects.filter(
            id__in=item_ids
        ).update(chunk=chunk)
        
        return Response({
            'success': True,
            'message': f'Assigned {updated_count} items to chunk'
        })


# ============================================================
# EXPORTS (Optional - for use in __init__.py)
# ============================================================

__all__ = [
    'VocabularyItemViewSet',
    'VocabularyPracticeViewSet',
    'StudentVocabMasteryViewSet',
    'VocabularyProgressViewSet',
    'FlashcardViewSet',
    'VocabularyBulkOperationViewSet',  # Added this
]