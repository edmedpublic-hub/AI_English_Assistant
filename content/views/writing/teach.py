# content/views/writing/teach.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
import re

from content.models.core import Unit
from content.models.writing import (
    WritingStage,
    WritingStageContent,
    WritingAttempt,
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

        status = get_stage_status(
            request.user, self.content, self.academic_year
        )
        if status == "locked":
            messages.warning(
                request,
                "Complete the previous stage before starting this one."
            )
            return redirect("content:writing_hub", unit_id=unit_id)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context   = super().get_context_data(**kwargs)
        user      = self.request.user

        stage_ctx = build_stage_context(
            user, self.content, self.academic_year
        )
        context.update(stage_ctx)

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

        latest_dissect = previous_attempts.first()
        dissect_passed = previous_attempts.filter(
            status=STATUS_PASSED
        ).exists()

        context.update({
            "previous_attempts":       previous_attempts,
            "latest_dissect":          latest_dissect,
            "dissect_passed":          dissect_passed,
            "attempt_count":           previous_attempts.count(),
            "active_phase":            PHASE_DISSECT,
            "show_proceed_to_imitate": dissect_passed,
            "show_proceed_to_produce": (
                dissect_passed
                and stage_ctx.get("phase_imitate_done", False)
            ),
        })

        return context


class WritingTeachSubmitView(LoginRequiredMixin, TemplateView):
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
                request, "Writing is not available right now.", unit_id
            )

        status = get_stage_status(request.user, content, academic_year)
        if status == "locked":
            return self._error_response(
                request, "This stage is not yet available.", unit_id
            )

        response_text = request.POST.get("response_text", "").strip()
        if not response_text:
            return self._error_response(
                request, "Please write your answer before submitting.", unit_id
            )

        evaluation     = _evaluate_dissect(response_text, content)
        attempt_number = get_next_attempt_number(
            request.user, content, academic_year, PHASE_DISSECT
        )

        attempt = WritingAttempt.objects.create(
            user               = request.user,
            content            = content,
            academic_year      = academic_year,
            phase              = PHASE_DISSECT,
            attempt_number     = attempt_number,
            response_text      = response_text,
            status             = STATUS_PASSED if evaluation["passed"] else STATUS_FAILED,
            auto_score         = evaluation["score"],
            auto_checks        = evaluation["checks"],
            time_spent_seconds = _parse_time_spent(request),
        )

        result = {
            "passed":         evaluation["passed"],
            "score":          evaluation["score"],
            "feedback":       evaluation["feedback"],
            "correct_answer": content.dissect_answer,
            "attempt_number": attempt_number,
            "attempt_id":     attempt.id,
        }

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(result)

        if evaluation["passed"]:
            messages.success(
                request, "Good work. You have completed the Dissect phase."
            )
        else:
            messages.warning(request, evaluation["feedback"])

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
# DISSECT EVALUATION
# ============================================================

def _evaluate_dissect(response_text, content):
    """
    Evaluate the student's dissect answer.

    Strategy:
    1. Exact match → 100, pass
    2. Role-pair match — checks subject/verb assigned correctly
       This prevents "subject: yearned, verb: humanity" passing
    3. Key terms fallback — for free-form answers
    """
    student = _normalise(response_text)
    correct = _normalise(content.dissect_answer)

    # ── 1. Exact match ────────────────────────────────
    if student == correct:
        return {
            "passed":   True,
            "score":    100,
            "checks":   {"exact_match": True},
            "feedback": "Correct. Well done.",
        }

    # ── 2. Role-pair matching ─────────────────────────
    correct_pairs = _extract_role_pairs(correct)
    student_pairs = _extract_role_pairs(student)
    checks        = {}

    if correct_pairs:
        correct_roles = 0
        wrong_roles   = []

        for role, word in correct_pairs.items():
            student_word = student_pairs.get(role, "")
            if word and word in student_word:
                correct_roles += 1
            else:
                wrong_roles.append(role)

        ratio = correct_roles / len(correct_pairs)
        checks["role_pair_ratio"] = ratio
        checks["wrong_roles"]     = wrong_roles

        if ratio == 1.0:
            return {
                "passed":   True,
                "score":    100,
                "checks":   checks,
                "feedback": "Correct. Well done.",
            }

        if ratio >= 0.5:
            return {
                "passed":   False,
                "score":    int(ratio * 100),
                "checks":   checks,
                "feedback": (
                    f"Not quite. Check these: "
                    f"{', '.join(wrong_roles)}. "
                    f"Look at the sentence again carefully."
                ),
            }

        return {
            "passed":   False,
            "score":    int(ratio * 100),
            "checks":   checks,
            "feedback": (
                f"{_build_dissect_hint(content)} "
                f"Look at the model sentence again and try once more."
            ),
        }

    # ── 3. Key terms fallback ─────────────────────────
    # Used when dissect_answer is free-form, not role:word format
    key_terms   = [w.lower() for w in correct.split() if len(w) > 3]
    terms_found = [t for t in key_terms if t in student.lower()]
    term_ratio  = len(terms_found) / len(key_terms) if key_terms else 0

    checks["key_terms_ratio"] = term_ratio
    checks["terms_found"]     = terms_found
    checks["terms_missing"]   = [
        t for t in key_terms if t not in student.lower()
    ]

    if term_ratio >= 0.8:
        return {
            "passed":   True,
            "score":    80,
            "checks":   checks,
            "feedback": "Good answer. You identified the key parts correctly.",
        }

    if term_ratio >= 0.6:
        missing = checks["terms_missing"]
        return {
            "passed":   True,
            "score":    60,
            "checks":   checks,
            "feedback": (
                "Your answer is mostly correct. "
                f"You could also mention: {', '.join(missing[:3])}."
            ),
        }

    return {
        "passed":   False,
        "score":    int(term_ratio * 100),
        "checks":   checks,
        "feedback": (
            f"Not quite. {_build_dissect_hint(content)} "
            f"Look at the model sentence again and try once more."
        ),
    }


def _extract_role_pairs(text):
    """
    Extract role→word mappings from a dissect answer.

    Handles:
        "subject: humanity, verb: yearned"
        "subject is humanity and verb is yearned"
        "humanity is the subject, yearned is the verb"

    Returns:
        {"subject": "humanity", "verb": "yearned"}
    """
    pairs = {}
    roles = [
        "subject", "verb", "object", "adjective",
        "adverb", "conjunction", "clause"
    ]

    for role in roles:
        # Pattern 1: "subject: humanity" or "subject is humanity"
        pattern1 = rf'{role}\s*[:=is]+\s*(["\']?[\w\s]+?["\']?)(?:,|and|$|\n)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            pairs[role] = match.group(1).strip().lower()
            continue

        # Pattern 2: "humanity is the subject"
        pattern2 = rf'([\w]+)\s+is\s+(?:the\s+)?{role}'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            pairs[role] = match.group(1).strip().lower()

    return pairs


def _normalise(text):
    """Lowercase, strip, collapse spaces."""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def _build_dissect_hint(content):
    """
    Build a hint from the dissect question.
    Points toward what to look for without revealing the answer.
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
    """Parse time_spent_seconds from POST. Returns None if missing."""
    try:
        val = request.POST.get("time_spent_seconds")
        return int(val) if val else None
    except (ValueError, TypeError):
        return None