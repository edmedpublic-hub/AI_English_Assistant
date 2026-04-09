# content/views/writing/teach.py
#
# Handles the Dissect phase — the Teach phase of each stage.
# The student studies a model sentence, sees the converted
# version alongside it, reads the conversion note, then
# answers the dissect question to demonstrate understanding.
#
# URL patterns expected:
#   writing/unit/<unit_id>/stage/<stage_id>/teach/     → WritingTeachView (GET)
#   writing/unit/<unit_id>/stage/<stage_id>/teach/     → WritingTeachSubmitView (POST)
#
# What GET does:
#   1. Loads the stage content
#   2. Checks stage is not locked
#   3. Builds context including previous dissect attempt if any
#   4. Renders the dissect phase template
#
# What POST does:
#   1. Validates the student's answer
#   2. Creates a WritingAttempt for the dissect phase
#   3. Evaluates automatically — simple text comparison
#   4. Returns result — pass routes to imitate or produce
#      fail shows what was wrong and allows retry immediately
#      (no cooldown on dissect phase)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import json

from content.models.core import Unit
from content.models.writing import (
    WritingStage,
    WritingStageContent,
    WritingAttempt,
    WritingAcademicYear,
    PHASE_DISSECT,
    STATUS_PASSED,
    STATUS_FAILED,
)
from .core import (
    get_current_academic_year,
    get_stage_status,
    get_next_attempt_number,
    build_stage_context,
)


class WritingTeachView(LoginRequiredMixin, TemplateView):
    """
    GET — renders the Dissect phase for a stage.
    Shows model sentence, converted version, conversion note,
    and the dissect question for the student to answer.
    """
    template_name = "content/writing/teach.html"

    def get(self, request, unit_id, stage_id, *args, **kwargs):
        self.unit    = get_object_or_404(Unit, pk=unit_id)
        self.stage   = get_object_or_404(WritingStage, pk=stage_id)
        self.content = get_object_or_404(
            WritingStageContent,
            stage=self.stage,
            unit=self.unit,
            is_complete=True,
        )
        self.academic_year = get_current_academic_year()

        if not self.academic_year:
            messages.error(
                request,
                "Writing is not available right now. "
                "Please check back later."
            )
            return redirect("content:writing_hub", unit_id=unit_id)

        # Check stage is not locked
        status = get_stage_status(
            request.user,
            self.content,
            self.academic_year,
        )
        if status == "locked":
            messages.warning(
                request,
                "Complete the previous stage before starting this one."
            )
            return redirect("content:writing_hub", unit_id=unit_id)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user    = self.request.user

        # Base stage context from core.py
        stage_ctx = build_stage_context(
            user,
            self.content,
            self.academic_year,
        )
        context.update(stage_ctx)

        # Previous dissect attempts for this stage
        previous_attempts = (
            WritingAttempt.objects
            .filter(
                user=user,
                content=self.content,
                academic_year=self.academic_year,
                phase=PHASE_DISSECT,
            )
            .order_by("-created_at")
        )

        # Latest dissect attempt — shown as previous answer
        latest_dissect = previous_attempts.first()

        # Has the student already passed dissect?
        dissect_passed = previous_attempts.filter(
            status=STATUS_PASSED,
        ).exists()

        context.update({
            "previous_attempts": previous_attempts,
            "latest_dissect":    latest_dissect,
            "dissect_passed":    dissect_passed,
            "attempt_count":     previous_attempts.count(),

            # Show the student which phase they are on
            "active_phase":      PHASE_DISSECT,

            # Phase navigation — which phases are done
            "show_proceed_to_imitate": dissect_passed,
            "show_proceed_to_produce": (
                dissect_passed
                and stage_ctx.get("phase_imitate_done", False)
            ),
        })

        return context


