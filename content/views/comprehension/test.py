# views/comprehension/test.py

from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

from content.models.comprehension import (
    ComprehensionQuestion,
    ComprehensionTestAttempt,
    ComprehensionQuestionAttempt,
    ChunkComprehensionFocus,
)
from content.serializers.comprehension import (
    ComprehensionQuestionAttemptSerializer,
    ComprehensionTestAttemptSerializer,
)
from content.services.comprehension.comprehension_mastery import is_focus_mastered


# ============================================================
# TEST SUBMISSION VIEW (Browser-based)
# ============================================================

class ComprehensionTestSubmitView(APIView):
    """
    Browser-safe mastery submission endpoint.
    
    Features:
    - 3 attempts max per cycle
    - 100% required to pass
    - Automatic cycle management
    - Atomic persistence
    - Redirect-after-POST to result page
    """

    permission_classes = [IsAuthenticated]

    def get_current_cycle(self, user, focus):
        """Get current test cycle number."""
        latest_attempt = ComprehensionTestAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-cycle_number', '-attempt_number').first()
        
        if latest_attempt:
            return latest_attempt.cycle_number
        return 1

    def get_current_attempt_number(self, user, focus, cycle_number):
        """Get next attempt number for current cycle."""
        attempts_in_cycle = ComprehensionTestAttempt.objects.filter(
            user=user,
            focus=focus,
            cycle_number=cycle_number
        ).count()
        
        return attempts_in_cycle + 1

    def validate_attempt_limits(self, user, focus):
        """
        Validate user hasn't exceeded test attempt limits.
        Returns (cycle_number, attempt_number) if valid.
        Raises PermissionDenied if limit exceeded.
        """
        current_cycle = self.get_current_cycle(user, focus)
        attempt_number = self.get_current_attempt_number(user, focus, current_cycle)
        
        if attempt_number > 3:
            # Check if user has mastered in a previous cycle
            has_mastered = ComprehensionTestAttempt.objects.filter(
                user=user,
                focus=focus,
                is_mastered=True
            ).exists()
            
            if has_mastered:
                raise PermissionDenied("You have already mastered this focus.")
            
            # Auto-start new cycle
            return current_cycle + 1, 1
        
        return current_cycle, attempt_number

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        focus_id = kwargs.get("focus_id")
        chunk_id = kwargs.get("chunk_id")
        
        focus = get_object_or_404(
            ChunkComprehensionFocus, 
            id=focus_id,
            chunk_id=chunk_id
        )
        student = request.user

        # --------------------------------------------------
        # 1️⃣ LMS progression lock
        # --------------------------------------------------
        previous_focus = (
            ChunkComprehensionFocus.objects
            .filter(chunk=focus.chunk, sequence_order__lt=focus.sequence_order)
            .order_by("-sequence_order")
            .first()
        )

        if previous_focus and not is_focus_mastered(student, previous_focus):
            messages.error(
                request,
                f"You must master {previous_focus.focus_title} "
                f"({previous_focus.get_level_display()}) first."
            )
            return redirect(
                "content:comprehension:focus",
                chunk_id=chunk_id,
                focus_id=previous_focus.id
            )

        # --------------------------------------------------
        # 2️⃣ Validate attempt limits
        # --------------------------------------------------
        try:
            cycle_number, attempt_number = self.validate_attempt_limits(student, focus)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect(
                "content:comprehension:focus",
                chunk_id=chunk_id,
                focus_id=focus_id
            )

        # --------------------------------------------------
        # 3️⃣ Collect POST answers from form
        # --------------------------------------------------
        questions = list(ComprehensionQuestion.objects.filter(
            focus=focus
        ).order_by('id'))

        if not questions:
            messages.error(request, "No questions configured for this focus.")
            return redirect(
                "content:comprehension:teach",
                chunk_id=chunk_id,
                focus_id=focus_id
            )

        # Validate all questions are answered
        answers = {}
        missing_answers = []
        
        for q in questions:
            answer = request.POST.get(f"q{q.id}", "").strip()
            if not answer:
                missing_answers.append(str(q.id))
            answers[str(q.id)] = answer

        if missing_answers:
            messages.error(
                request, 
                f"Questions {', '.join(missing_answers)} must be answered."
            )
            return redirect(
                "content:comprehension:test",
                chunk_id=chunk_id,
                focus_id=focus_id
            )

        # --------------------------------------------------
        # 4️⃣ Score answers
        # --------------------------------------------------
        total_questions = len(questions)
        correct_count = 0
        question_attempts = []
        now = timezone.now()

        for q in questions:
            selected = answers[str(q.id)]

            # Determine correctness based on question type
            is_correct = False
            
            if q.question_type == ComprehensionQuestion.TYPE_MCQ:
                # MCQ: exact match with correct answer (case-insensitive)
                options_lower = [opt.lower() for opt in q.get_options_list()]
                is_correct = (
                    selected.lower() in options_lower and
                    selected.lower() == q.correct_answer.strip().lower()
                )
            
            elif q.question_type == ComprehensionQuestion.TYPE_TRUE_FALSE:
                # True/False: match boolean representation
                selected_lower = selected.lower()
                correct_lower = q.correct_answer.strip().lower()
                is_correct = selected_lower == correct_lower
            
            elif q.question_type == ComprehensionQuestion.TYPE_SHORT_ANSWER:
                # Short answer: case-insensitive trim comparison
                is_correct = (
                    selected.lower().strip()
                    == q.correct_answer.strip().lower()
                )
            
            elif q.question_type == ComprehensionQuestion.TYPE_OPEN_ENDED:
                # Open-ended: mark for teacher review (count as incorrect for now)
                is_correct = False  # Will be reviewed by teacher

            if is_correct:
                correct_count += 1

            # Prepare question attempt (will be created after test attempt)
            question_attempts.append({
                'question': q,
                'selected_answer': selected,
                'is_correct': is_correct,
            })

        # --------------------------------------------------
        # 5️⃣ Calculate score and mastery
        # --------------------------------------------------
        score_percent = int(round((correct_count / total_questions) * 100))
        is_mastered = (score_percent == 100)

        # --------------------------------------------------
        # 6️⃣ Create test attempt
        # --------------------------------------------------
        test_attempt = ComprehensionTestAttempt.objects.create(
            user=student,
            focus=focus,
            attempt_number=attempt_number,
            cycle_number=cycle_number,
            score_percent=score_percent,
            is_mastered=is_mastered,
            correct_answers=correct_count,
            total_questions=total_questions,
            questions_data={
                'questions': [
                    {
                        'id': qa['question'].id,
                        'text': qa['question'].question_text,
                        'type': qa['question'].question_type,
                        'correct': qa['question'].correct_answer,
                        'options': qa['question'].get_options_list(),
                        'user_answer': qa['selected_answer'],
                        'is_correct': qa['is_correct']
                    }
                    for qa in question_attempts
                ],
                'cycle_number': cycle_number,
                'attempt_number': attempt_number,
                'focus_title': focus.focus_title,
                'level': focus.level,
            }
        )

        # --------------------------------------------------
        # 7️⃣ Create individual question attempts
        # --------------------------------------------------
        question_attempt_objects = []
        for qa in question_attempts:
            question_attempt_objects.append(
                ComprehensionQuestionAttempt(
                    user=student,
                    question=qa['question'],
                    test_attempt=test_attempt,
                    selected_answer=qa['selected_answer'],
                    is_correct=qa['is_correct'],
                    cycle_number=cycle_number,
                    attempt_number=attempt_number,
                )
            )

        if question_attempt_objects:
            ComprehensionQuestionAttempt.objects.bulk_create(question_attempt_objects)

        # --------------------------------------------------
        # 8️⃣ Add success message based on result
        # --------------------------------------------------
        if is_mastered:
            messages.success(
                request,
                f"🎉 Congratulations! You've mastered {focus.focus_title} "
                f"with a perfect score! (Attempt {attempt_number}/3, Cycle {cycle_number})"
            )
            
            # Check if this unlocks the next focus
            next_focus = ChunkComprehensionFocus.objects.filter(
                chunk=focus.chunk,
                sequence_order=focus.sequence_order + 1
            ).first()
            
            if next_focus:
                messages.info(
                    request,
                    f"You've unlocked: {next_focus.focus_title} "
                    f"({next_focus.get_level_display()})"
                )
        else:
            if attempt_number >= 3:
                messages.warning(
                    request,
                    f"You scored {score_percent}% ({correct_count}/{total_questions}). "
                    f"You've used all 3 attempts in cycle {cycle_number}. "
                    f"A new practice cycle has been started."
                )
            else:
                messages.warning(
                    request,
                    f"You scored {score_percent}% ({correct_count}/{total_questions}). "
                    f"Need 100% to master. Attempts remaining this cycle: {3 - attempt_number}"
                )

        # --------------------------------------------------
        # 9️⃣ REDIRECT → result page
        # --------------------------------------------------
        return redirect(
            "content:comprehension:test-result",
            chunk_id=chunk_id,
            focus_id=focus.id,
            attempt_id=test_attempt.id
        )


