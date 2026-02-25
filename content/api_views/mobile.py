# api_views/mobile.py

"""
Mobile-optimized API views for efficient data transfer to mobile clients.
Provides lightweight endpoints, batch operations, and sync capabilities.
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
from datetime import timedelta
import hashlib
import json

from content.models.core import Textbook, Unit, Lesson, LessonChunk
from content.models.grammar import (
    ChunkGrammarFocus, GrammarQuestion,
    GrammarPracticeAttempt, GrammarTestAttempt
)
from content.models.punctuation import (
    ChunkPunctuationFocus, PunctuationQuestion,
    PunctuationPracticeAttempt, PunctuationTestAttempt
)
from content.models.vocabulary import (
    VocabularyItem, VocabularyAttempt, StudentVocabMastery
)
from content.models.comprehension import (
    ChunkComprehensionFocus, ComprehensionQuestion,
    ComprehensionPracticeAttempt, ComprehensionTestAttempt
)
from content.models.writing import (
    ChunkWritingFocus, UnitWritingTask, WritingPrompt,
    WritingPracticeAttempt, WritingTestAttempt
)
from content.models.pronunciation import (
    PronunciationFocus, PronunciationAttempt, PronunciationMastery
)
from content.models.testing import (
    UnitTestSession, UnitTestQuestion, UnitTestAnswer
)

from content.serializers.mobile import (
    # Core mobile
    LessonChunkMobileSerializer, LessonMobileSerializer,
    UnitMobileSerializer, TextbookMobileSerializer,
    UnitWithLessonsMobileSerializer, LessonWithChunksMobileSerializer,
    
    # Grammar mobile
    GrammarQuestionMobileSerializer, ChunkGrammarFocusMobileSerializer,
    GrammarPracticeAttemptMobileSerializer, GrammarTestAttemptMobileSerializer,
    
    # Punctuation mobile
    PunctuationQuestionMobileSerializer, ChunkPunctuationFocusMobileSerializer,
    PunctuationPracticeAttemptMobileSerializer, PunctuationTestAttemptMobileSerializer,
    
    # Vocabulary mobile
    VocabularyItemMobileSerializer, VocabularyAttemptMobileSerializer,
    StudentVocabMasteryMobileSerializer,
    
    # Comprehension mobile
    ComprehensionQuestionMobileSerializer, ChunkComprehensionFocusMobileSerializer,
    ComprehensionPracticeAttemptMobileSerializer, ComprehensionTestAttemptMobileSerializer,
    
    # Writing mobile
    WritingPromptMobileSerializer, ChunkWritingFocusMobileSerializer,
    UnitWritingTaskMobileSerializer, WritingPracticeAttemptMobileSerializer,
    WritingTestAttemptMobileSerializer,
    
    # Pronunciation mobile
    PronunciationFocusMobileSerializer, PronunciationAttemptMobileSerializer,
    PronunciationMasteryMobileSerializer,
    
    # Testing mobile
    UnitTestQuestionMobileSerializer, UnitTestSessionMobileSerializer,
    UnitTestSessionActiveMobileSerializer, UnitTestAnswerMobileSerializer,
    UnitTestHistoryMobileSerializer,
    
    # Mobile dashboard
    DomainProgressMobileSerializer, DashboardMobileSerializer,
    
    # Mobile submissions
    MobilePracticeSubmitSerializer, MobileTestSubmitSerializer,
    
    # Offline sync
    SyncPayloadSerializer, SyncResponseSerializer,
    
    # Batch operations
    MobileBatchContentSerializer, MobileBatchContentResponseSerializer,
    
    # Push notifications
    MobileNotificationSerializer
)
from .base import BaseViewSet, log_user_activity
from .progress import DashboardViewSet


# ============================================================
# MOBILE CONTENT VIEWS
# ============================================================

class MobileContentViewSet(viewsets.GenericViewSet):
    """
    Mobile-optimized content delivery endpoints.
    Provides lightweight content for efficient mobile browsing.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def textbooks(self, request):
        """
        Get lightweight list of textbooks for mobile.
        """
        textbooks = Textbook.objects.all().order_by('class_level', 'title')
        serializer = TextbookMobileSerializer(textbooks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def units(self, request):
        """
        Get lightweight list of units for a textbook.
        """
        textbook_id = request.query_params.get('textbook_id')
        if not textbook_id:
            return Response(
                {'error': 'textbook_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        units = Unit.objects.filter(textbook_id=textbook_id).order_by('number')
        serializer = UnitMobileSerializer(units, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def lessons(self, request):
        """
        Get lightweight list of lessons for a unit.
        """
        unit_id = request.query_params.get('unit_id')
        if not unit_id:
            return Response(
                {'error': 'unit_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lessons = Lesson.objects.filter(unit_id=unit_id).order_by('number')
        serializer = LessonMobileSerializer(lessons, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def chunks(self, request):
        """
        Get all chunks for a lesson.
        """
        lesson_id = request.query_params.get('lesson_id')
        if not lesson_id:
            return Response(
                {'error': 'lesson_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        chunks = LessonChunk.objects.filter(lesson_id=lesson_id).order_by('order')
        serializer = LessonChunkMobileSerializer(chunks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unit_with_lessons(self, request):
        """
        Get a unit with its lessons (for offline storage).
        """
        unit_id = request.query_params.get('unit_id')
        if not unit_id:
            return Response(
                {'error': 'unit_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        unit = get_object_or_404(Unit, id=unit_id)
        serializer = UnitWithLessonsMobileSerializer(unit)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def lesson_with_chunks(self, request):
        """
        Get a lesson with its chunks (for offline storage).
        """
        lesson_id = request.query_params.get('lesson_id')
        if not lesson_id:
            return Response(
                {'error': 'lesson_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lesson = get_object_or_404(Lesson, id=lesson_id)
        serializer = LessonWithChunksMobileSerializer(lesson)
        return Response(serializer.data)


# ============================================================
# MOBILE DOMAIN FOCUS VIEWS
# ============================================================

class MobileGrammarViewSet(viewsets.GenericViewSet):
    """
    Mobile-optimized grammar endpoints.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def focuses(self, request):
        """
        Get grammar focuses for a chunk.
        """
        chunk_id = request.query_params.get('chunk_id')
        if not chunk_id:
            return Response(
                {'error': 'chunk_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        focuses = ChunkGrammarFocus.objects.filter(chunk_id=chunk_id).order_by('sequence_order')
        serializer = ChunkGrammarFocusMobileSerializer(focuses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def questions(self, request):
        """
        Get grammar questions for a focus.
        """
        focus_id = request.query_params.get('focus_id')
        if not focus_id:
            return Response(
                {'error': 'focus_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        questions = GrammarQuestion.objects.filter(focus_id=focus_id)
        serializer = GrammarQuestionMobileSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def practice_history(self, request):
        """
        Get user's grammar practice history.
        """
        user = request.user
        focus_id = request.query_params.get('focus_id')
        
        attempts = GrammarPracticeAttempt.objects.filter(user=user)
        if focus_id:
            attempts = attempts.filter(focus_id=focus_id)
        
        attempts = attempts.order_by('-attempted_at')[:20]
        serializer = GrammarPracticeAttemptMobileSerializer(attempts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def test_history(self, request):
        """
        Get user's grammar test history.
        """
        user = request.user
        focus_id = request.query_params.get('focus_id')
        
        attempts = GrammarTestAttempt.objects.filter(user=user)
        if focus_id:
            attempts = attempts.filter(focus_id=focus_id)
        
        attempts = attempts.order_by('-created_at')[:20]
        serializer = GrammarTestAttemptMobileSerializer(attempts, many=True)
        return Response(serializer.data)


class MobilePunctuationViewSet(viewsets.GenericViewSet):
    """
    Mobile-optimized punctuation endpoints.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def focuses(self, request):
        """
        Get punctuation focuses for a chunk.
        """
        chunk_id = request.query_params.get('chunk_id')
        if not chunk_id:
            return Response(
                {'error': 'chunk_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        focuses = ChunkPunctuationFocus.objects.filter(chunk_id=chunk_id).order_by('sequence_order')
        serializer = ChunkPunctuationFocusMobileSerializer(focuses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def questions(self, request):
        """
        Get punctuation questions for a focus.
        """
        focus_id = request.query_params.get('focus_id')
        if not focus_id:
            return Response(
                {'error': 'focus_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        questions = PunctuationQuestion.objects.filter(focus_id=focus_id)
        serializer = PunctuationQuestionMobileSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def practice_history(self, request):
        """
        Get user's punctuation practice history.
        """
        user = request.user
        focus_id = request.query_params.get('focus_id')
        
        attempts = PunctuationPracticeAttempt.objects.filter(user=user)
        if focus_id:
            attempts = attempts.filter(focus_id=focus_id)
        
        attempts = attempts.order_by('-created_at')[:20]
        serializer = PunctuationPracticeAttemptMobileSerializer(attempts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def test_history(self, request):
        """
        Get user's punctuation test history.
        """
        user = request.user
        focus_id = request.query_params.get('focus_id')
        
        attempts = PunctuationTestAttempt.objects.filter(user=user)
        if focus_id:
            attempts = attempts.filter(focus_id=focus_id)
        
        attempts = attempts.order_by('-created_at')[:20]
        serializer = PunctuationTestAttemptMobileSerializer(attempts, many=True)
        return Response(serializer.data)


class MobileVocabularyViewSet(viewsets.GenericViewSet):
    """
    Mobile-optimized vocabulary endpoints.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def items(self, request):
        """
        Get vocabulary items for a lesson or chunk.
        """
        lesson_id = request.query_params.get('lesson_id')
        chunk_id = request.query_params.get('chunk_id')
        
        items = VocabularyItem.objects.all()
        if lesson_id:
            items = items.filter(lesson_id=lesson_id)
        elif chunk_id:
            items = items.filter(chunk_id=chunk_id)
        else:
            return Response(
                {'error': 'Either lesson_id or chunk_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = VocabularyItemMobileSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mastery(self, request):
        """
        Get user's vocabulary mastery status.
        """
        user = request.user
        mastery = StudentVocabMastery.objects.filter(user=user).select_related('vocab_item')
        
        # Filter by level if provided
        level = request.query_params.get('level')
        if level:
            mastery = mastery.filter(mastery_level=level)
        
        serializer = StudentVocabMasteryMobileSerializer(mastery, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def needs_review(self, request):
        """
        Get vocabulary items needing review.
        """
        user = request.user
        from .vocabulary import StudentVocabMasteryViewSet
        
        viewset = StudentVocabMasteryViewSet()
        viewset.request = request
        response = viewset.needs_review(request)
        return response
    
    @action(detail=False, methods=['get'])
    def practice_history(self, request):
        """
        Get user's vocabulary practice history.
        """
        user = request.user
        item_id = request.query_params.get('item_id')
        
        attempts = VocabularyAttempt.objects.filter(user=user)
        if item_id:
            attempts = attempts.filter(vocab_item_id=item_id)
        
        attempts = attempts.order_by('-created_at')[:50]
        serializer = VocabularyAttemptMobileSerializer(attempts, many=True)
        return Response(serializer.data)


class MobileComprehensionViewSet(viewsets.GenericViewSet):
    """
    Mobile-optimized comprehension endpoints.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def focuses(self, request):
        """
        Get comprehension focuses for a chunk.
        """
        chunk_id = request.query_params.get('chunk_id')
        if not chunk_id:
            return Response(
                {'error': 'chunk_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        focuses = ChunkComprehensionFocus.objects.filter(chunk_id=chunk_id).order_by('sequence_order')
        serializer = ChunkComprehensionFocusMobileSerializer(focuses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def questions(self, request):
        """
        Get comprehension questions for a focus.
        """
        focus_id = request.query_params.get('focus_id')
        if not focus_id:
            return Response(
                {'error': 'focus_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        questions = ComprehensionQuestion.objects.filter(focus_id=focus_id)
        serializer = ComprehensionQuestionMobileSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def practice_history(self, request):
        """
        Get user's comprehension practice history.
        """
        user = request.user
        focus_id = request.query_params.get('focus_id')
        
        attempts = ComprehensionPracticeAttempt.objects.filter(user=user)
        if focus_id:
            attempts = attempts.filter(focus_id=focus_id)
        
        attempts = attempts.order_by('-attempted_at')[:20]
        serializer = ComprehensionPracticeAttemptMobileSerializer(attempts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def test_history(self, request):
        """
        Get user's comprehension test history.
        """
        user = request.user
        focus_id = request.query_params.get('focus_id')
        
        attempts = ComprehensionTestAttempt.objects.filter(user=user)
        if focus_id:
            attempts = attempts.filter(focus_id=focus_id)
        
        attempts = attempts.order_by('-created_at')[:20]
        serializer = ComprehensionTestAttemptMobileSerializer(attempts, many=True)
        return Response(serializer.data)


class MobileWritingViewSet(viewsets.GenericViewSet):
    """
    Mobile-optimized writing endpoints.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def chunk_focuses(self, request):
        """
        Get chunk-level writing focuses.
        """
        chunk_id = request.query_params.get('chunk_id')
        if not chunk_id:
            return Response(
                {'error': 'chunk_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        focuses = ChunkWritingFocus.objects.filter(chunk_id=chunk_id).order_by('sequence_order')
        serializer = ChunkWritingFocusMobileSerializer(focuses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unit_tasks(self, request):
        """
        Get unit-level writing tasks.
        """
        unit_id = request.query_params.get('unit_id')
        if not unit_id:
            return Response(
                {'error': 'unit_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = UnitWritingTask.objects.filter(unit_id=unit_id).order_by('order')
        serializer = UnitWritingTaskMobileSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def prompts(self, request):
        """
        Get writing prompts for a focus or task.
        """
        focus_id = request.query_params.get('focus_id')
        task_id = request.query_params.get('task_id')
        
        prompts = WritingPrompt.objects.all()
        if focus_id:
            prompts = prompts.filter(focus_id=focus_id)
        elif task_id:
            prompts = prompts.filter(task_id=task_id)
        else:
            return Response(
                {'error': 'Either focus_id or task_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = WritingPromptMobileSerializer(prompts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def practice_history(self, request):
        """
        Get user's writing practice history.
        """
        user = request.user
        focus_id = request.query_params.get('focus_id')
        
        attempts = WritingPracticeAttempt.objects.filter(user=user)
        if focus_id:
            attempts = attempts.filter(focus_id=focus_id)
        
        attempts = attempts.order_by('-created_at')[:20]
        serializer = WritingPracticeAttemptMobileSerializer(attempts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def test_history(self, request):
        """
        Get user's writing test history.
        """
        user = request.user
        focus_id = request.query_params.get('focus_id')
        task_id = request.query_params.get('task_id')
        
        attempts = WritingTestAttempt.objects.filter(user=user)
        if focus_id:
            attempts = attempts.filter(focus_id=focus_id)
        elif task_id:
            attempts = attempts.filter(task_id=task_id)
        
        attempts = attempts.order_by('-created_at')[:20]
        serializer = WritingTestAttemptMobileSerializer(attempts, many=True)
        return Response(serializer.data)


class MobilePronunciationViewSet(viewsets.GenericViewSet):
    """
    Mobile-optimized pronunciation endpoints.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def focuses(self, request):
        """
        Get pronunciation focuses for a chunk.
        """
        chunk_id = request.query_params.get('chunk_id')
        if not chunk_id:
            return Response(
                {'error': 'chunk_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        focuses = PronunciationFocus.objects.filter(chunk_id=chunk_id).order_by('sequence_order')
        serializer = PronunciationFocusMobileSerializer(focuses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mastery(self, request):
        """
        Get user's pronunciation mastery status.
        """
        user = request.user
        mastery = PronunciationMastery.objects.filter(user=user).select_related('focus')
        
        serializer = PronunciationMasteryMobileSerializer(mastery, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def practice_history(self, request):
        """
        Get user's pronunciation attempt history.
        """
        user = request.user
        focus_id = request.query_params.get('focus_id')
        
        attempts = PronunciationAttempt.objects.filter(user=user)
        if focus_id:
            attempts = attempts.filter(focus_id=focus_id)
        
        attempts = attempts.order_by('-created_at')[:20]
        serializer = PronunciationAttemptMobileSerializer(attempts, many=True)
        return Response(serializer.data)


class MobileTestingViewSet(viewsets.GenericViewSet):
    """
    Mobile-optimized testing endpoints.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get user's unit test history.
        """
        user = request.user
        sessions = UnitTestSession.objects.filter(user=user).order_by('-started_at')
        
        serializer = UnitTestHistoryMobileSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_session(self, request):
        """
        Get active test session for a unit.
        """
        user = request.user
        unit_id = request.query_params.get('unit_id')
        
        if not unit_id:
            return Response(
                {'error': 'unit_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session = UnitTestSession.objects.filter(
            user=user,
            unit_id=unit_id,
            completed_at__isnull=True
        ).first()
        
        if not session:
            return Response(
                {'error': 'No active session found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UnitTestSessionActiveMobileSerializer(session)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def session_questions(self, request):
        """
        Get questions for a test session.
        """
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response(
                {'error': 'session_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session = get_object_or_404(UnitTestSession, id=session_id, user=request.user)
        questions = session.questions.all().order_by('order')
        serializer = UnitTestQuestionMobileSerializer(questions, many=True)
        return Response(serializer.data)


# ============================================================
# MOBILE DASHBOARD VIEWS
# ============================================================

class MobileDashboardViewSet(viewsets.GenericViewSet):
    """
    Mobile-optimized dashboard endpoints.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get lightweight dashboard summary for mobile.
        """
        user = request.user
        
        # Use the existing DashboardViewSet but filter for mobile
        dashboard = DashboardViewSet()
        dashboard.request = request
        dashboard.action = 'summary'  # Set the action attribute
        
        # Get quick summary
        response = dashboard.summary(request)
        return response
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """
        Get recent activity feed for mobile.
        """
        user = request.user
        dashboard = DashboardViewSet()
        dashboard.request = request
        dashboard.action = 'recent_activity'  # Set the action attribute
        
        activities = dashboard._get_recent_activity(user, limit=10)
        return Response(activities)
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """
        Get personalized recommendations for mobile.
        """
        user = request.user
        dashboard = DashboardViewSet()
        dashboard.request = request
        dashboard.action = 'recommendations'  # Set the action attribute
        
        recommendations = dashboard._get_recommendations(user, limit=5)
        return Response(recommendations)
    
    @action(detail=False, methods=['get'])
    def streak(self, request):
        """
        Get current streak information.
        """
        user = request.user
        dashboard = DashboardViewSet()
        dashboard.request = request
        dashboard.action = 'streak'  # Set the action attribute
        
        streak_days = dashboard._calculate_streak(user)
        
        # Get last activity date
        from django.db.models.functions import TruncDate
        last_activity = None
        
        # Check various activity sources
        last_grammar = GrammarPracticeAttempt.objects.filter(
            user=user
        ).order_by('-attempted_at').first()
        
        if last_grammar:
            last_activity = last_grammar.attempted_at
        
        # Add more sources as needed
        
        return Response({
            'current_streak': streak_days,
            'last_activity': last_activity,
            'next_milestone': ((streak_days // 7) + 1) * 7
        })


# ============================================================
# MOBILE SUBMISSION VIEWS
# ============================================================

class MobileSubmissionViewSet(viewsets.GenericViewSet):
    """
    Unified submission endpoints for mobile.
    Handles practice and test submissions from mobile clients.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def submit_practice(self, request):
        """
        Unified practice submission for any domain.
        """
        serializer = MobilePracticeSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        domain = serializer.validated_data['domain']
        focus_id = serializer.validated_data.get('focus_id')
        item_id = serializer.validated_data.get('item_id')
        answers = serializer.validated_data.get('answers', [])
        time_spent = serializer.validated_data.get('time_spent_seconds')
        
        # Route to appropriate domain viewset
        try:
            if domain == 'grammar':
                from .grammar import GrammarPracticeViewSet
                viewset = GrammarPracticeViewSet()
                viewset.request = request
                viewset.action = 'create'  # Set the action attribute
                
                # Prepare data for grammar practice
                request.data['focus_id'] = focus_id
                request.data['answers'] = answers
                request.data['time_taken_seconds'] = time_spent
                
                response = viewset.create(request)
                return response
            
            elif domain == 'punctuation':
                from .punctuation import PunctuationPracticeViewSet
                viewset = PunctuationPracticeViewSet()
                viewset.request = request
                viewset.action = 'create'  # Set the action attribute
                
                request.data['focus_id'] = focus_id
                request.data['answers'] = answers
                request.data['time_taken_seconds'] = time_spent
                
                response = viewset.create(request)
                return response
            
            elif domain == 'vocabulary':
                from .vocabulary import VocabularyPracticeViewSet
                viewset = VocabularyPracticeViewSet()
                viewset.request = request
                
                # For vocabulary, we need to handle single vs batch
                if len(answers) == 1:
                    # Single attempt
                    viewset.action = 'create'  # Set the action attribute
                    request.data['vocab_item_id'] = item_id or answers[0].get('vocab_item_id')
                    request.data['is_correct'] = answers[0].get('is_correct')
                    request.data['time_taken_seconds'] = time_spent
                    
                    response = viewset.create(request)
                    return response
                else:
                    # Batch submission
                    viewset.action = 'batch_submit'  # Set the action attribute
                    request.data['attempts'] = [
                        {
                            'vocab_item_id': a.get('vocab_item_id'),
                            'is_correct': a.get('is_correct'),
                            'time_taken_seconds': a.get('time_taken_seconds')
                        }
                        for a in answers
                    ]
                    
                    response = viewset.batch_submit(request)
                    return response
            
            elif domain == 'comprehension':
                from .comprehension import ComprehensionPracticeViewSet
                viewset = ComprehensionPracticeViewSet()
                viewset.request = request
                viewset.action = 'create'  # Set the action attribute
                
                request.data['focus_id'] = focus_id
                request.data['answers'] = answers
                request.data['time_taken_seconds'] = time_spent
                
                response = viewset.create(request)
                return response
            
            elif domain == 'writing':
                from .writing import WritingPracticeViewSet
                viewset = WritingPracticeViewSet()
                viewset.request = request
                viewset.action = 'create'  # Set the action attribute
                
                request.data['focus_id'] = focus_id
                request.data['answers'] = answers
                request.data['response_text'] = answers[0].get('response_text') if answers else ''
                request.data['time_spent_seconds'] = time_spent
                
                response = viewset.create(request)
                return response
            
            elif domain == 'pronunciation':
                from .pronunciation import PronunciationAttemptViewSet
                viewset = PronunciationAttemptViewSet()
                viewset.request = request
                viewset.action = 'create'  # Set the action attribute
                
                # Handle audio data
                request.data['focus_id'] = focus_id
                request.data['recording'] = answers[0].get('recording') if answers else None
                
                response = viewset.create(request)
                return response
            
            else:
                return Response(
                    {'error': f'Unsupported domain: {domain}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            log_user_activity(
                request.user,
                'mobile_submit_practice_error',
                {'domain': domain, 'error': str(e)}
            )
            return Response(
                {'error': f'Failed to submit practice: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def submit_test(self, request):
        """
        Unified test submission for any domain.
        """
        serializer = MobileTestSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        domain = serializer.validated_data['domain']
        focus_id = serializer.validated_data.get('focus_id')
        task_id = serializer.validated_data.get('task_id')
        session_id = serializer.validated_data.get('session_id')
        answers = serializer.validated_data.get('answers', [])
        time_spent = serializer.validated_data.get('time_spent_seconds')
        
        # Route to appropriate domain viewset
        try:
            if domain == 'grammar':
                from .grammar import GrammarTestViewSet
                viewset = GrammarTestViewSet()
                viewset.request = request
                viewset.action = 'create'  # Set the action attribute
                
                request.data['focus_id'] = focus_id
                request.data['answers'] = answers
                request.data['time_taken_seconds'] = time_spent
                
                response = viewset.create(request)
                return response
            
            elif domain == 'punctuation':
                from .punctuation import PunctuationTestViewSet
                viewset = PunctuationTestViewSet()
                viewset.request = request
                viewset.action = 'create'  # Set the action attribute
                
                request.data['focus_id'] = focus_id
                request.data['answers'] = answers
                request.data['time_taken_seconds'] = time_spent
                
                response = viewset.create(request)
                return response
            
            elif domain == 'comprehension':
                from .comprehension import ComprehensionTestViewSet
                viewset = ComprehensionTestViewSet()
                viewset.request = request
                viewset.action = 'create'  # Set the action attribute
                
                request.data['focus_id'] = focus_id
                request.data['answers'] = answers
                request.data['time_taken_seconds'] = time_spent
                
                response = viewset.create(request)
                return response
            
            elif domain == 'writing':
                from .writing import WritingTestViewSet
                viewset = WritingTestViewSet()
                viewset.request = request
                viewset.action = 'create'  # Set the action attribute
                
                request.data['focus_id'] = focus_id
                request.data['task_id'] = task_id
                request.data['prompt_id'] = answers[0].get('prompt_id') if answers else None
                request.data['response_text'] = answers[0].get('response_text') if answers else ''
                request.data['time_spent_seconds'] = time_spent
                
                response = viewset.create(request)
                return response
            
            elif domain == 'pronunciation':
                from .pronunciation import PronunciationAttemptViewSet
                viewset = PronunciationAttemptViewSet()
                viewset.request = request
                viewset.action = 'create'  # Set the action attribute
                
                request.data['focus_id'] = focus_id
                request.data['attempt_type'] = 'test'
                request.data['recording'] = answers[0].get('recording') if answers else None
                
                response = viewset.create(request)
                return response
            
            elif domain == 'unit_test':
                from .testing import UnitTestSessionViewSet
                viewset = UnitTestSessionViewSet()
                viewset.request = request
                viewset.action = 'submit'  # Set the action attribute
                
                # For unit test, we need to call the submit method with pk
                # Create a copy of request with modified data
                from django.test import RequestFactory
                factory = RequestFactory()
                submit_request = factory.post('/', {
                    'session_id': session_id,
                    'answers': answers,
                    'time_taken_seconds': time_spent
                }, format='json')
                submit_request.user = request.user
                submit_request._dont_enforce_csrf_checks = True
                
                response = viewset.submit(submit_request, pk=session_id)
                return response
            
            else:
                return Response(
                    {'error': f'Unsupported domain: {domain}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            log_user_activity(
                request.user,
                'mobile_submit_test_error',
                {'domain': domain, 'error': str(e)}
            )
            return Response(
                {'error': f'Failed to submit test: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================
# MOBILE SYNC VIEWS
# ============================================================

class MobileSyncViewSet(viewsets.GenericViewSet):
    """
    Synchronization endpoints for offline mobile clients.
    Handles uploading pending data and downloading updates.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Synchronize data between mobile client and server.
        """
        serializer = SyncPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        pending_practices = serializer.validated_data.get('pending_practices', [])
        pending_tests = serializer.validated_data.get('pending_tests', [])
        last_sync = serializer.validated_data.get('last_sync_timestamp')
        
        results = {
            'synced_practices': [],
            'synced_tests': [],
            'updated_content': {},
            'server_timestamp': timezone.now()
        }
        
        # Process pending practices
        for practice_data in pending_practices:
            try:
                # Use the unified submission endpoint
                submission_viewset = MobileSubmissionViewSet()
                submission_viewset.request = request
                submission_viewset.action = 'submit_practice'  # Set the action attribute
                
                # Create a new request for this practice
                from django.test import RequestFactory
                factory = RequestFactory()
                sync_request = factory.post('/', practice_data, format='json')
                sync_request.user = request.user
                sync_request._dont_enforce_csrf_checks = True
                
                response = submission_viewset.submit_practice(sync_request)
                
                if response.status_code == 201:
                    results['synced_practices'].append({
                        'original': practice_data,
                        'success': True,
                        'response': response.data
                    })
                else:
                    results['synced_practices'].append({
                        'original': practice_data,
                        'success': False,
                        'error': response.data.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                results['synced_practices'].append({
                    'original': practice_data,
                    'success': False,
                    'error': str(e)
                })
        
        # Process pending tests
        for test_data in pending_tests:
            try:
                submission_viewset = MobileSubmissionViewSet()
                submission_viewset.request = request
                submission_viewset.action = 'submit_test'  # Set the action attribute
                
                factory = RequestFactory()
                sync_request = factory.post('/', test_data, format='json')
                sync_request.user = request.user
                sync_request._dont_enforce_csrf_checks = True
                
                response = submission_viewset.submit_test(sync_request)
                
                if response.status_code == 201:
                    results['synced_tests'].append({
                        'original': test_data,
                        'success': True,
                        'response': response.data
                    })
                else:
                    results['synced_tests'].append({
                        'original': test_data,
                        'success': False,
                        'error': response.data.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                results['synced_tests'].append({
                    'original': test_data,
                    'success': False,
                    'error': str(e)
                })
        
        # Get updated content since last sync
        if last_sync:
            results['updated_content'] = self._get_updated_content(last_sync, request.user)
        
        log_user_activity(
            request.user,
            'mobile_sync',
            {
                'practices_synced': len(results['synced_practices']),
                'tests_synced': len(results['synced_tests'])
            }
        )
        
        return Response(results)
    
    def _get_updated_content(self, since_timestamp, user):
        """
        Get content that has been updated since the given timestamp.
        """
        updated = {}
        
        # Check for updated textbooks
        textbooks = Textbook.objects.filter(updated_at__gte=since_timestamp)
        if textbooks.exists():
            updated['textbooks'] = TextbookMobileSerializer(textbooks, many=True).data
        
        # Check for updated units
        units = Unit.objects.filter(updated_at__gte=since_timestamp)
        if units.exists():
            updated['units'] = UnitMobileSerializer(units, many=True).data
        
        # Check for updated lessons
        lessons = Lesson.objects.filter(updated_at__gte=since_timestamp)
        if lessons.exists():
            updated['lessons'] = LessonMobileSerializer(lessons, many=True).data
        
        # Check for updated chunks
        chunks = LessonChunk.objects.filter(updated_at__gte=since_timestamp)
        if chunks.exists():
            updated['chunks'] = LessonChunkMobileSerializer(chunks, many=True).data
        
        # Check for user's updated progress data
        updated['progress'] = self._get_updated_progress(since_timestamp, user)
        
        return updated
    
    def _get_updated_progress(self, since_timestamp, user):
        """
        Get user progress data updated since timestamp.
        """
        progress = {}
        
        # Grammar practice attempts
        grammar_practice = GrammarPracticeAttempt.objects.filter(
            user=user,
            attempted_at__gte=since_timestamp
        )
        if grammar_practice.exists():
            progress['grammar_practice'] = GrammarPracticeAttemptMobileSerializer(
                grammar_practice, many=True
            ).data
        
        # Grammar test attempts
        grammar_test = GrammarTestAttempt.objects.filter(
            user=user,
            created_at__gte=since_timestamp
        )
        if grammar_test.exists():
            progress['grammar_test'] = GrammarTestAttemptMobileSerializer(
                grammar_test, many=True
            ).data
        
        # Vocabulary mastery updates
        vocab_mastery = StudentVocabMastery.objects.filter(
            user=user,
            updated_at__gte=since_timestamp
        )
        if vocab_mastery.exists():
            progress['vocabulary_mastery'] = StudentVocabMasteryMobileSerializer(
                vocab_mastery, many=True
            ).data
        
        # Unit test sessions
        test_sessions = UnitTestSession.objects.filter(
            user=user,
            completed_at__gte=since_timestamp
        )
        if test_sessions.exists():
            progress['unit_tests'] = UnitTestSessionMobileSerializer(
                test_sessions, many=True
            ).data
        
        return progress
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get sync status (pending items count, last sync time).
        """
        user = request.user
        
        # Count pending items (not applicable for server - client tracks this)
        # Instead, return last activity and server version info
        
        last_activity = None
        
        # Check various activity sources
        last_grammar = GrammarPracticeAttempt.objects.filter(
            user=user
        ).order_by('-attempted_at').first()
        
        if last_grammar:
            last_activity = last_grammar.attempted_at
        
        # Add more sources...
        
        return Response({
            'user_id': user.id,
            'last_activity': last_activity,
            'server_time': timezone.now(),
            'api_version': '1.0',
            'content_version': self._get_content_version()
        })
    
    def _get_content_version(self):
        """
        Get current content version hash.
        """
        # Simple hash of latest updates across content models
        content_hash = hashlib.md5()
        
        latest_textbook = Textbook.objects.order_by('-updated_at').first()
        if latest_textbook:
            content_hash.update(str(latest_textbook.updated_at.timestamp()).encode())
        
        latest_unit = Unit.objects.order_by('-updated_at').first()
        if latest_unit:
            content_hash.update(str(latest_unit.updated_at.timestamp()).encode())
        
        latest_lesson = Lesson.objects.order_by('-updated_at').first()
        if latest_lesson:
            content_hash.update(str(latest_lesson.updated_at.timestamp()).encode())
        
        return content_hash.hexdigest()[:8]


# ============================================================
# MOBILE BATCH VIEWS
# ============================================================

class MobileBatchViewSet(viewsets.GenericViewSet):
    """
    Batch operations for mobile to reduce API calls.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def get_content(self, request):
        """
        Get multiple content items in one request.
        """
        serializer = MobileBatchContentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        textbook_ids = serializer.validated_data.get('textbook_ids', [])
        unit_ids = serializer.validated_data.get('unit_ids', [])
        lesson_ids = serializer.validated_data.get('lesson_ids', [])
        chunk_ids = serializer.validated_data.get('chunk_ids', [])
        
        response_data = {}
        
        # Fetch textbooks
        if textbook_ids:
            textbooks = Textbook.objects.filter(id__in=textbook_ids)
            response_data['textbooks'] = TextbookMobileSerializer(textbooks, many=True).data
        
        # Fetch units
        if unit_ids:
            units = Unit.objects.filter(id__in=unit_ids)
            response_data['units'] = UnitMobileSerializer(units, many=True).data
        
        # Fetch lessons
        if lesson_ids:
            lessons = Lesson.objects.filter(id__in=lesson_ids)
            response_data['lessons'] = LessonMobileSerializer(lessons, many=True).data
        
        # Fetch chunks
        if chunk_ids:
            chunks = LessonChunk.objects.filter(id__in=chunk_ids)
            response_data['chunks'] = LessonChunkMobileSerializer(chunks, many=True).data
        
        # Fetch domain-specific content based on chunks
        if chunk_ids:
            chunks_qs = LessonChunk.objects.filter(id__in=chunk_ids)
            
            # Grammar focuses
            grammar_focuses = ChunkGrammarFocus.objects.filter(chunk__in=chunks_qs)
            if grammar_focuses.exists():
                response_data['grammar_focuses'] = ChunkGrammarFocusMobileSerializer(
                    grammar_focuses, many=True
                ).data
            
            # Punctuation focuses
            punct_focuses = ChunkPunctuationFocus.objects.filter(chunk__in=chunks_qs)
            if punct_focuses.exists():
                response_data['punctuation_focuses'] = ChunkPunctuationFocusMobileSerializer(
                    punct_focuses, many=True
                ).data
            
            # Vocabulary items
            vocab_items = VocabularyItem.objects.filter(chunk__in=chunks_qs)
            if vocab_items.exists():
                response_data['vocabulary_items'] = VocabularyItemMobileSerializer(
                    vocab_items, many=True
                ).data
            
            # Comprehension focuses
            comp_focuses = ChunkComprehensionFocus.objects.filter(chunk__in=chunks_qs)
            if comp_focuses.exists():
                response_data['comprehension_focuses'] = ChunkComprehensionFocusMobileSerializer(
                    comp_focuses, many=True
                ).data
            
            # Writing focuses
            writing_focuses = ChunkWritingFocus.objects.filter(chunk__in=chunks_qs)
            if writing_focuses.exists():
                response_data['writing_focuses'] = ChunkWritingFocusMobileSerializer(
                    writing_focuses, many=True
                ).data
            
            # Pronunciation focuses
            pron_focuses = PronunciationFocus.objects.filter(chunk__in=chunks_qs)
            if pron_focuses.exists():
                response_data['pronunciation_focuses'] = PronunciationFocusMobileSerializer(
                    pron_focuses, many=True
                ).data
        
        log_user_activity(
            request.user,
            'mobile_batch_content',
            {
                'textbooks': len(textbook_ids),
                'units': len(unit_ids),
                'lessons': len(lesson_ids),
                'chunks': len(chunk_ids)
            }
        )
        
        return Response(response_data)
    
    @action(detail=False, methods=['post'])
    def mark_completed(self, request):
        """
        Mark multiple items as completed in one request.
        """
        items = request.data.get('items', [])
        
        results = []
        for item in items:
            item_type = item.get('type')
            item_id = item.get('id')
            
            # This would integrate with your progress tracking
            # For now, just log and return success
            results.append({
                'type': item_type,
                'id': item_id,
                'success': True
            })
        
        return Response({
            'success': True,
            'results': results
        })


# ============================================================
# MOBILE NOTIFICATION VIEWS
# ============================================================

class MobileNotificationViewSet(viewsets.GenericViewSet):
    """
    Push notification registration and management.
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def register_device(self, request):
        """
        Register a device for push notifications.
        """
        device_token = request.data.get('device_token')
        device_type = request.data.get('device_type', 'ios')  # ios, android, web
        
        if not device_token:
            return Response(
                {'error': 'device_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store device token in user profile or separate model
        # This would be implemented based on your notification service
        
        log_user_activity(
            request.user,
            'mobile_register_device',
            {'device_type': device_type}
        )
        
        return Response({
            'success': True,
            'message': 'Device registered successfully'
        })
    
    @action(detail=False, methods=['post'])
    def unregister_device(self, request):
        """
        Unregister a device from push notifications.
        """
        device_token = request.data.get('device_token')
        
        if not device_token:
            return Response(
                {'error': 'device_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove device token
        
        return Response({
            'success': True,
            'message': 'Device unregistered successfully'
        })
    
    @action(detail=False, methods=['get'])
    def preferences(self, request):
        """
        Get user's notification preferences.
        """
        # Get from user profile
        preferences = {
            'practice_reminders': True,
            'test_reminders': True,
            'achievement_alerts': True,
            'streak_alerts': True,
            'content_updates': False,
            'reminder_time': '09:00',
            'frequency': 'daily'
        }
        
        return Response(preferences)
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """
        Update notification preferences.
        """
        preferences = request.data.get('preferences', {})
        
        # Save to user profile
        
        log_user_activity(
            request.user,
            'mobile_update_notification_preferences',
            preferences
        )
        
        return Response({
            'success': True,
            'message': 'Preferences updated successfully'
        })