class WritingTeachSubmitView(LoginRequiredMixin, TemplateView):
    """
    POST — receives the student's dissect answer,
    evaluates it, creates a WritingAttempt record,
    and returns the result.

    Dissect evaluation:
    - Simple text comparison against dissect_answer
    - Case-insensitive, whitespace-normalised
    - Partial credit: if student answer contains
      the key parts of the correct answer
    - No cooldown — student can retry dissect immediately

    Returns JSON for AJAX submission or redirects for
    standard form submission.
    """
    template_name = "content/writing/teach.html"

    def post(self, request, unit_id, stage_id, *args, **kwargs):
        unit    = get_object_or_404(Unit, pk=unit_id)
        stage   = get_object_or_404(WritingStage, pk=stage_id)
        content = get_object_or_404(
            WritingStageContent,
            stage=stage,
            unit=unit,
            is_complete=True,
        )
        academic_year = get_current_academic_year()

        if not academic_year:
            return self._error_response(
                request,
                "Writing is not available right now.",
                unit_id,
            )

        # Check stage is not locked
        status = get_stage_status(request.user, content, academic_year)
        if status == "locked":
            return self._error_response(
                request,
                "This stage is not yet available.",
                unit_id,
            )

        # Get student's answer
        response_text = request.POST.get("response_text", "").strip()
        if not response_text:
            return self._error_response(
                request,
                "Please write your answer before submitting.",
                unit_id,
            )

        # Evaluate the dissect answer
        evaluation = _evaluate_dissect(response_text, content)

        # Record the attempt
        attempt_number = get_next_attempt_number(
            request.user,
            content,
            academic_year,
            PHASE_DISSECT,
        )

        attempt = WritingAttempt.objects.create(
            user          = request.user,
            content       = content,
            academic_year = academic_year,
            phase         = PHASE_DISSECT,
            attempt_number = attempt_number,
            response_text = response_text,
            status        = STATUS_PASSED if evaluation["passed"] else STATUS_FAILED,
            auto_score    = evaluation["score"],
            auto_checks   = evaluation["checks"],
            time_spent_seconds = _parse_time_spent(request),
        )

        # Build response context
        result = {
            "passed":           evaluation["passed"],
            "score":            evaluation["score"],
            "feedback":         evaluation["feedback"],
            "correct_answer":   content.dissect_answer,
            "attempt_number":   attempt_number,
            "attempt_id":       attempt.id,
        }

        # AJAX request — return JSON
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(result)

        # Standard form submission — redirect with message
        if evaluation["passed"]:
            messages.success(
                request,
                "Good work. You have completed the Dissect phase."
            )
        else:
            messages.warning(
                request,
                evaluation["feedback"]
            )

        return redirect(
            "content:writing_teach",
            unit_id=unit_id,
            stage_id=stage_id,
        )

    def _error_response(self, request, message, unit_id):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": message}, status=400)
        messages.error(request, message)
        return redirect("content:writing_hub", unit_id=unit_id)


# ============================================================
# DISSECT EVALUATION LOGIC
# ============================================================

def _evaluate_dissect(response_text, content):
    """
    Evaluate the student's dissect answer.

    Strategy:
    1. Exact match (case-insensitive, normalised) → 100%
    2. Key terms match — student answer contains the
       essential parts of the correct answer → 80%
    3. Partial match — student answer shares significant
       overlap with correct answer → 60% (pass threshold)
    4. Poor match → fail with specific feedback

    Pass threshold: score >= 60

    Returns:
    {
        'passed': bool,
        'score': int,
        'checks': dict,
        'feedback': str,
    }
    """
    student  = _normalise(response_text)
    correct  = _normalise(content.dissect_answer)

    checks   = {}
    feedback = ""

    # ── Check 1: Exact match ──────────────────────────────
    if student == correct:
        return {
            "passed":   True,
            "score":    100,
            "checks":   {"exact_match": True},
            "feedback": "Correct. Well done.",
        }

    # ── Check 2: Key terms present ────────────────────────
    # Extract key terms from correct answer
    # (words longer than 3 characters — ignore articles/prepositions)
    key_terms = [
        w for w in correct.split()
        if len(w) > 3
    ]
    terms_found = [t for t in key_terms if t in student]
    term_ratio  = len(terms_found) / len(key_terms) if key_terms else 0

    checks["key_terms_ratio"] = term_ratio
    checks["terms_found"]     = terms_found
    checks["terms_missing"]   = [
        t for t in key_terms if t not in student
    ]

    if term_ratio >= 0.8:
        return {
            "passed":   True,
            "score":    80,
            "checks":   checks,
            "feedback": (
                "Good answer. You identified the key parts correctly."
            ),
        }

    if term_ratio >= 0.6:
        missing = checks["terms_missing"]
        return {
            "passed":   True,
            "score":    60,
            "checks":   checks,
            "feedback": (
                "Your answer is mostly correct. "
                "You could also mention: "
                f"{', '.join(missing[:3])}."
            ),
        }

    # ── Check 3: Poor match — fail ────────────────────────
    # Give the student a specific hint without
    # revealing the full answer
    hint = _build_dissect_hint(content)

    return {
        "passed":   False,
        "score":    int(term_ratio * 100),
        "checks":   checks,
        "feedback": (
            f"Not quite. {hint} "
            f"Look at the model sentence again and try once more."
        ),
    }


def _normalise(text):
    """
    Normalise text for comparison:
    lowercase, strip whitespace, collapse multiple spaces.
    """
    import re
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def _build_dissect_hint(content):
    """
    Build a hint based on the dissect question.
    Does not reveal the answer — points the student
    toward what to look for.
    """
    question = content.dissect_question.lower()

    if "subject" in question:
        return (
            "Look for who or what the sentence is about — "
            "that is the subject."
        )
    if "verb" in question:
        return (
            "Look for the action word or state word — "
            "that is the verb."
        )
    if "object" in question:
        return (
            "Look for who or what receives the action — "
            "that is the object."
        )
    if "conjunction" in question:
        return (
            "Look for the joining word that connects "
            "the two parts of the sentence."
        )
    if "adjective" in question or "adverb" in question:
        return (
            "Look for the describing word — "
            "it tells you more about a noun or verb."
        )
    return (
        "Read the model sentence carefully and "
        "look for the part the question is asking about."
    )


def _parse_time_spent(request):
    """
    Parse time_spent_seconds from POST data.
    Returns None if not present or invalid.
    """
    try:
        val = request.POST.get("time_spent_seconds")
        return int(val) if val else None
    except (ValueError, TypeError):
        return None