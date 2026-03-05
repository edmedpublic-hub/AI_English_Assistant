# content/views/grammar/practice.py

import random
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
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
    - Questions shuffled on each fresh GET
    - 100% required to pass and unlock test
    - Consecutive fail count tracked in Django session
    - 3 consecutive fails → suggest returning to teach page
    """
    template_name = "content/grammar/practice.html"

    # --- Session helpers ---
    def _session_key(self, focus_id):
        return f"grammar_practice_fails_{focus_id}"

    def get_consecutive_fails(self, focus_id):
        return self.request.session.get(self._session_key(focus_id), 0)

    def increment_fails(self, focus_id):
        key = self._session_key(focus_id)
        self.request.session[key] = self.request.session.get(key, 0) + 1
        self.request.session.modified = True

    def reset_fails(self, focus_id):
        self.request.session[self._session_key(focus_id)] = 0
        self.request.session.modified = True

    # --- Object helpers ---
    def get_chunk_and_focus(self):
        chunk = get_object_or_404(LessonChunk, id=self.kwargs['chunk_id'])
        focus = get_object_or_404(
            ChunkGrammarFocus, id=self.kwargs['focus_id'], chunk=chunk)
        return chunk, focus

    def get_questions(self, focus, shuffle=False):
        qs = list(GrammarQuestion.objects.filter(focus=focus))
        if shuffle:
            random.shuffle(qs)
        return qs

    def get_current_cycle(self, user, focus):
        latest = GrammarPracticeAttempt.objects.filter(
            user=user, focus=focus
        ).order_by('-cycle_number', '-attempt_number').first()
        return latest.cycle_number if latest else 1

    def get_current_attempt_number(self, user, focus, cycle_number):
        count = GrammarPracticeAttempt.objects.filter(
            user=user, focus=focus, cycle_number=cycle_number).count()
        return count + 1

    # --- GET ---
    def get_context_data(self, questions=None, submitted=False,
                         score_percent=None, correct_count=None,
                         total_questions=None, consecutive_fails=None,
                         suggest_reteach=False, **kwargs):
        context = super().get_context_data(**kwargs)
        chunk, focus = self.get_chunk_and_focus()

        if questions is None:
            questions = self.get_questions(focus, shuffle=True)
            for q in questions:
                q.user_answer = None
                q.is_correct = None
                q.feedback_ready = False

        if consecutive_fails is None:
            consecutive_fails = self.get_consecutive_fails(focus.id)

        context.update({
            "chunk": chunk,
            "focus": focus,
            "concept": focus.concept,
            "questions": questions,
            "submitted": submitted,
            "score_percent": score_percent,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "consecutive_fails": consecutive_fails,
            "suggest_reteach": consecutive_fails >= 3,
        })
        return context

    # --- POST ---
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        chunk, focus = self.get_chunk_and_focus()
        questions = self.get_questions(focus, shuffle=False)

        current_cycle = self.get_current_cycle(request.user, focus)
        attempt_number = self.get_current_attempt_number(
            request.user, focus, current_cycle)

        # Process answers
        correct_count = 0
        question_attempts = []
        any_answered = False

        for q in questions:
            user_answer = request.POST.get(f"q{q.id}", "").strip()
            if not user_answer:
                continue

            any_answered = True
            is_correct = (
                user_answer.lower().strip()
                == q.correct_answer.strip().lower()
            )

            if is_correct:
                correct_count += 1

            question_attempts.append(
                GrammarQuestionAttempt(
                    user=request.user,
                    question=q,
                    selected_answer=user_answer,
                    is_correct=is_correct,
                )
            )

            q.user_answer = user_answer
            q.is_correct = is_correct
            q.feedback_ready = True

        if not any_answered:
            messages.warning(request, "Please attempt at least one question.")
            return self.render_to_response(
                self.get_context_data(questions=questions, submitted=True))

        total_questions = len(questions)
        score_percent = int(
            (correct_count / total_questions) * 100) if total_questions else 0
        is_passed = (score_percent == 100)

        # Save attempt record
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
                        'user_answer': getattr(q, 'user_answer', None),
                        'is_correct': getattr(q, 'is_correct', None),
                    }
                    for q in questions if getattr(q, 'user_answer', None)
                ]
            }
        )

        for qa in question_attempts:
            qa.practice_attempt = practice_attempt
        if question_attempts:
            GrammarQuestionAttempt.objects.bulk_create(question_attempts)

        # --- PASS: reset fails, go to test ---
        if is_passed:
            self.reset_fails(focus.id)
            messages.success(
                request, "Perfect score! You've unlocked the Final Test.")
            return redirect(
                "content:grammar:test",
                chunk_id=chunk.id,
                focus_id=focus.id,
            )

        # --- FAIL: increment and re-render with feedback ---
        self.increment_fails(focus.id)
        consecutive_fails = self.get_consecutive_fails(focus.id)

        return self.render_to_response(
            self.get_context_data(
                questions=questions,
                submitted=True,
                score_percent=score_percent,
                correct_count=correct_count,
                total_questions=total_questions,
                consecutive_fails=consecutive_fails,
            )
        )


grammar_practice = GrammarPracticeView.as_view()