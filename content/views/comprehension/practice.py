# content/views/comprehension/practice.py

from django.db import transaction, IntegrityError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionQuestion,
    ComprehensionPracticeAttempt,
    ComprehensionQuestionAttempt,
)
from content.serializers.comprehension import ComprehensionPracticeAttemptSerializer
from content.services.comprehension.comprehension_mastery import is_focus_mastered


class ComprehensionPracticeView(generics.CreateAPIView):
    """
    Record a practice attempt for comprehension questions,
    enforcing LMS progression, chunk integrity, and student ownership.
    
    Practice requires 100% correct to pass, with 3 attempts per cycle.
    Tracks individual question attempts for detailed analytics.
    """

    serializer_class = ComprehensionPracticeAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        """Add request to serializer context for user access."""
        context = super().get_serializer_context()
        context.update({
            'chunk_id': self.kwargs.get('chunk_id'),
            'focus_id': self.kwargs.get('focus_id'),
        })
        return context

    def get_current_cycle(self, user, focus):
        """Get current practice cycle number."""
        latest_attempt = ComprehensionPracticeAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-cycle_number', '-attempt_number').first()
        
        if latest_attempt:
            return latest_attempt.cycle_number
        return 1

    def get_current_attempt_number(self, user, focus, cycle_number):
        """Get next attempt number for current cycle."""
        attempts_in_cycle = ComprehensionPracticeAttempt.objects.filter(
            user=user,
            focus=focus,
            cycle_number=cycle_number
        ).count()
        
        return attempts_in_cycle + 1

    def validate_attempt_limits(self, user, focus):
        """
        Validate user hasn't exceeded attempt limits.
        Returns (cycle_number, attempt_number) if valid.
        Raises ValidationError if limit exceeded.
        """
        current_cycle = self.get_current_cycle(user, focus)
        attempt_number = self.get_current_attempt_number(user, focus, current_cycle)
        
        if attempt_number > 3:
            # Check if any attempts in next cycle
            next_cycle_attempts = ComprehensionPracticeAttempt.objects.filter(
                user=user,
                focus=focus,
                cycle_number=current_cycle + 1
            ).exists()
            
            if not next_cycle_attempts:
                # Auto-start new cycle
                return current_cycle + 1, 1
            else:
                raise ValidationError(
                    f"Maximum attempts (3) reached for cycle {current_cycle}. "
                    f"Please start a new practice cycle."
                )
        
        return current_cycle, attempt_number

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Wrapped in atomic transaction for LMS consistency.
        Expects list of question attempts in request data.
        """
        chunk_id = self.kwargs.get("chunk_id")
        focus_id = self.kwargs.get("focus_id")
        
        # Validate focus exists and belongs to chunk
        try:
            focus = ChunkComprehensionFocus.objects.select_related(
                'chunk'
            ).prefetch_related(
                'questions'
            ).get(
                id=focus_id,
                chunk_id=chunk_id
            )
        except ChunkComprehensionFocus.DoesNotExist:
            raise ValidationError("Focus not found in this chunk.")
        
        student = request.user
        
        # --------------------------------------------------
        # 1️⃣ Sequential mastery enforcement
        # --------------------------------------------------
        previous_focus = (
            ChunkComprehensionFocus.objects
            .filter(chunk=focus.chunk, sequence_order__lt=focus.sequence_order)
            .order_by("-sequence_order")
            .first()
        )

        if previous_focus and not is_focus_mastered(student, previous_focus):
            raise PermissionDenied(
                f"You must master {previous_focus.focus_title} "
                f"({previous_focus.get_level_display()}) first."
            )

        # --------------------------------------------------
        # 2️⃣ Validate attempt limits
        # --------------------------------------------------
        cycle_number, attempt_number = self.validate_attempt_limits(student, focus)
        
        # --------------------------------------------------
        # 3️⃣ Validate and process question attempts
        # --------------------------------------------------
        question_data = request.data.get('questions', [])
        
        if not question_data:
            raise ValidationError("No question attempts provided.")
        
        # Get all questions for this focus
        questions = {
            q.id: q for q in ComprehensionQuestion.objects.filter(
                focus=focus
            ).select_related('focus')
        }
        
        # Validate all questions belong to this focus
        for item in question_data:
            question_id = item.get('question_id')
            if question_id not in questions:
                raise ValidationError(
                    f"Question {question_id} does not belong to this focus."
                )
        
        # Process answers and calculate score
        correct_count = 0
        question_attempts = []
        
        for item in question_data:
            question_id = item.get('question_id')
            selected_answer = item.get('selected_answer', '').strip()
            open_ended_answer = item.get('open_ended_answer', '').strip()
            
            question = questions[question_id]
            
            # Determine correctness based on question type
            is_correct = False
            
            if question.question_type == ComprehensionQuestion.TYPE_MCQ:
                # MCQ: exact match with correct answer (case-insensitive)
                if selected_answer:
                    options_lower = [opt.lower() for opt in question.get_options_list()]
                    is_correct = (
                        selected_answer.lower() in options_lower and
                        selected_answer.lower() == question.correct_answer.strip().lower()
                    )
            
            elif question.question_type == ComprehensionQuestion.TYPE_TRUE_FALSE:
                # True/False: match boolean representation
                if selected_answer:
                    selected_lower = selected_answer.lower()
                    correct_lower = question.correct_answer.strip().lower()
                    is_correct = selected_lower == correct_lower
            
            elif question.question_type == ComprehensionQuestion.TYPE_SHORT_ANSWER:
                # Short answer: case-insensitive trim comparison
                if selected_answer:
                    is_correct = (
                        selected_answer.lower().strip()
                        == question.correct_answer.strip().lower()
                    )
            
            elif question.question_type == ComprehensionQuestion.TYPE_OPEN_ENDED:
                # Open-ended: no automatic correctness, mark as needs review
                is_correct = False  # Will be reviewed by teacher
            
            if is_correct:
                correct_count += 1
            
            # Store question attempt (will be linked after practice attempt created)
            question_attempts.append({
                'question': question,
                'selected_answer': selected_answer,
                'open_ended_answer': open_ended_answer,
                'is_correct': is_correct,
                'cycle_number': cycle_number,
                'attempt_number': attempt_number,
            })
        
        # Calculate score percentage
        total_questions = len(questions)
        score_percent = int((correct_count / total_questions) * 100) if total_questions else 0
        is_passed = (score_percent == 100)  # Must be perfect to pass
        
        # --------------------------------------------------
        # 4️⃣ Create practice attempt record
        # --------------------------------------------------
        practice_attempt = ComprehensionPracticeAttempt.objects.create(
            user=student,
            focus=focus,
            attempt_number=attempt_number,
            cycle_number=cycle_number,
            score_percent=score_percent,
            is_passed=is_passed,
            correct_answers=correct_count,
            total_questions=total_questions,
            questions_data={
                'questions': [
                    {
                        'id': q['question'].id,
                        'text': q['question'].question_text,
                        'type': q['question'].question_type,
                        'correct': q['question'].correct_answer,
                        'options': q['question'].get_options_list(),
                        'user_answer': q['selected_answer'] or q['open_ended_answer'],
                        'is_correct': q['is_correct']
                    }
                    for q in question_attempts
                ],
                'cycle_number': cycle_number,
                'attempt_number': attempt_number,
                'focus_title': focus.focus_title,
                'level': focus.level,
            }
        )
        
        # --------------------------------------------------
        # 5️⃣ Create individual question attempts
        # --------------------------------------------------
        question_attempt_objects = []
        for qa in question_attempts:
            question_attempt_objects.append(
                ComprehensionQuestionAttempt(
                    user=student,
                    question=qa['question'],
                    practice_attempt=practice_attempt,
                    selected_answer=qa['selected_answer'],
                    open_ended_answer=qa['open_ended_answer'],
                    is_correct=qa['is_correct'],
                    cycle_number=qa['cycle_number'],
                    attempt_number=qa['attempt_number'],
                )
            )
        
        if question_attempt_objects:
            ComprehensionQuestionAttempt.objects.bulk_create(question_attempt_objects)
        
        # --------------------------------------------------
        # 6️⃣ Prepare response
        # --------------------------------------------------
        response_data = {
            'practice_attempt_id': practice_attempt.id,
            'focus_id': focus.id,
            'focus_title': focus.focus_title,
            'level': focus.level,
            'attempt_number': attempt_number,
            'cycle_number': cycle_number,
            'score_percent': score_percent,
            'is_passed': is_passed,
            'correct_answers': correct_count,
            'total_questions': total_questions,
            'attempts_remaining_in_cycle': 3 - attempt_number,
            'next_allowed_cycle': cycle_number + (1 if attempt_number >= 3 else 0),
            'question_results': [
                {
                    'question_id': qa['question'].id,
                    'is_correct': qa['is_correct'],
                    'correct_answer': qa['question'].correct_answer,
                    'explanation': qa['question'].explanation,
                }
                for qa in question_attempts
            ]
        }
        
        # Add mastery status if passed
        if is_passed:
            response_data['mastery_achieved'] = True
            response_data['next_focus_available'] = (
                ChunkComprehensionFocus.objects.filter(
                    chunk=focus.chunk,
                    sequence_order=focus.sequence_order + 1
                ).exists()
            )
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class ComprehensionPracticeHistoryView(generics.ListAPIView):
    """
    Retrieve practice history for a comprehension focus.
    """
    serializer_class = ComprehensionPracticeAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chunk_id = self.kwargs.get("chunk_id")
        focus_id = self.kwargs.get("focus_id")
        
        return ComprehensionPracticeAttempt.objects.filter(
            user=self.request.user,
            focus_id=focus_id,
            focus__chunk_id=chunk_id
        ).select_related(
            'focus'
        ).prefetch_related(
            'question_attempts'
        ).order_by('-cycle_number', '-attempt_number')