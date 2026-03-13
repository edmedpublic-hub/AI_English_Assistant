# PATH: content/views/comprehension/test.py

from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View

from content.models.comprehension import (
    ComprehensionQuestion,
    ComprehensionTestAttempt,
    ComprehensionQuestionAttempt,
    ChunkComprehensionFocus,
)
from content.services.comprehension.comprehension_mastery import is_focus_mastered


@method_decorator(login_required, name="dispatch")
class ComprehensionTestSubmitView(View):
    """
    Mastery test view for comprehension focuses.

    GET  — renders test.html with questions
    POST — scores answers, saves attempt, redirects to test-result
    """

    template_name = "content/comprehension/test.html"

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
            ComprehensionTestAttempt.objects
            .filter(user=user, focus=focus)
            .order_by("-cycle_number", "-attempt_number")
            .first()
        )
        if not latest:
            return 1, 1

        if latest.is_mastered:
            return latest.cycle_number, latest.attempt_number

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

        if is_focus_mastered(request.user, focus):
            messages.info(request, "You have already mastered this focus.")
            return redirect("content:chunk_comprehension", chunk_id=chunk_id)

        questions      = self._get_questions(focus)
        cycle, attempt = self._get_cycle_and_attempt(request.user, focus)

        context = {
            "chunk":          focus.chunk,
            "focus":          focus,
            "questions":      questions,
            "cycle_number":   cycle,
            "attempt_number": attempt,
            "attempts_left":  3 - (attempt - 1),
        }
        return render(request, self.template_name, context)

    # ── POST ──────────────────────────────────────────────────

    @transaction.atomic
    def post(self, request, chunk_id, focus_id):
        focus   = self._get_focus(chunk_id, focus_id)
        student = request.user

        redirect_response = self._enforce_progression(request, focus, chunk_id)
        if redirect_response:
            return redirect_response

        if is_focus_mastered(student, focus):
            messages.info(request, "You have already mastered this focus.")
            return redirect("content:chunk_comprehension", chunk_id=chunk_id)

        cycle, attempt = self._get_cycle_and_attempt(student, focus)

        questions = self._get_questions(focus)
        if not questions:
            messages.error(request, "No questions configured for this focus.")
            return redirect(
                "content:comprehension:teach",
                chunk_id=chunk_id,
                focus_id=focus_id,
            )

        # Validate all answered
        answers = {}
        missing = []
        for q in questions:
            answer = request.POST.get(f"q{q.id}", "").strip()
            if not answer and q.question_type != ComprehensionQuestion.TYPE_OPEN_ENDED:
                missing.append(str(q.id))
            answers[q.id] = answer

        if missing:
            messages.error(request, "Please answer all questions before submitting.")
            return redirect(
                "content:comprehension:test",
                chunk_id=chunk_id,
                focus_id=focus_id,
            )

        # Score
        correct_count     = 0
        auto_scorable     = 0
        question_attempts = []

        for q in questions:
            selected   = answers[q.id]
            is_correct = False

            if q.question_type == ComprehensionQuestion.TYPE_MCQ:
                auto_scorable += 1
                if selected:
                    is_correct = (
                        selected.lower()
                        == (q.correct_answer or "").strip().lower()
                    )

            elif q.question_type == ComprehensionQuestion.TYPE_TRUE_FALSE:
                auto_scorable += 1
                if selected:
                    is_correct = (
                        selected.lower()
                        == (q.correct_answer or "").strip().lower()
                    )

            elif q.question_type == ComprehensionQuestion.TYPE_SHORT_ANSWER:
                auto_scorable += 1
                if selected:
                    is_correct = (
                        selected.lower()
                        == (q.correct_answer or "").strip().lower()
                    )

            elif q.question_type == ComprehensionQuestion.TYPE_OPEN_ENDED:
                pass  # not auto-scored

            if is_correct:
                correct_count += 1

            question_attempts.append({
                "question":        q,
                "selected_answer": selected,
                "is_correct":      is_correct,
            })

        total_for_score = auto_scorable or len(questions)
        score_percent   = int(round((correct_count / total_for_score) * 100))
        is_mastered     = (score_percent == 100)

        # Save test attempt
        test_attempt = ComprehensionTestAttempt.objects.create(
            user            = student,
            focus           = focus,
            attempt_number  = attempt,
            cycle_number    = cycle,
            score_percent   = score_percent,
            is_mastered     = is_mastered,
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

        # Save per-question attempts
        ComprehensionQuestionAttempt.objects.bulk_create([
            ComprehensionQuestionAttempt(
                user            = student,
                question        = qa["question"],
                test_attempt    = test_attempt,
                selected_answer = qa["selected_answer"],
                is_correct      = qa["is_correct"],
                cycle_number    = cycle,
                attempt_number  = attempt,
            )
            for qa in question_attempts
        ],
        ignore_conflicts=True  # in case of retries, avoid duplicate question attempts                                           
)

        # Feedback messages
        if is_mastered:
            messages.success(
                request,
                f"🎉 You have mastered '{focus.focus_title}' with a perfect score!",
            )
            next_focus = ChunkComprehensionFocus.objects.filter(
                chunk=focus.chunk,
                sequence_order=focus.sequence_order + 1,
            ).first()
            if next_focus:
                messages.info(
                    request,
                    f"You have unlocked: {next_focus.focus_title} "
                    f"({next_focus.get_level_display()})",
                )
        else:
            remaining = 3 - attempt
            if remaining > 0:
                messages.warning(
                    request,
                    f"You scored {score_percent}%. "
                    f"{remaining} attempt(s) remaining in cycle {cycle}.",
                )
            else:
                messages.warning(
                    request,
                    f"You scored {score_percent}%. "
                    f"All 3 attempts used. A new cycle will begin next time.",
                )

        return redirect(
            "content:comprehension:test-result",
            chunk_id=chunk_id,
            focus_id=focus.id,
        )