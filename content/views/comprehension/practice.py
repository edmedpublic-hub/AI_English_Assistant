# PATH: content/views/comprehension/practice.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionQuestion,
    ComprehensionPracticeAttempt,
    ComprehensionQuestionAttempt,
)
from content.services.comprehension.comprehension_mastery import is_focus_mastered


class ComprehensionPracticeView(LoginRequiredMixin, View):
    """
    HTML practice view for comprehension focuses.

    GET  — renders practice.html with questions
    POST — scores answers, saves attempt, redirects to practice-result
    """

    template_name = "content/comprehension/practice.html"

    # ── shared helpers ────────────────────────────────────────

    def _get_focus(self, chunk_id, focus_id):
        return get_object_or_404(
            ChunkComprehensionFocus.objects.select_related("chunk"),
            id=focus_id,
            chunk_id=chunk_id,
        )

    def _enforce_progression(self, request, focus, chunk_id):
        previous = (
            ChunkComprehensionFocus.objects
            .filter(chunk=focus.chunk, sequence_order__lt=focus.sequence_order)
            .order_by("-sequence_order")
            .first()
        )
        if previous and not is_focus_mastered(request.user, previous):
            messages.error(
                request,
                f"You must master '{previous.focus_title}' "
                f"({previous.get_level_display()}) first.",
            )
            return redirect(
                "content:comprehension:teach",
                chunk_id=chunk_id,
                focus_id=previous.id,
            )
        return None

    def _get_cycle_and_attempt(self, user, focus):
        latest = (
            ComprehensionPracticeAttempt.objects
            .filter(user=user, focus=focus)
            .order_by("-cycle_number", "-attempt_number")
            .first()
        )
        if not latest:
            return 1, 1

        cycle   = latest.cycle_number
        attempt = latest.attempt_number + 1

        if attempt > 3:
            cycle  += 1
            attempt = 1

        return cycle, attempt

    def _get_questions(self, focus):
        questions = list(
            ComprehensionQuestion.objects
            .filter(focus=focus)
            .order_by("difficulty", "id")
        )
        for q in questions:
            if q.question_type == ComprehensionQuestion.TYPE_TRUE_FALSE:
                q.tf_options = ["True", "False"]
            else:
                q.tf_options = []
        return questions

    # ── GET ───────────────────────────────────────────────────

    def get(self, request, chunk_id, focus_id):
        focus = self._get_focus(chunk_id, focus_id)

        redirect_response = self._enforce_progression(request, focus, chunk_id)
        if redirect_response:
            return redirect_response

        questions = self._get_questions(focus)

        latest_attempt = (
            ComprehensionPracticeAttempt.objects
            .filter(user=request.user, focus=focus)
            .order_by("-attempted_at")
            .first()
        )

        previous_answers = {}
        if latest_attempt and latest_attempt.questions_data:
            for q_data in latest_attempt.questions_data.get("questions", []):
                previous_answers[q_data["id"]] = q_data.get("user_answer", "")

        for q in questions:
            q.user_answer    = previous_answers.get(q.id, "")
            q.feedback_ready = False

        cycle, attempt = self._get_cycle_and_attempt(request.user, focus)

        context = {
            "chunk":          focus.chunk,
            "focus":          focus,
            "questions":      questions,
            "submitted":      False,
            "cycle_number":   cycle,
            "attempt_number": attempt,
            "attempts_left":  3 - (attempt - 1),
        }
        return render(request, self.template_name, context)

    # ── POST ──────────────────────────────────────────────────

    @transaction.atomic
    def post(self, request, chunk_id, focus_id):
        focus = self._get_focus(chunk_id, focus_id)

        redirect_response = self._enforce_progression(request, focus, chunk_id)
        if redirect_response:
            return redirect_response

        questions      = self._get_questions(focus)
        cycle, attempt = self._get_cycle_and_attempt(request.user, focus)

        correct_count     = 0
        auto_scorable     = 0
        question_attempts = []

        for q in questions:
            raw_answer = request.POST.get(f"q{q.id}", "").strip()
            is_correct = False

            if q.question_type == ComprehensionQuestion.TYPE_MCQ:
                auto_scorable += 1
                if raw_answer:
                    is_correct = (
                        raw_answer.lower()
                        == (q.correct_answer or "").strip().lower()
                    )

            elif q.question_type == ComprehensionQuestion.TYPE_TRUE_FALSE:
                auto_scorable += 1
                if raw_answer:
                    is_correct = (
                        raw_answer.lower()
                        == (q.correct_answer or "").strip().lower()
                    )

            elif q.question_type == ComprehensionQuestion.TYPE_SHORT_ANSWER:
                auto_scorable += 1
                if raw_answer:
                    is_correct = (
                        raw_answer.lower()
                        == (q.correct_answer or "").strip().lower()
                    )

            elif q.question_type == ComprehensionQuestion.TYPE_OPEN_ENDED:
                pass  # not auto-scored

            if is_correct:
                correct_count += 1

            question_attempts.append({
                "question":        q,
                "selected_answer": raw_answer,
                "is_correct":      is_correct,
            })

        total_for_score = auto_scorable or len(questions)
        score_percent   = int((correct_count / total_for_score) * 100)
        is_passed       = (score_percent == 100)

        practice_attempt = ComprehensionPracticeAttempt.objects.create(
            user            = request.user,
            focus           = focus,
            attempt_number  = attempt,
            cycle_number    = cycle,
            score_percent   = score_percent,
            is_passed       = is_passed,
            correct_answers = correct_count,
            total_questions = total_for_score,
            questions_data  = {
                "questions": [
                    {
                        "id":          qa["question"].id,
                        "text":        qa["question"].question_text,
                        "type":        qa["question"].question_type,
                        "correct":     qa["question"].correct_answer,
                        "options":     qa["question"].get_options_list(),
                        "user_answer": qa["selected_answer"],
                        "is_correct":  qa["is_correct"],
                    }
                    for qa in question_attempts
                ],
                "cycle_number":   cycle,
                "attempt_number": attempt,
                "focus_title":    focus.focus_title,
                "level":          focus.level,
            },
        )

        ComprehensionQuestionAttempt.objects.bulk_create(
            [
                ComprehensionQuestionAttempt(
                    user             = request.user,
                    question         = qa["question"],
                    practice_attempt = practice_attempt,
                    selected_answer  = qa["selected_answer"],
                    is_correct       = qa["is_correct"],
                    cycle_number     = cycle,
                    attempt_number   = attempt,
                )
                for qa in question_attempts
            ],
            ignore_conflicts=True,  # prevents IntegrityError on retry
        )

        if is_passed:
            messages.success(
                request,
                f"Perfect score! You've passed practice for "
                f"'{focus.focus_title}'. You can now take the test.",
            )
        else:
            remaining = 3 - attempt
            if remaining > 0:
                messages.warning(
                    request,
                    f"You scored {score_percent}%. "
                    f"{remaining} attempt(s) remaining in this cycle.",
                )
            else:
                messages.warning(
                    request,
                    f"You scored {score_percent}%. "
                    f"All 3 attempts used. A new cycle will begin next time.",
                )

        return redirect(
            "content:comprehension:practice-result-detail",
            chunk_id=chunk_id,
            focus_id=focus_id,
            practice_id=practice_attempt.id,
        )