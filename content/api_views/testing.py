# api_views/testing.py

"""
Unit testing views for comprehensive assessment across all domains.
Provides endpoints for unit test generation, submission, and results tracking.
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
import random

from content.models.testing import (
    UnitTestSession, UnitTestQuestion, UnitTestAnswer,
    VocabularyUnitTestAttempt
)
from content.models.core import Unit, Lesson, LessonChunk
from content.models.vocabulary import VocabularyItem
from content.models.grammar import GrammarConcept, ChunkGrammarFocus, GrammarQuestion
from content.models.punctuation import PunctuationMark, ChunkPunctuationFocus, PunctuationQuestion
from content.models.comprehension import ChunkComprehensionFocus, ComprehensionQuestion, BloomLevel
from content.models.writing import UnitWritingTask, WritingPrompt
from content.models.pronunciation import PronunciationFocus

from content.serializers.testing import (
    # Test questions
    UnitTestQuestionSerializer, UnitTestQuestionListSerializer,
    UnitTestQuestionMobileSerializer,
    
    # Test answers
    UnitTestAnswerSerializer, UnitTestAnswerSubmitSerializer,
    UnitTestAnswerMobileSerializer,
    
    # Test sessions
    UnitTestSessionSerializer, UnitTestSessionListSerializer,
    UnitTestSessionCreateSerializer, UnitTestSessionSubmitSerializer,
    UnitTestSessionMobileSerializer, UnitTestSessionActiveMobileSerializer,
    
    # Domain-specific test attempts
    VocabularyUnitTestAttemptSerializer,
    
    # Progress tracking
    UnitTestDomainBreakdownSerializer, UnitTestHistorySerializer,
    UnitTestHistoryMobileSerializer, UnitTestPerformanceSerializer,
    
    # Bulk operations
    UnitTestBulkQuestionCreateSerializer,
    
    # Test generation
    TestGenerationConfigSerializer,
    
    # Legacy migration
    LegacyVocabularyTestSessionSerializer,
    LegacyVocabularyTestQuestionSerializer,
    LegacyVocabularyTestAnswerSerializer,
    LegacyVocabularyTestAttemptSerializer,
    LegacyToUnitTestMigrationSerializer
)
from .base import (
    BaseViewSet, TestViewSet, ProgressViewSet,
    UserFilterMixin, IsOwnerOrReadOnly, log_user_activity
)


# ============================================================
# UNIT TEST SESSION VIEWS
# ============================================================

class UnitTestSessionViewSet(BaseViewSet, UserFilterMixin):
    """
    ViewSet for unit test sessions.
    
    Provides:
    - Start a new test session
    - Submit test answers
    - Get test results and history
    - Mobile-optimized endpoints
    """
    
    queryset = UnitTestSession.objects.all()
    serializer_class = UnitTestSessionSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    # Maximum attempts per unit
    max_attempts_per_unit = 3
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'create':
            return UnitTestSessionCreateSerializer
        
        if self.action == 'submit':
            return UnitTestSessionSubmitSerializer
        
        if self.action == 'list':
            if self.request.GET.get('mobile') == 'true':
                return UnitTestSessionMobileSerializer
            return UnitTestSessionListSerializer
        
        if self.action == 'retrieve' and self.request.GET.get('mobile') == 'true':
            return UnitTestSessionMobileSerializer
        
        if self.action == 'active' and self.request.GET.get('mobile') == 'true':
            return UnitTestSessionActiveMobileSerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter to current user's sessions.
        """
        queryset = super().get_queryset()
        
        # Filter by unit
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter == 'completed':
            queryset = queryset.filter(completed_at__isnull=False)
        elif status_filter == 'in_progress':
            queryset = queryset.filter(completed_at__isnull=True)
        
        # Filter by pass/fail
        passed = self.request.query_params.get('passed')
        if passed is not None:
            is_passed = passed.lower() == 'true'
            queryset = queryset.filter(passed=is_passed)
        
        return queryset.select_related('unit').order_by('-started_at')
    
    def validate_new_session_allowed(self, user, unit_id):
        """
        Validate that user can start a new test session.
        """
        # Count existing attempts
        attempt_count = UnitTestSession.objects.filter(
            user=user,
            unit_id=unit_id
        ).count()
        
        if attempt_count >= self.max_attempts_per_unit:
            raise ValidationError(
                f"Maximum {self.max_attempts_per_unit} attempts reached for this unit"
            )
        
        # Check if there's an in-progress session
        in_progress = UnitTestSession.objects.filter(
            user=user,
            unit_id=unit_id,
            completed_at__isnull=True
        ).exists()
        
        if in_progress:
            raise ValidationError(
                "You already have an in-progress test for this unit"
            )
        
        return True
    
    def generate_test_questions(self, unit, attempt_number):
        """
        Generate questions for a unit test.
        Selects questions from all domains covered in the unit.
        """
        questions = []
        
        # Get all chunks in this unit
        chunks = LessonChunk.objects.filter(lesson__unit=unit)
        
        # Vocabulary questions (25% of test)
        vocab_items = VocabularyItem.objects.filter(chunk__in=chunks)
        if vocab_items.exists():
            # Select random vocabulary items
            selected = random.sample(
                list(vocab_items), 
                min(5, vocab_items.count())
            )
            for item in selected:
                questions.append({
                    'domain': 'vocabulary',
                    'question_type': 'mcq',
                    'question_text': f"What is the meaning of '{item.word}'?",
                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],  # Would be real options
                    'correct_answer': item.meaning,
                    'difficulty': 3,
                    'points': 1,
                    'vocabulary_item_id': item.id
                })
        
        # Grammar questions (25% of test)
        grammar_focuses = ChunkGrammarFocus.objects.filter(chunk__in=chunks)
        if grammar_focuses.exists():
            grammar_questions = GrammarQuestion.objects.filter(
                focus__in=grammar_focuses
            )
            if grammar_questions.exists():
                selected = random.sample(
                    list(grammar_questions),
                    min(5, grammar_questions.count())
                )
                for q in selected:
                    questions.append({
                        'domain': 'grammar',
                        'question_type': q.question_type,
                        'question_text': q.question_text,
                        'options': q.options,
                        'correct_answer': q.correct_answer,
                        'difficulty': q.difficulty,
                        'points': 1,
                        'grammar_concept_id': q.focus.concept_id
                    })
        
        # Punctuation questions (15% of test)
        punct_focuses = ChunkPunctuationFocus.objects.filter(chunk__in=chunks)
        if punct_focuses.exists():
            punct_questions = PunctuationQuestion.objects.filter(
                focus__in=punct_focuses
            )
            if punct_questions.exists():
                selected = random.sample(
                    list(punct_questions),
                    min(3, punct_questions.count())
                )
                for q in selected:
                    questions.append({
                        'domain': 'punctuation',
                        'question_type': q.question_type,
                        'question_text': q.question_text,
                        'options': q.options,
                        'correct_answer': q.correct_answer,
                        'difficulty': q.difficulty,
                        'points': 1,
                        'punctuation_mark_id': q.focus.mark_id
                    })
        
        # Comprehension questions (20% of test)
        comp_focuses = ChunkComprehensionFocus.objects.filter(chunk__in=chunks)
        if comp_focuses.exists():
            comp_questions = ComprehensionQuestion.objects.filter(
                focus__in=comp_focuses
            )
            if comp_questions.exists():
                selected = random.sample(
                    list(comp_questions),
                    min(4, comp_questions.count())
                )
                for q in selected:
                    questions.append({
                        'domain': 'comprehension',
                        'question_type': q.question_type,
                        'question_text': q.question_text,
                        'options': q.options,
                        'correct_answer': q.correct_answer,
                        'difficulty': q.difficulty,
                        'points': 1,
                        'bloom_level': q.focus.level
                    })
        
        # Writing prompt (10% of test - usually 1-2 prompts)
        writing_tasks = UnitWritingTask.objects.filter(unit=unit)
        if writing_tasks.exists():
            prompts = WritingPrompt.objects.filter(task__in=writing_tasks)
            if prompts.exists():
                selected = random.sample(
                    list(prompts),
                    min(1, prompts.count())
                )
                for p in selected:
                    questions.append({
                        'domain': 'writing',
                        'question_type': 'open_ended',
                        'question_text': p.prompt_text,
                        'options': [],
                        'correct_answer': '',  # Open-ended
                        'difficulty': p.task.difficulty_level if p.task else 3,
                        'points': 5,  # Writing questions worth more
                        'writing_prompt_id': p.id
                    })
        
        # Pronunciation (5% of test)
        pron_focuses = PronunciationFocus.objects.filter(chunk__in=chunks)
        if pron_focuses.exists():
            # Pronunciation questions would be added here
            # For now, we'll skip
            pass
        
        # Shuffle questions
        random.shuffle(questions)
        
        return questions
    
    def create(self, request, *args, **kwargs):
        """
        Start a new unit test session.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            unit_id = serializer.validated_data['unit_id']
            unit = get_object_or_404(Unit, id=unit_id)
            
            # Validate attempt allowed
            self.validate_new_session_allowed(request.user, unit_id)
            
            # Get attempt number
            attempt_count = UnitTestSession.objects.filter(
                user=request.user,
                unit=unit
            ).count()
            attempt_number = attempt_count + 1
            
            # Generate questions
            questions_data = self.generate_test_questions(unit, attempt_number)
            
            # Create session
            session = UnitTestSession.objects.create(
                user=request.user,
                unit=unit,
                attempt_number=attempt_number,
                total_questions=len(questions_data),
                test_data={
                    'questions': questions_data,
                    'version': '1.0',
                    'generated_at': timezone.now().isoformat()
                }
            )
            
            # Create question instances
            for order, q_data in enumerate(questions_data, start=1):
                UnitTestQuestion.objects.create(
                    session=session,
                    domain=q_data['domain'],
                    question_type=q_data['question_type'],
                    question_text=q_data['question_text'],
                    options=q_data.get('options', []),
                    correct_answer=q_data.get('correct_answer', ''),
                    difficulty=q_data.get('difficulty', 3),
                    order=order,
                    points=q_data.get('points', 1),
                    vocabulary_item_id=q_data.get('vocabulary_item_id'),
                    grammar_concept_id=q_data.get('grammar_concept_id'),
                    punctuation_mark_id=q_data.get('punctuation_mark_id'),
                    bloom_level=q_data.get('bloom_level')
                )
            
            log_user_activity(
                request.user,
                'unit_test_started',
                {
                    'unit_id': unit_id,
                    'attempt_number': attempt_number,
                    'question_count': len(questions_data)
                }
            )
            
            # Return active session data
            response_serializer = UnitTestSessionActiveMobileSerializer(session)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            log_user_activity(
                request.user,
                'unit_test_start_error',
                {'error': str(e)}
            )
            return Response({
                'success': False,
                'error': 'Failed to start test session'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit answers for a test session.
        """
        session = self.get_object()
        
        # Check if already completed
        if session.completed_at:
            return Response({
                'error': 'Test already completed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UnitTestSessionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        answers_data = serializer.validated_data['answers']
        time_taken = serializer.validated_data.get('time_taken_seconds')
        
        with transaction.atomic():
            # Process each answer
            correct_count = 0
            domain_scores = {}
            
            for answer_data in answers_data:
                question_id = answer_data['question_id']
                student_answer = answer_data['student_answer']
                time_taken_q = answer_data.get('time_taken_seconds')
                
                try:
                    question = session.questions.get(id=question_id)
                    
                    # Check if correct (simple string comparison - enhance as needed)
                    is_correct = (student_answer.strip().lower() == 
                                 question.correct_answer.strip().lower())
                    
                    if is_correct:
                        correct_count += 1
                    
                    # Track domain scores
                    domain = question.domain
                    if domain not in domain_scores:
                        domain_scores[domain] = {'correct': 0, 'total': 0}
                    domain_scores[domain]['total'] += 1
                    if is_correct:
                        domain_scores[domain]['correct'] += 1
                    
                    # Create answer record
                    UnitTestAnswer.objects.create(
                        question=question,
                        student_answer=student_answer,
                        is_correct=is_correct,
                        time_taken_seconds=time_taken_q
                    )
                    
                except UnitTestQuestion.DoesNotExist:
                    continue
            
            # Update session
            session.completed_at = timezone.now()
            session.time_taken_seconds = time_taken
            session.correct_answers = correct_count
            session.total_questions = session.questions.count()
            
            # Calculate domain percentages
            domain_percentages = {}
            for domain, scores in domain_scores.items():
                if scores['total'] > 0:
                    domain_percentages[domain] = (scores['correct'] / scores['total']) * 100
            session.domain_scores = domain_percentages
            
            session.save()
            
            # Create domain-specific attempt records (for backward compatibility)
            if 'vocabulary' in domain_scores:
                self._create_vocabulary_attempt(session)
        
        log_user_activity(
            request.user,
            'unit_test_completed',
            {
                'session_id': session.id,
                'score': session.score_percentage,
                'passed': session.passed,
                'time_taken': time_taken
            }
        )
        
        return Response({
            'success': True,
            'session_id': session.id,
            'score': session.score_percentage,
            'passed': session.passed,
            'correct_answers': session.correct_answers,
            'total_questions': session.total_questions,
            'domain_scores': session.domain_scores
        })
    
    def _create_vocabulary_attempt(self, session):
        """
        Create vocabulary-specific attempt record for backward compatibility.
        """
        vocab_questions = session.questions.filter(domain='vocabulary')
        if not vocab_questions.exists():
            return
        
        correct = 0
        total = vocab_questions.count()
        
        for question in vocab_questions:
            try:
                answer = question.answers.get()
                if answer.is_correct:
                    correct += 1
            except UnitTestAnswer.DoesNotExist:
                continue
        
        score_percent = int((correct / total) * 100) if total > 0 else 0
        
        VocabularyUnitTestAttempt.objects.create(
            user=session.user,
            unit_test_session=session,
            lesson=None,  # Can be derived from questions
            chunk=None,
            score_percent=score_percent,
            correct_answers=correct,
            total_questions=total,
            questions_data={
                'questions': [
                    {
                        'id': q.id,
                        'text': q.question_text,
                        'vocab_item_id': q.vocabulary_item_id
                    }
                    for q in vocab_questions
                ]
            }
        )
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Get detailed results for a completed test.
        """
        session = self.get_object()
        
        if not session.completed_at:
            return Response({
                'error': 'Test not yet completed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all questions with answers
        questions = session.questions.prefetch_related('answers').all()
        
        results = {
            'session_id': session.id,
            'unit_id': session.unit_id,
            'unit_title': session.unit.title,
            'attempt_number': session.attempt_number,
            'started_at': session.started_at,
            'completed_at': session.completed_at,
            'time_taken_minutes': (session.time_taken_seconds / 60) if session.time_taken_seconds else None,
            'overall_score': session.score_percentage,
            'passed': session.passed,
            'correct_answers': session.correct_answers,
            'total_questions': session.total_questions,
            'domain_scores': session.domain_scores,
            'questions': []
        }
        
        for question in questions:
            answer = question.answers.first()
            results['questions'].append({
                'id': question.id,
                'order': question.order,
                'domain': question.domain,
                'question_text': question.question_text,
                'student_answer': answer.student_answer if answer else None,
                'correct_answer': question.correct_answer,
                'is_correct': answer.is_correct if answer else False,
                'time_taken': answer.time_taken_seconds if answer else None,
                'points': question.points
            })
        
        return Response(results)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get current active test session for a unit.
        """
        unit_id = request.query_params.get('unit_id')
        if not unit_id:
            return Response(
                {'error': 'unit_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session = UnitTestSession.objects.filter(
            user=request.user,
            unit_id=unit_id,
            completed_at__isnull=True
        ).first()
        
        if not session:
            return Response(
                {'error': 'No active test session found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UnitTestSessionActiveMobileSerializer(session)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get test history for all units.
        """
        user = request.user
        sessions = self.get_queryset()
        
        # Group by unit
        units = Unit.objects.all().order_by('number')
        history = []
        
        for unit in units:
            unit_sessions = sessions.filter(unit=unit)
            if unit_sessions.exists():
                best = unit_sessions.order_by('-score_percentage').first()
                latest = unit_sessions.order_by('-started_at').first()
                
                history.append({
                    'unit_id': unit.id,
                    'unit_title': unit.title,
                    'unit_number': unit.number,
                    'attempts': unit_sessions.count(),
                    'best_score': best.score_percentage,
                    'latest_score': latest.score_percentage,
                    'passed': any(s.passed for s in unit_sessions),
                    'last_attempted': latest.started_at
                })
            else:
                history.append({
                    'unit_id': unit.id,
                    'unit_title': unit.title,
                    'unit_number': unit.number,
                    'attempts': 0,
                    'best_score': None,
                    'latest_score': None,
                    'passed': False,
                    'last_attempted': None
                })
        
        return Response(history)


# ============================================================
# TEST QUESTION VIEWS
# ============================================================

class UnitTestQuestionViewSet(BaseViewSet):
    """
    ViewSet for unit test questions.
    Mostly read-only for analytics.
    """
    
    queryset = UnitTestQuestion.objects.all()
    serializer_class = UnitTestQuestionSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and request.
        """
        if self.action == 'list':
            if self.request.GET.get('mobile') == 'true':
                return UnitTestQuestionMobileSerializer
            return UnitTestQuestionListSerializer
        
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter by session or domain.
        """
        queryset = super().get_queryset()
        
        # Filter by session
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        # Filter by domain
        domain = self.request.query_params.get('domain')
        if domain:
            queryset = queryset.filter(domain=domain)
        
        return queryset.order_by('order')
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """
        Get analytics for a specific question.
        """
        question = self.get_object()
        
        # Get all answers for this question
        answers = question.answers.all()
        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        
        analytics = {
            'question_id': question.id,
            'domain': question.domain,
            'question_type': question.question_type,
            'difficulty': question.difficulty,
            'total_attempts': total,
            'correct_attempts': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0,
            'average_time': answers.aggregate(avg=Avg('time_taken_seconds'))['avg'],
            'by_session': []
        }
        
        # Group by session
        sessions = answers.values_list('question__session', flat=True).distinct()
        for session_id in sessions[:10]:  # Limit to 10 sessions
            session_answers = answers.filter(question__session_id=session_id)
            session_correct = session_answers.filter(is_correct=True).count()
            analytics['by_session'].append({
                'session_id': session_id,
                'attempts': session_answers.count(),
                'correct': session_correct,
                'accuracy': (session_correct / session_answers.count() * 100)
            })
        
        return Response(analytics)


# ============================================================
# TEST ANSWER VIEWS
# ============================================================

class UnitTestAnswerViewSet(BaseViewSet, UserFilterMixin):
    """
    ViewSet for test answers.
    Read-only for analytics.
    """
    
    queryset = UnitTestAnswer.objects.all()
    serializer_class = UnitTestAnswerSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on request.
        """
        if self.request.GET.get('mobile') == 'true':
            return UnitTestAnswerMobileSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Filter by question or session.
        """
        queryset = super().get_queryset()
        
        # Filter by question
        question_id = self.request.query_params.get('question_id')
        if question_id:
            queryset = queryset.filter(question_id=question_id)
        
        # Filter by session (via question)
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(question__session_id=session_id)
        
        return queryset.select_related('question')


# ============================================================
# PROGRESS VIEWS
# ============================================================

class UnitTestProgressViewSet(ProgressViewSet):
    """
    ViewSet for unit test progress tracking.
    """
    
    serializer_class = UnitTestHistorySerializer
    
    def get_user_progress(self, user):
        """
        Get unit test progress for user.
        """
        sessions = UnitTestSession.objects.filter(user=user)
        
        # Overall stats
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(completed_at__isnull=False).count()
        passed_sessions = sessions.filter(passed=True).count()
        
        # Unit stats
        units = Unit.objects.all().order_by('number')
        unit_progress = []
        
        for unit in units:
            unit_sessions = sessions.filter(unit=unit)
            if unit_sessions.exists():
                best = unit_sessions.order_by('-score_percentage').first()
                latest = unit_sessions.order_by('-started_at').first()
                
                unit_progress.append({
                    'unit_id': unit.id,
                    'unit_title': unit.title,
                    'unit_number': unit.number,
                    'attempts': unit_sessions.count(),
                    'best_score': best.score_percentage,
                    'latest_score': latest.score_percentage,
                    'passed': any(s.passed for s in unit_sessions),
                    'last_attempted': latest.started_at
                })
        
        # Domain performance
        domain_performance = {}
        for session in sessions.filter(completed_at__isnull=False):
            if session.domain_scores:
                for domain, score in session.domain_scores.items():
                    if domain not in domain_performance:
                        domain_performance[domain] = []
                    domain_performance[domain].append(score)
        
        avg_domain_scores = {}
        for domain, scores in domain_performance.items():
            avg_domain_scores[domain] = sum(scores) / len(scores)
        
        progress_data = {
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'passed_sessions': passed_sessions,
            'pass_rate': (passed_sessions / completed_sessions * 100) if completed_sessions > 0 else 0,
            'average_score': sessions.filter(completed_at__isnull=False).aggregate(avg=Avg('score_percentage'))['avg'],
            'best_score': sessions.filter(completed_at__isnull=False).aggregate(best=Max('score_percentage'))['best'],
            'unit_progress': unit_progress,
            'domain_performance': avg_domain_scores,
            'last_activity': sessions.order_by('-started_at').first().started_at if sessions.exists() else None
        }
        
        return progress_data
    
    @action(detail=False, methods=['get'])
    def unit_summary(self, request):
        """
        Get test summary for a specific unit.
        """
        user = request.user
        unit_id = request.query_params.get('unit_id')
        
        if not unit_id:
            return Response(
                {'error': 'unit_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sessions = UnitTestSession.objects.filter(
            user=user,
            unit_id=unit_id
        ).order_by('-attempt_number')
        
        if not sessions.exists():
            return Response({
                'unit_id': unit_id,
                'attempts': 0,
                'message': 'No test attempts for this unit'
            })
        
        summary = {
            'unit_id': unit_id,
            'unit_title': sessions.first().unit.title,
            'attempts': sessions.count(),
            'attempts_remaining': self.max_attempts_per_unit - sessions.count(),
            'best_score': sessions.aggregate(best=Max('score_percentage'))['best'],
            'latest_score': sessions.first().score_percentage,
            'passed': any(s.passed for s in sessions),
            'attempts_list': UnitTestSessionListSerializer(sessions, many=True).data
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def domain_breakdown(self, request):
        """
        Get performance breakdown by domain across all tests.
        """
        user = request.user
        sessions = UnitTestSession.objects.filter(
            user=user,
            completed_at__isnull=False
        )
        
        if not sessions.exists():
            return Response({})
        
        # Aggregate domain scores
        domain_aggregates = {}
        domain_counts = {}
        
        for session in sessions:
            if session.domain_scores:
                for domain, score in session.domain_scores.items():
                    if domain not in domain_aggregates:
                        domain_aggregates[domain] = 0
                        domain_counts[domain] = 0
                    domain_aggregates[domain] += score
                    domain_counts[domain] += 1
        
        # Calculate averages
        domain_averages = {
            domain: domain_aggregates[domain] / domain_counts[domain]
            for domain in domain_aggregates
        }
        
        return Response(domain_averages)


# ============================================================
# TEST GENERATION VIEWS
# ============================================================

class TestGenerationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for test generation and configuration.
    Admin endpoints for managing test content.
    """
    
    permission_classes = [IsAuthenticated]  # Add admin check
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a custom test based on configuration.
        """
        serializer = TestGenerationConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        unit_id = serializer.validated_data['unit_id']
        unit = get_object_or_404(Unit, id=unit_id)
        
        # Get configuration
        questions_per_domain = serializer.validated_data.get(
            'questions_per_domain',
            {'vocabulary': 5, 'grammar': 5, 'punctuation': 3, 'comprehension': 4}
        )
        
        include_domains = serializer.validated_data.get(
            'include_domains',
            ['vocabulary', 'grammar', 'punctuation', 'comprehension']
        )
        
        # Generate questions based on config
        questions = []
        chunks = LessonChunk.objects.filter(lesson__unit=unit)
        
        if 'vocabulary' in include_domains:
            vocab_items = VocabularyItem.objects.filter(chunk__in=chunks)
            count = min(questions_per_domain.get('vocabulary', 5), vocab_items.count())
            selected = random.sample(list(vocab_items), count) if count > 0 else []
            for item in selected:
                questions.append({
                    'domain': 'vocabulary',
                    'question_type': 'mcq',
                    'question_text': f"Select the correct meaning of '{item.word}'",
                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                    'correct_answer': item.meaning,
                    'difficulty': 3,
                    'vocabulary_item_id': item.id
                })
        
        # Similar blocks for other domains...
        
        return Response({
            'unit_id': unit_id,
            'total_questions': len(questions),
            'questions': questions
        })


# ============================================================
# LEGACY MIGRATION VIEWS
# ============================================================

class LegacyMigrationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for migrating legacy test data.
    Temporary endpoints for data migration.
    """
    
    permission_classes = [IsAuthenticated]  # Add admin check
    
    @action(detail=False, methods=['post'])
    def migrate_vocabulary_tests(self, request):
        """
        Migrate legacy vocabulary tests to new unit test format.
        """
        from content.models.testing import VocabularyTestSession
        
        legacy_sessions = VocabularyTestSession.objects.all()
        migrated_count = 0
        
        with transaction.atomic():
            for legacy in legacy_sessions:
                # Find corresponding unit
                # This logic would need to be customized based on your data
                unit = Unit.objects.first()  # Placeholder
                
                # Create new session
                session = UnitTestSession.objects.create(
                    user_id=legacy.student_id,  # This would need proper user mapping
                    unit=unit,
                    attempt_number=1,
                    started_at=legacy.started_at,
                    completed_at=legacy.completed_at,
                    total_questions=legacy.total_questions,
                    correct_answers=legacy.correct_answers,
                    score_percentage=legacy.score_percentage,
                    passed=legacy.passed,
                    test_data={'migrated_from': 'legacy_vocabulary'}
                )
                
                migrated_count += 1
        
        return Response({
            'success': True,
            'message': f'Migrated {migrated_count} legacy test sessions'
        })