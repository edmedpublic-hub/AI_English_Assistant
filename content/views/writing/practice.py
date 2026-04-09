# content/views/writing/practice.py
#
# Handles the Imitate phase — the Practice phase of each stage.
# The student is given a sentence frame and fills it with
# their own words to produce a correct sentence or paragraph.
#
# URL patterns expected:
#   writing/unit/<unit_id>/stage/<stage_id>/practice/    → WritingPracticeView (GET)
#   writing/unit/<unit_id>/stage/<stage_id>/practice/    → WritingPracticeSubmitView (POST)
#
# What GET does:
#   1. Loads the stage content
#   2. Checks stage is not locked
#   3. Builds context including the imitate frame
#      and previous imitate attempts if any
#   4. Renders the imitate phase template
#
# What POST does:
#   1. Validates the student's filled frame response
#   2. Runs the same automatic checks as Produce
#      (structure is given — evaluation is on correctness)
#   3. For paragraph stages — runs sentence-level
#      intervention detection
#   4. Creates a WritingAttempt for the imitate phase
#   5. Creates WritingIntervention records if needed
#   6. Returns result — pass allows proceeding to Produce
#      fail shows specific feedback, retry allowed immediately
#      (no cooldown on imitate phase)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from content.models.core import Unit
from content.models.writing import (
    WritingStage,
    WritingStageContent,
    WritingAttempt,
    WritingIntervention,
    PHASE_DISSECT,
    PHASE_IMITATE,
    PHASE_PRODUCE,
    STATUS_PASSED,
    STATUS_FAILED,
    TIER_SENTENCE,
)
from .core import (
    get_current_academic_year,
    get_stage_status,
    get_next_attempt_number,
    build_stage_context,
    evaluate_automatic,
    detect_sentence_interventions,
)


class WritingPracticeView(LoginRequiredMixin, TemplateView):
    """
    GET — renders the Imitate phase for a stage.
    Shows the sentence frame and instructions.
    Student fills the frame with their own words.
    """
    template_name = "content/writing/practice.html"

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

        # Previous imitate attempts
        previous_attempts = (
            WritingAttempt.objects
            .filter(
                user=user,
                content=self.content,
                academic_year=self.academic_year,
                phase=PHASE_IMITATE,
            )
            .order_by("-created_at")
        )

        latest_imitate = previous_attempts.first()

        # Has the student already passed imitate?
        imitate_passed = previous_attempts.filter(
            status=STATUS_PASSED,
        ).exists()

        # Interventions from latest failed attempt
        latest_interventions = []
        if latest_imitate and latest_imitate.status == STATUS_FAILED:
            latest_interventions = list(
                latest_imitate.interventions
                .filter(is_resolved=False)
                .order_by("id")
            )

        # Parse the frame into display parts
        # Splits on ___ to show the student where to write
        frame_parts = _parse_frame(self.content.imitate_frame)

        context.update({
            "previous_attempts":    previous_attempts,
            "latest_imitate":       latest_imitate,
            "imitate_passed":       imitate_passed,
            "attempt_count":        previous_attempts.count(),
            "latest_interventions": latest_interventions,

            # Frame display
            "frame_parts":          frame_parts,
            "frame_has_blanks":     "___" in self.content.imitate_frame,

            # Active phase
            "active_phase":         PHASE_IMITATE,

            # Phase navigation
            "show_proceed_to_produce": imitate_passed,
            "dissect_available": True,
            "dissect_passed":    stage_ctx.get("phase_dissect_done", False),
        })

        return context


