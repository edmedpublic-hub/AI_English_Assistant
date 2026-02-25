# content/views/grammar/practice.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.db import transaction

from content.models.grammar import (
    GrammarQuestion,
    GrammarPracticeAttempt,
    GrammarQuestionAttempt,
    ChunkGrammarFocus,
)
from content.models.core import LessonChunk


class GrammarPracticeView(LoginRequiredMixin, TemplateView):
    """
    Grammar Practice View
    - Chunk + focus scoped
    - Tracks individual question attempts
    - Test unlocked if all answers correct (100%)
    - 3 attempts max per cycle
    """
    template_name = "content/grammar/practice.html"

    def get_chunk_and_focus(self):
        """Resolve chunk and focus objects from URL params."""
        chunk_id = self.kwargs.get('chunk_id')
        focus_id = self.kwargs.get('focus_id')
        
        chunk = get_object_or_404(LessonChunk, id=chunk_id)
        focus = get_object_or_404(
            ChunkGrammarFocus, 
            id=focus_id,
            chunk=chunk
        )
        
        return chunk, focus

    def get_questions(self, focus):
        """Fetch questions for this focus."""
        return GrammarQuestion.objects.filter(
            focus=focus
        ).order_by("id")

    def get_current_cycle(self, user, focus):
        """Get current practice cycle number."""
        latest_attempt = GrammarPracticeAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-cycle_number', '-attempt_number').first()
        
        if latest_attempt:
            return latest_attempt.cycle_number
        return 1

    def get_current_attempt_number(self, user, focus, cycle_number):
        """Get next attempt number for current cycle."""
        attempts_in_cycle = GrammarPracticeAttempt.objects.filter(
            user=user,
            focus=focus,
            cycle_number=cycle_number
        ).count()
        
        return attempts_in_cycle + 1

    def get_practice_history(self, user, focus):
        """Get user's practice history for this focus."""
        return GrammarPracticeAttempt.objects.filter(
            user=user,
            focus=focus
        ).order_by('-cycle_number', '-attempt_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        chunk, focus = self.get_chunk_and_focus()
        questions = self.get_questions(focus)
        practice_history = self.get_practice_history(self.request.user, focus)
        current_cycle = self.get_current_cycle(self.request.user, focus)
        
        # Prepare questions for template
        for q in questions:
            q.user_answer = None
            q.is_correct = None
            q.feedback_ready = False
        
        context.update({
            "chunk": chunk,
            "focus": focus,
            "concept": focus.concept,
            "questions": questions,
            "practice_history": practice_history,
            "current_cycle": current_cycle,
            "attempts_remaining": 3 - practice_history.filter(
                cycle_number=current_cycle
            ).count(),
            "submitted": False,
        })
        
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        chunk, focus = self.get_chunk_and_focus()
        questions = self.get_questions(focus)
        
        # Get current cycle info
        current_cycle = self.get_current_cycle(request.user, focus)
        attempt_number = self.get_current_attempt_number(
            request.user, focus, current_cycle
        )
        
        # Check if max attempts reached
        if attempt_number > 3:
            messages.warning(
                request,
                f"You've used all 3 attempts in cycle {current_cycle}. "
                f"Please start a new practice cycle."
            )
            return redirect(
                "content:grammar:practice",
                chunk_id=chunk.id,
                focus_id=focus.id
            )
        
        # Process answers
        any_answered = False
        correct_count = 0
        question_attempts = []
        
        for q in questions:
            user_answer = request.POST.get(f"q{q.id}", "").strip()
            if not user_answer:
                continue
            
            any_answered = True
            
            # For MCQ, ensure exact match (case-insensitive)
            if q.question_type == GrammarQuestion.TYPE_MCQ:
                options_lower = [opt.lower() for opt in q.get_options_list()]
                is_correct = user_answer.lower() in options_lower and \
                           user_answer.lower() == q.correct_answer.strip().lower()
            else:
                # For fill-in/rewrite, case-insensitive trim comparison
                is_correct = (
                    user_answer.lower().strip()
                    == q.correct_answer.strip().lower()
                )
            
            if is_correct:
                correct_count += 1
            
            # Store for bulk create
            question_attempts.append(
                GrammarQuestionAttempt(
                    user=request.user,
                    question=q,
                    selected_answer=user_answer,
                    is_correct=is_correct,
                )
            )
            
            # For template feedback
            q.user_answer = user_answer
            q.is_correct = is_correct
            q.feedback_ready = True
        
        if not any_answered:
            messages.warning(
                request,
                "Please attempt at least one question."
            )
            
            context = self.get_context_data()
            context.update({
                "questions": questions,
                "submitted": True,
            })
            return self.render_to_response(context)
        
        # Calculate score percentage
        total_questions = questions.count()
        score_percent = int((correct_count / total_questions) * 100) if total_questions else 0
        is_passed = (score_percent == 100)  # Must be perfect to pass
        
        # Create practice attempt record
        practice_attempt = GrammarPracticeAttempt.objects.create(
            user=request.user,
            focus=focus,
            attempt_number=attempt_number,
            cycle_number=current_cycle,
            score_percent=score_percent,
            is_passed=is_passed,
            correct_answers=correct_count,
            total_questions=total_questions,
            questions_data={
                'questions': [
                    {
                        'id': q.id,
                        'text': q.question_text,
                        'correct': q.correct_answer,
                        'user_answer': q.user_answer,
                        'is_correct': q.is_correct
                    }
                    for q in questions if hasattr(q, 'user_answer') and q.user_answer
                ]
            }
        )
        
        # Link question attempts to practice attempt and bulk create
        for qa in question_attempts:
            qa.practice_attempt = practice_attempt
        
        if question_attempts:
            GrammarQuestionAttempt.objects.bulk_create(question_attempts)
        
        # Handle success/failure
        if is_passed:
            messages.success(
                request,
                f"Perfect score! You've unlocked the Final Test. "
                f"(Attempt {attempt_number}/3, Cycle {current_cycle})"
            )
            
            return redirect(
                "content:grammar:test",
                chunk_id=chunk.id,
                focus_id=focus.id
            )
        else:
            if attempt_number >= 3:
                # Max attempts reached in this cycle
                messages.warning(
                    request,
                    f"You've used all 3 attempts in cycle {current_cycle} "
                    f"with {score_percent}%. Start a new cycle to try again."
                )
            else:
                messages.warning(
                    request,
                    f"You scored {score_percent}% ({correct_count}/{total_questions}). "
                    f"Need 100% to unlock the Final Test. "
                    f"Attempts left this cycle: {3 - attempt_number}"
                )
        
        context = self.get_context_data()
        context.update({
            "questions": questions,
            "submitted": True,
            "score_percent": score_percent,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "practice_attempt": practice_attempt,
        })
        
        return self.render_to_response(context)


# Keep the function-based view for backward compatibility if needed
grammar_practice = GrammarPracticeView.as_view()