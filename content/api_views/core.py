# api_views/core.py

"""
Core content views for textbooks, units, lessons, and chunks.
Provides endpoints for browsing and retrieving learning content.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.db.models import Prefetch, Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

from content.models.core import Textbook, Unit, Lesson, LessonChunk
from content.models.vocabulary import VocabularyItem
from content.serializers.core import (
    # Textbook serializers
    TextbookSerializer,
    TextbookListMobileSerializer,
    
    # Unit serializers
    UnitSerializer,
    UnitListMobileSerializer,
    
    # Lesson serializers
    LessonSerializer,
    LessonListMobileSerializer,
    
    # Lesson chunk serializers
    LessonChunkSerializer,
    LessonChunkMasterySerializer,
    
    # Mastery serializers
    ChunkMasteryDetailsSerializer,
)
from .base import ReadOnlyViewSet, UserFilterMixin, MultipleFieldLookupMixin, log_user_activity


# ============================================================
# TEXTBOOK VIEWS
# ============================================================

class TextbookViewSet(ReadOnlyViewSet):
    """
    ViewSet for viewing textbooks.
    
    Provides:
    - List all textbooks (with unit counts)
    - Retrieve single textbook with all units
    - Get textbooks by level
    - Mobile-optimized endpoints
    """
    
    queryset = Textbook.objects.all()
    serializer_class = TextbookSerializer
    lookup_field = 'pk'
    
    # Additional lookup fields for slugs or custom IDs
    lookup_fields = ['pk', 'id']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'list':
            # Check if mobile requested
            if self.request.GET.get('mobile') == 'true':
                return TextbookListMobileSerializer
            return TextbookSerializer  # Using TextbookSerializer for list view
        
        if self.action == 'retrieve':
            return TextbookSerializer
        
        if self.action == 'by_level':
            return TextbookSerializer
        
        if self.action == 'mobile_list':
            return TextbookListMobileSerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Optimize queryset with annotations and prefetches.
        """
        queryset = super().get_queryset()
        
        # Annotate with unit count
        queryset = queryset.annotate(
            unit_count=Count('units', distinct=True)
        )
        
        # For detail view, prefetch units and their lessons
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'units',
                    queryset=Unit.objects.all().order_by('number')
                )
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """
        Get textbooks filtered by class level.
        Query param: ?level=9th
        """
        level = request.query_params.get('level')
        if not level:
            return Response(
                {'error': 'Level parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        textbooks = self.get_queryset().filter(class_level=level)
        serializer = self.get_serializer(textbooks, many=True)
        
        log_user_activity(
            request.user,
            'view_textbooks_by_level',
            {'level': level, 'count': textbooks.count()}
        )
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mobile_list(self, request):
        """
        Ultra-lightweight textbook list for mobile.
        Returns only essential fields.
        """
        textbooks = self.get_queryset().only('id', 'title', 'class_level')
        serializer = TextbookListMobileSerializer(textbooks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        Get user's progress through this textbook.
        """
        textbook = self.get_object()
        user = request.user
        
        # Calculate progress across all units
        total_units = textbook.units.count()
        completed_units = 0
        
        for unit in textbook.units.all():
            # Check if unit is completed (all lessons mastered)
            unit_completed = True
            for lesson in unit.lessons.all():
                for chunk in lesson.chunks.all():
                    if not chunk.is_mastered_by(user):
                        unit_completed = False
                        break
                if not unit_completed:
                    break
            
            if unit_completed:
                completed_units += 1
        
        progress_data = {
            'textbook_id': textbook.id,
            'textbook_title': textbook.title,
            'total_units': total_units,
            'completed_units': completed_units,
            'progress_percentage': (completed_units / total_units * 100) if total_units > 0 else 0,
            'last_accessed': None  # Could track this in a separate model
        }
        
        return Response(progress_data)


# ============================================================
# UNIT VIEWS
# ============================================================

class UnitViewSet(ReadOnlyViewSet, MultipleFieldLookupMixin):
    """
    ViewSet for viewing units within textbooks.
    
    Provides:
    - List units in a textbook
    - Retrieve single unit with lessons
    - Get unit progress
    - Mobile-optimized endpoints
    """
    
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    lookup_field = 'pk'
    lookup_fields = ['pk', 'number']  # Allow lookup by unit number within textbook
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'list':
            if self.request.GET.get('mobile') == 'true':
                return UnitListMobileSerializer
            return UnitSerializer  # Using UnitSerializer for list view
        
        if self.action == 'retrieve':
            return UnitSerializer
        
        if self.action == 'mobile_list':
            return UnitListMobileSerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Optimize queryset with prefetches.
        """
        queryset = super().get_queryset()
        
        # Filter by textbook if provided
        textbook_id = self.request.query_params.get('textbook_id')
        if textbook_id:
            queryset = queryset.filter(textbook_id=textbook_id)
        
        # Annotate with lesson count
        queryset = queryset.annotate(
            lesson_count=Count('lessons', distinct=True)
        )
        
        # For detail view, prefetch lessons
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'lessons',
                    queryset=Lesson.objects.all().order_by('number')
                )
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def mobile_list(self, request):
        """
        Lightweight unit list for mobile.
        """
        textbook_id = request.query_params.get('textbook_id')
        if not textbook_id:
            return Response(
                {'error': 'textbook_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        units = self.get_queryset().filter(textbook_id=textbook_id)
        serializer = UnitListMobileSerializer(units, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        Get user's progress through this unit.
        """
        unit = self.get_object()
        user = request.user
        
        # Calculate lesson completion
        total_lessons = unit.lessons.count()
        completed_lessons = 0
        lesson_progress = []
        
        for lesson in unit.lessons.all().order_by('number'):
            # Check if lesson is completed
            lesson_completed = True
            for chunk in lesson.chunks.all():
                if not chunk.is_mastered_by(user):
                    lesson_completed = False
                    break
            
            if lesson_completed:
                completed_lessons += 1
            
            lesson_progress.append({
                'lesson_id': lesson.id,
                'lesson_number': lesson.number,
                'lesson_title': lesson.title,
                'completed': lesson_completed
            })
        
        # Get test progress
        from content.models.testing import UnitTestSession
        test_sessions = UnitTestSession.objects.filter(
            user=user,
            unit=unit
        ).order_by('-attempt_number')
        
        test_progress = {
            'attempts': test_sessions.count(),
            'best_score': test_sessions.order_by('-score_percentage').first().score_percentage if test_sessions.exists() else None,
            'passed': test_sessions.filter(passed=True).exists(),
            'latest_score': test_sessions.first().score_percentage if test_sessions.exists() else None
        }
        
        progress_data = {
            'unit_id': unit.id,
            'unit_number': unit.number,
            'unit_title': unit.title,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percentage': (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0,
            'lesson_progress': lesson_progress,
            'test_progress': test_progress
        }
        
        log_user_activity(
            request.user,
            'view_unit_progress',
            {'unit_id': unit.id, 'progress': progress_data['progress_percentage']}
        )
        
        return Response(progress_data)


# ============================================================
# LESSON VIEWS
# ============================================================

class LessonViewSet(ReadOnlyViewSet, MultipleFieldLookupMixin):
    """
    ViewSet for viewing lessons within units.
    
    Provides:
    - List lessons in a unit
    - Retrieve single lesson with chunks
    - Get lesson progress and mastery
    - Mobile-optimized endpoints
    """
    
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    lookup_field = 'pk'
    lookup_fields = ['pk', 'number']  # Allow lookup by lesson number within unit
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'list':
            if self.request.GET.get('mobile') == 'true':
                return LessonListMobileSerializer
            return LessonSerializer  # Using LessonSerializer for list view
        
        if self.action == 'retrieve':
            return LessonSerializer
        
        if self.action == 'mobile_list':
            return LessonListMobileSerializer
        
        if self.action == 'chunks':
            return LessonChunkSerializer
        
        if self.action == 'mastery':
            return LessonChunkMasterySerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Optimize queryset with prefetches.
        """
        queryset = super().get_queryset()
        
        # Filter by unit if provided
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        
        # Annotate with chunk count
        queryset = queryset.annotate(
            chunk_count=Count('chunks', distinct=True)
        )
        
        # For detail view, prefetch chunks
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'chunks',
                    queryset=LessonChunk.objects.all().order_by('order')
                )
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def mobile_list(self, request):
        """
        Lightweight lesson list for mobile.
        """
        unit_id = request.query_params.get('unit_id')
        if not unit_id:
            return Response(
                {'error': 'unit_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lessons = self.get_queryset().filter(unit_id=unit_id)
        serializer = LessonListMobileSerializer(lessons, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        """
        Get all chunks for a lesson.
        """
        lesson = self.get_object()
        chunks = lesson.chunks.all().order_by('order')
        serializer = LessonChunkSerializer(chunks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def mastery(self, request, pk=None):
        """
        Get mastery status for all chunks in this lesson.
        """
        lesson = self.get_object()
        chunks = lesson.chunks.all().order_by('order')
        
        # Use mastery serializer with user context
        serializer = LessonChunkMasterySerializer(
            chunks,
            many=True,
            context={'request': request}
        )
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        Get detailed progress for this lesson.
        """
        lesson = self.get_object()
        user = request.user
        
        chunks = lesson.chunks.all().order_by('order')
        total_chunks = chunks.count()
        mastered_chunks = 0
        chunk_progress = []
        
        for chunk in chunks:
            is_mastered = chunk.is_mastered_by(user)
            if is_mastered:
                mastered_chunks += 1
            
            status = chunk.get_mastery_status(user)
            
            chunk_progress.append({
                'chunk_id': chunk.id,
                'order': chunk.order,
                'mastered': is_mastered,
                'next_domain': status.get('next_domain_to_work') if status else None,
                'estimated_time': chunk.estimated_time_minutes
            })
        
        progress_data = {
            'lesson_id': lesson.id,
            'lesson_number': lesson.number,
            'lesson_title': lesson.title,
            'total_chunks': total_chunks,
            'mastered_chunks': mastered_chunks,
            'progress_percentage': (mastered_chunks / total_chunks * 100) if total_chunks > 0 else 0,
            'estimated_total_minutes': lesson.chunks.aggregate(total=models.Sum('estimated_time_minutes'))['total'] or 0,
            'chunk_progress': chunk_progress,
            'next_chunk': next(
                (c for c in chunk_progress if not c['mastered']),
                None
            )
        }
        
        log_user_activity(
            request.user,
            'view_lesson_progress',
            {'lesson_id': lesson.id, 'progress': progress_data['progress_percentage']}
        )
        
        return Response(progress_data)


# ============================================================
# LESSON CHUNK VIEWS
# ============================================================

class LessonChunkViewSet(ReadOnlyViewSet):
    """
    ViewSet for viewing individual lesson chunks.
    
    Provides:
    - Retrieve single chunk
    - Get chunk mastery status
    - Get all focuses for a chunk (grammar, punctuation, etc.)
    """
    
    queryset = LessonChunk.objects.all()
    serializer_class = LessonChunkSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        """
        Optimize queryset.
        """
        queryset = super().get_queryset()
        
        # Filter by lesson if provided
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        
        return queryset
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'mastery':
            return LessonChunkMasterySerializer
        
        if self.action == 'focuses':
            return LessonChunkSerializer  # Will nest focuses via serializer
        
        return self.serializer_class
    
    @action(detail=True, methods=['get'])
    def mastery(self, request, pk=None):
        """
        Get detailed mastery status for this chunk.
        """
        chunk = self.get_object()
        serializer = LessonChunkMasterySerializer(
            chunk,
            context={'request': request}
        )
        
        log_user_activity(
            request.user,
            'view_chunk_mastery',
            {'chunk_id': chunk.id}
        )
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def focuses(self, request, pk=None):
        """
        Get all domain focuses for this chunk.
        """
        chunk = self.get_object()
        
        # Get all focuses from different domains
        focuses = {
            'grammar': [
                {
                    'id': f.id,
                    'title': f.focus_title,
                    'depth': f.depth_level,
                    'order': f.sequence_order
                }
                for f in chunk.grammar_focuses.all()
            ],
            'punctuation': [
                {
                    'id': f.id,
                    'title': f.focus_title,
                    'mark': f.mark.symbol,
                    'depth': f.depth_level,
                    'order': f.sequence_order
                }
                for f in chunk.punctuation_focuses.all()
            ],
            'vocabulary': [
                {
                    'id': item.id,
                    'word': item.word,
                    'part_of_speech': item.part_of_speech
                }
                for item in chunk.vocab_items.all()
            ],
            'comprehension': [
                {
                    'id': f.id,
                    'title': f.focus_title,
                    'level': f.level,
                    'depth': f.depth_level,
                    'order': f.sequence_order
                }
                for f in chunk.comprehension_focuses.all()
            ],
            'writing': [
                {
                    'id': f.id,
                    'title': f.focus_title,
                    'depth': f.depth_level,
                    'order': f.sequence_order
                }
                for f in chunk.writing_focuses.all()
            ],
            'pronunciation': [
                {
                    'id': f.id,
                    'title': f.focus_title,
                    'order': f.sequence_order
                }
                for f in chunk.pronunciation_focuses.all()
            ]
        }
        
        return Response(focuses)
    
    @action(detail=True, methods=['get'])
    def prerequisites(self, request, pk=None):
        """
        Check if user has mastered prerequisites for this chunk.
        """
        chunk = self.get_object()
        user = request.user
        
        # Get previous chunks in same lesson
        previous_chunks = LessonChunk.objects.filter(
            lesson=chunk.lesson,
            order__lt=chunk.order
        ).order_by('order')
        
        prerequisites_met = True
        missing = []
        
        for prev_chunk in previous_chunks:
            if not prev_chunk.is_mastered_by(user):
                prerequisites_met = False
                missing.append({
                    'chunk_id': prev_chunk.id,
                    'order': prev_chunk.order,
                    'title': f"Chunk {prev_chunk.order}"
                })
        
        return Response({
            'chunk_id': chunk.id,
            'prerequisites_met': prerequisites_met,
            'missing_prerequisites': missing,
            'can_proceed': prerequisites_met
        })


# ============================================================
# SEARCH VIEWS
# ============================================================

class SearchViewSet(viewsets.GenericViewSet):
    """
    Unified search across all content.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def all(self, request):
        """
        Search across all content types.
        Query param: ?q=search_term
        """
        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = {
            'textbooks': [],
            'units': [],
            'lessons': [],
            'vocabulary': []
        }
        
        # Search textbooks
        textbooks = Textbook.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )[:5]
        results['textbooks'] = [
            {'id': t.id, 'title': t.title, 'type': 'textbook'}
            for t in textbooks
        ]
        
        # Search units
        units = Unit.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).select_related('textbook')[:5]
        results['units'] = [
            {
                'id': u.id,
                'title': u.title,
                'textbook': u.textbook.title,
                'type': 'unit'
            }
            for u in units
        ]
        
        # Search lessons
        lessons = Lesson.objects.filter(
            Q(title__icontains=query) | Q(english_text__icontains=query)
        ).select_related('unit__textbook')[:5]
        results['lessons'] = [
            {
                'id': l.id,
                'title': l.title,
                'unit': l.unit.title,
                'textbook': l.unit.textbook.title,
                'type': 'lesson'
            }
            for l in lessons
        ]
        
        # Search vocabulary
        vocab = VocabularyItem.objects.filter(
            Q(word__icontains=query) | Q(meaning__icontains=query)
        ).select_related('lesson__unit__textbook')[:5]
        results['vocabulary'] = [
            {
                'id': v.id,
                'word': v.word,
                'meaning': v.meaning,
                'lesson': v.lesson.title,
                'type': 'vocabulary'
            }
            for v in vocab
        ]
        
        log_user_activity(
            request.user,
            'search',
            {'query': query, 'results_count': sum(len(r) for r in results.values())}
        )
        
        return Response(results)