class WritingPracticeSubmitView(LoginRequiredMixin, TemplateView):
    """
    POST — receives the student's imitate response,
    evaluates it, records the attempt, handles
    sentence-level interventions for paragraph stages.

    Evaluation:
    - Same automatic checks as Produce phase
    - For paragraph stages (stage 6+): sentence-level
      intervention detection runs on every submission
    - Interventions stored and shown to student
    - No cooldown — student retries imitate immediately

    Pass → student proceeds to Produce phase
    Fail → student sees specific feedback and interventions
    """
    template_name = "content/writing/practice.html"

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

        # Get student's response
        response_text = request.POST.get("response_text", "").strip()
        if not response_text:
            return self._error_response(
                request,
                "Please write your response before submitting.",
                unit_id,
            )

        # ── Run automatic evaluation ──────────────────────
        evaluation = evaluate_automatic(
            response_text,
            content,
            PHASE_IMITATE,
        )

        # ── Sentence-level intervention detection ─────────
        # Only for paragraph stages (stage 6+)
        interventions_data = []
        if stage.number >= 6:
            interventions_data = detect_sentence_interventions(
                response_text,
                stage.number,
            )

        # ── Determine pass/fail ───────────────────────────
        # Fail if automatic checks failed OR
        # if there are unresolved sentence interventions
        has_interventions = len(interventions_data) > 0
        passed = evaluation["passed"] and not has_interventions

        # ── Record the attempt ────────────────────────────
        attempt_number = get_next_attempt_number(
            request.user,
            content,
            academic_year,
            PHASE_IMITATE,
        )

        attempt = WritingAttempt.objects.create(
            user               = request.user,
            content            = content,
            academic_year      = academic_year,
            phase              = PHASE_IMITATE,
            attempt_number     = attempt_number,
            response_text      = response_text,
            status             = STATUS_PASSED if passed else STATUS_FAILED,
            auto_score         = evaluation["score"],
            auto_checks        = evaluation["checks"],
            intervention_flags = interventions_data,
            time_spent_seconds = _parse_time_spent(request),
        )

        # ── Create intervention records ───────────────────
        created_interventions = []
        for iv_data in interventions_data:
            iv = WritingIntervention.objects.create(
                attempt       = attempt,
                sentence_text = iv_data["sentence"],
                issue_label   = iv_data["issue"],
                fix_exercise  = iv_data["fix_exercise"],
            )
            created_interventions.append(iv)

        # ── Build result ──────────────────────────────────
        result = {
            "passed":           passed,
            "score":            evaluation["score"],
            "feedback":         evaluation["feedback"],
            "checks":           evaluation["checks"],
            "word_count":       evaluation["word_count"],
            "keywords_found":   evaluation["keywords_found"],
            "keywords_missing": evaluation["keywords_missing"],
            "attempt_number":   attempt_number,
            "attempt_id":       attempt.id,
            "interventions":    [
                {
                    "id":           iv.id,
                    "sentence":     iv.sentence_text,
                    "issue":        iv.issue_label,
                    "fix_exercise": iv.fix_exercise,
                }
                for iv in created_interventions
            ],
        }

        # ── AJAX response ─────────────────────────────────
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(result)

        # ── Standard form response ────────────────────────
        if passed:
            messages.success(
                request,
                "Well done. You have completed the Imitate phase. "
                "You are ready to write on your own."
            )
        else:
            if has_interventions:
                messages.warning(
                    request,
                    "Some sentences need attention. "
                    "Fix the highlighted sentences and try again."
                )
            else:
                messages.warning(
                    request,
                    evaluation["feedback"]
                )

        return redirect(
            "content:writing_practice",
            unit_id=unit_id,
            stage_id=stage_id,
        )

    def _error_response(self, request, message, unit_id):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": message}, status=400)
        messages.error(request, message)
        return redirect("content:writing_hub", unit_id=unit_id)


# ============================================================
# INTERVENTION FIX SUBMISSION
# ============================================================

class WritingInterventionFixView(LoginRequiredMixin, TemplateView):
    """
    POST — receives the student's fix attempt for a
    sentence-level intervention.

    The student rewrites the problematic sentence.
    The fix is recorded and the intervention marked resolved.
    The student does not need to get it perfect —
    attempting the fix is enough to proceed.

    URL pattern:
        writing/intervention/<intervention_id>/fix/
    """
    template_name = "content/writing/practice.html"

    def post(self, request, intervention_id, *args, **kwargs):
        from content.models.writing import WritingIntervention

        intervention = get_object_or_404(
            WritingIntervention,
            pk=intervention_id,
            attempt__user=request.user,
        )

        fix_text = request.POST.get("fix_text", "").strip()

        if not fix_text:
            return self._error_response(
                request,
                "Please write your fix before submitting.",
            )

        # Mark as resolved — attempting is enough
        intervention.resolve(fix_text)

        # Check if all interventions for this attempt are resolved
        attempt = intervention.attempt
        all_resolved = not attempt.interventions.filter(
            is_resolved=False
        ).exists()

        result = {
            "resolved":          True,
            "intervention_id":   intervention_id,
            "all_resolved":      all_resolved,
            "feedback": (
                "Good. Keep going."
                if not all_resolved
                else (
                    "All sentences fixed. "
                    "You can now resubmit your full response."
                )
            ),
        }

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(result)

        if all_resolved:
            messages.success(
                request,
                "All sentences fixed. "
                "You can now resubmit your full response."
            )
        else:
            messages.info(
                request,
                "Sentence fixed. Check the remaining highlighted sentences."
            )

        return redirect(
            "content:writing_practice",
            unit_id=attempt.content.unit.id,
            stage_id=attempt.content.stage.id,
        )

    def _error_response(self, request, message):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": message}, status=400)
        messages.error(request, message)
        return redirect("content:writing_hub", unit_id=0)


# ============================================================
# FRAME PARSING HELPER
# ============================================================

def _parse_frame(frame_text):
    """
    Parse an imitate frame into display parts.

    Splits the frame on ___ markers to produce
    a list of alternating text and blank segments.

    Example:
        Input:  "The ___ [subject] walked ___ [adverb]."
        Output: [
            {"type": "text",  "content": "The "},
            {"type": "blank", "content": "[subject]"},
            {"type": "text",  "content": " walked "},
            {"type": "blank", "content": "[adverb]"},
            {"type": "text",  "content": "."},
        ]

    Used by the template to render the frame with
    input fields in place of blanks.
    """
    if not frame_text:
        return [{"type": "text", "content": ""}]

    parts  = []
    # Split on ___ — may have labels in brackets after
    import re
    segments = re.split(r'(___(?:\s*\[[^\]]*\])?)', frame_text)

    for segment in segments:
        if not segment:
            continue
        if segment.startswith("___"):
            # Extract label if present
            label_match = re.search(r'\[([^\]]*)\]', segment)
            label = label_match.group(1) if label_match else ""
            parts.append({
                "type":    "blank",
                "content": label,
            })
        else:
            parts.append({
                "type":    "text",
                "content": segment,
            })

    return parts


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