# ============================================================
# TEST RESULTS VIEW (Single attempt details)
# ============================================================

class ComprehensionTestResultDetailView(generics.RetrieveAPIView):
    serializer_class = ComprehensionTestAttemptSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        chunk_id = self.kwargs.get("chunk_id")
        focus_id = self.kwargs.get("focus_id")
        return ComprehensionTestAttempt.objects.filter(
            user=self.request.user,
            focus_id=focus_id,
            focus__chunk_id=chunk_id
        ).select_related('focus').prefetch_related(
            'question_attempts__question'
        )


# ============================================================
# TEST HISTORY VIEW (All attempts for a focus)
# ============================================================

class ComprehensionTestHistoryView(generics.ListAPIView):
    """
    Returns all test attempts for a specific focus.
    """
    serializer_class = ComprehensionTestAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chunk_id = self.kwargs.get("chunk_id")
        focus_id = self.kwargs.get("focus_id")
        
        return ComprehensionTestAttempt.objects.filter(
            user=self.request.user,
            focus_id=focus_id,
            focus__chunk_id=chunk_id
        ).select_related(
            'focus'
        ).prefetch_related(
            'question_attempts__question'
        ).order_by('-cycle_number', '-attempt_number')


# ============================================================
# LEGACY SUPPORT (if needed)
# ============================================================

# Keep the old class names for backward compatibility if needed
ComprehensionTestResultsView = ComprehensionTestHistoryView