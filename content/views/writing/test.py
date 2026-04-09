# content/views/writing/test.py
#
# Handles the Produce phase — the Test phase of each stage.
# The student writes independently with no frame.
# This is the mastery gate — pass here = stage complete.
#
# URL patterns expected:
#   writing/unit/<unit_id>/stage/<stage_id>/test/        → WritingTestView (GET)
#   writing/unit/<unit_id>/stage/<stage_id>/test/        → WritingTestSubmitView (POST)
#   writing/unit/<unit_id>/stage/<stage_id>/test/result/ → WritingTestResultView (GET)
#
# What GET does:
#   1. Loads the stage content
#   2. Checks stage is not locked
#   3. Checks cooldown — blocks if in cooldown period
#   4. Builds context including produce prompt,
#      previous attempts, and cooldown information
#   5. Renders the produce phase template
#
# What POST does:
#   1. Validates the student's response
#   2. Checks cooldown has expired
#   3. Routes to correct evaluator based on stage eval_method:
#      - Automatic → evaluate_automatic → instant result
#      - Keyword   → evaluate_automatic → instant result
#      - Teacher   → save as pending → teacher reviews in admin
#      - AI+Teacher→ evaluate_with_ai → save result →
#                    teacher can override
#   4. For paragraph stages → sentence-level intervention detection
#   5. On pass → grant mastery (automatic/keyword stages only)
#   6. On fail → set cooldown + generate cooldown task
#   7. Redirects to result page

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
    WritingStageMastery,
    PHASE_PRODUCE,
    PHASE_DISSECT,
    PHASE_IMITATE,
    EVAL_AUTOMATIC,
    EVAL_KEYWORD,
    EVAL_TEACHER,
    EVAL_AI_TEACHER,
    STATUS_PENDING,
    STATUS_PASSED,
    STATUS_FAILED,
    STATUS_COOLDOWN,
    STATUS_APPROVED,
)
from .core import (
    get_current_academic_year,
    get_stage_status,
    get_cooldown_info,
    get_next_attempt_number,
    build_stage_context,
    evaluate_automatic,
    detect_sentence_interventions,
    generate_cooldown_task,
    grant_mastery,
    evaluate_with_ai,
    COOLDOWN_HOURS,
)


class WritingTestView(LoginRequiredMixin, TemplateView):
    """
    GET — renders the Produce phase for a stage.
    Shows the produce prompt and instructions.
    Student writes independently — no frame given.
    Blocked if student is in cooldown.
    """
    template_name = "content/writing/test.html"

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

        # Check cooldown
        cooldown_info = get_cooldown_info(
            request.user,
            self.content,
            self.academic_year,
        )
        if cooldown_info["is_in_cooldown"]:
            # Do not block — show the cooldown screen
            # with the directed task
            pass

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

        # Previous produce attempts
        previous_attempts = (
            WritingAttempt.objects
            .filter(
                user=user,
                content=self.content,
                academic_year=self.academic_year,
                phase=PHASE_PRODUCE,
            )
            .order_by("-created_at")
        )

        latest_produce = previous_attempts.first()

        # Has the student already passed produce?
        produce_passed = previous_attempts.filter(
            status__in=(STATUS_PASSED, STATUS_APPROVED),
        ).exists()

        # Cooldown information
        cooldown_info = get_cooldown_info(
            user,
            self.content,
            self.academic_year,
        )

        # Cooldown task from latest failed attempt
        cooldown_task = ""
        if cooldown_info["is_in_cooldown"] and latest_produce:
            cooldown_task = latest_produce.cooldown_task

        # Cooldown remaining display
        cooldown_remaining = None
        if cooldown_info["is_in_cooldown"] and latest_produce:
            remaining = latest_produce.cooldown_remaining()
            if remaining:
                total_seconds = int(remaining.total_seconds())
                hours         = total_seconds // 3600
                minutes       = (total_seconds % 3600) // 60
                cooldown_remaining = {
                    "hours":   hours,
                    "minutes": minutes,
                    "ends_at": cooldown_info["ends_at"],
                }

        # Interventions from latest failed attempt
        latest_interventions = []
        if (
            latest_produce
            and latest_produce.status == STATUS_FAILED
            and not cooldown_info["is_in_cooldown"]
        ):
            latest_interventions = list(
                latest_produce.interventions
                .filter(is_resolved=False)
                .order_by("id")
            )

        # Min word count for display
        min_words = self.content.get_min_words()

        # Required keywords for display
        required_keywords = self.content.get_required_keywords_list()

        context.update({
            "previous_attempts":   previous_attempts,
            "latest_produce":      latest_produce,
            "produce_passed":      produce_passed,
            "attempt_count":       previous_attempts.count(),
            "latest_interventions": latest_interventions,

            # Cooldown
            "is_in_cooldown":      cooldown_info["is_in_cooldown"],
            "cooldown_task":       cooldown_task,
            "cooldown_remaining":  cooldown_remaining,

            # Writing guidance
            "min_words":           min_words,
            "required_keywords":   required_keywords,

            # Eval method — used by template to show
            # correct expectations to student
            "eval_method":         self.content.stage.eval_method,
            "is_auto_evaluated":   self.content.stage.eval_method in (
                EVAL_AUTOMATIC, EVAL_KEYWORD
            ),
            "is_teacher_evaluated": self.content.stage.eval_method in (
                EVAL_TEACHER, EVAL_AI_TEACHER
            ),

            # Active phase
            "active_phase":        PHASE_PRODUCE,

            # Phase navigation
            "dissect_available":   True,
            "imitate_available":   True,
            "dissect_passed":      stage_ctx.get("phase_dissect_done", False),
            "imitate_passed":      stage_ctx.get("phase_imitate_done", False),
        })

        return context


class WritingTestSubmitView(LoginRequiredMixin, TemplateView):
    """
    POST — receives the student's produce response.
    Routes to correct evaluator based on eval_method.
    Handles cooldown, mastery grant, and interventions.
    """
    template_name = "content/writing/test.html"

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
        stage_status = get_stage_status(
            request.user, content, academic_year
        )
        if stage_status == "locked":
            return self._error_response(
                request,
                "This stage is not yet available.",
                unit_id,
            )

        # Check cooldown — hard block on submission
        cooldown_info = get_cooldown_info(
            request.user, content, academic_year
        )
        if cooldown_info["is_in_cooldown"]:
            return self._error_response(
                request,
                "You must wait before trying again. "
                "Complete your focus tasks first.",
                unit_id,
                stage_id=stage_id,
            )

        # Get student's response
        response_text = request.POST.get("response_text", "").strip()
        if not response_text:
            return self._error_response(
                request,
                "Please write your response before submitting.",
                unit_id,
                stage_id=stage_id,
            )

        # ── Route to evaluator ────────────────────────────
        eval_method = content.stage.eval_method

        if eval_method in (EVAL_AUTOMATIC, EVAL_KEYWORD):
            return self._handle_automatic(
                request, content, academic_year,
                response_text, unit_id, stage_id,
            )

        elif eval_method == EVAL_TEACHER:
            return self._handle_teacher(
                request, content, academic_year,
                response_text, unit_id, stage_id,
            )

        elif eval_method == EVAL_AI_TEACHER:
            return self._handle_ai_teacher(
                request, content, academic_year,
                response_text, unit_id, stage_id,
            )

        return self._error_response(
            request,
            "Unknown evaluation method.",
            unit_id,
        )

    # ── Automatic / Keyword evaluation ───────────────────

    def _handle_automatic(
        self, request, content, academic_year,
        response_text, unit_id, stage_id,
    ):
        """
        Run automatic checks.
        Run sentence interventions for paragraph stages.
        Pass → grant mastery → redirect to result.
        Fail → set cooldown → redirect to result.
        """
        evaluation = evaluate_automatic(
            response_text, content, PHASE_PRODUCE
        )

        # Sentence interventions for paragraph stages
        interventions_data = []
        if content.stage.number >= 6:
            interventions_data = detect_sentence_interventions(
                response_text,
                content.stage.number,
            )

        has_interventions = len(interventions_data) > 0
        passed = evaluation["passed"] and not has_interventions

        # Record attempt
        attempt_number = get_next_attempt_number(
            request.user, content, academic_year, PHASE_PRODUCE
        )

        attempt = WritingAttempt.objects.create(
            user               = request.user,
            content            = content,
            academic_year      = academic_year,
            phase              = PHASE_PRODUCE,
            attempt_number     = attempt_number,
            response_text      = response_text,
            status             = STATUS_PASSED if passed else STATUS_FAILED,
            auto_score         = evaluation["score"],
            auto_checks        = evaluation["checks"],
            intervention_flags = interventions_data,
            time_spent_seconds = _parse_time_spent(request),
        )

        # Create intervention records
        for iv_data in interventions_data:
            WritingIntervention.objects.create(
                attempt       = attempt,
                sentence_text = iv_data["sentence"],
                issue_label   = iv_data["issue"],
                fix_exercise  = iv_data["fix_exercise"],
            )

        if passed:
            # Grant mastery immediately
            grant_mastery(
                request.user, content, academic_year, attempt
            )
        else:
            # Set cooldown and generate directed task
            cooldown_task = generate_cooldown_task(evaluation, content)
            attempt.set_cooldown(hours=COOLDOWN_HOURS)
            attempt.cooldown_task = cooldown_task
            attempt.save()

        return redirect(
            "content:writing_test_result",
            unit_id=unit_id,
            stage_id=stage_id,
            attempt_id=attempt.id,
        )

    # ── Teacher evaluation ────────────────────────────────

    def _handle_teacher(
        self, request, content, academic_year,
        response_text, unit_id, stage_id,
    ):
        """
        Save submission as pending.
        Teacher reviews in admin and marks approved/revision.
        Student sees a 'submitted — waiting for review' screen.
        No cooldown set here — cooldown is set by teacher
        if they request revision.
        """
        # Run basic structural checks so teacher
        # can see automatic results alongside writing
        evaluation = evaluate_automatic(
            response_text, content, PHASE_PRODUCE
        )

        # Sentence interventions
        interventions_data = []
        if content.stage.number >= 6:
            interventions_data = detect_sentence_interventions(
                response_text,
                content.stage.number,
            )

        attempt_number = get_next_attempt_number(
            request.user, content, academic_year, PHASE_PRODUCE
        )

        attempt = WritingAttempt.objects.create(
            user               = request.user,
            content            = content,
            academic_year      = academic_year,
            phase              = PHASE_PRODUCE,
            attempt_number     = attempt_number,
            response_text      = response_text,
            status             = STATUS_PENDING,
            auto_score         = evaluation["score"],
            auto_checks        = evaluation["checks"],
            intervention_flags = interventions_data,
            time_spent_seconds = _parse_time_spent(request),
        )

        # Create intervention records
        for iv_data in interventions_data:
            WritingIntervention.objects.create(
                attempt       = attempt,
                sentence_text = iv_data["sentence"],
                issue_label   = iv_data["issue"],
                fix_exercise  = iv_data["fix_exercise"],
            )

        return redirect(
            "content:writing_test_result",
            unit_id=unit_id,
            stage_id=stage_id,
            attempt_id=attempt.id,
        )

    # ── AI + Teacher evaluation ───────────────────────────

    def _handle_ai_teacher(
        self, request, content, academic_year,
        response_text, unit_id, stage_id,
    ):
        """
        Call AI evaluator first.
        Save result with AI score and feedback.
        Status stays pending — teacher must review.
        Teacher can approve or override AI verdict.
        Student sees AI feedback immediately but knows
        teacher will also review.
        """
        # Run automatic checks first
        evaluation = evaluate_automatic(
            response_text, content, PHASE_PRODUCE
        )

        # Sentence interventions
        interventions_data = []
        if content.stage.number >= 6:
            interventions_data = detect_sentence_interventions(
                response_text,
                content.stage.number,
            )

        # AI evaluation
        ai_result = evaluate_with_ai(response_text, content)

        attempt_number = get_next_attempt_number(
            request.user, content, academic_year, PHASE_PRODUCE
        )

        attempt = WritingAttempt.objects.create(
            user               = request.user,
            content            = content,
            academic_year      = academic_year,
            phase              = PHASE_PRODUCE,
            attempt_number     = attempt_number,
            response_text      = response_text,
            # Pending — teacher must still approve
            status             = STATUS_PENDING,
            auto_score         = evaluation["score"],
            auto_checks        = evaluation["checks"],
            intervention_flags = interventions_data,
            ai_score           = ai_result["score"],
            ai_feedback        = ai_result["feedback"],
            ai_rubric_scores   = ai_result["rubric_scores"],
            time_spent_seconds = _parse_time_spent(request),
        )

        # Create intervention records
        for iv_data in interventions_data:
            WritingIntervention.objects.create(
                attempt       = attempt,
                sentence_text = iv_data["sentence"],
                issue_label   = iv_data["issue"],
                fix_exercise  = iv_data["fix_exercise"],
            )

        return redirect(
            "content:writing_test_result",
            unit_id=unit_id,
            stage_id=stage_id,
            attempt_id=attempt.id,
        )

    def _error_response(
        self, request, message, unit_id, stage_id=None
    ):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": message}, status=400)
        messages.error(request, message)
        if stage_id:
            return redirect(
                "content:writing_test",
                unit_id=unit_id,
                stage_id=stage_id,
            )
        return redirect("content:writing_hub", unit_id=unit_id)


# ============================================================
# RESULT VIEW
# ============================================================

class WritingTestResultView(LoginRequiredMixin, TemplateView):
    """
    GET — shows the result of a produce attempt.

    Handles four distinct result states:
    1. Passed (automatic/keyword) — congratulations,
       next stage unlocked if available
    2. Failed (automatic/keyword) — cooldown screen
       with directed task and timer
    3. Pending (teacher) — submitted, waiting for review
    4. Pending (AI+Teacher) — AI feedback shown,
       waiting for teacher review

    URL pattern:
        writing/unit/<unit_id>/stage/<stage_id>/test/result/<attempt_id>/
    """
    template_name = "content/writing/test_result.html"

    def get(
        self, request, unit_id, stage_id, attempt_id,
        *args, **kwargs
    ):
        self.unit    = get_object_or_404(Unit, pk=unit_id)
        self.stage   = get_object_or_404(WritingStage, pk=stage_id)
        self.content = get_object_or_404(
            WritingStageContent,
            stage=self.stage,
            unit=self.unit,
        )
        self.attempt = get_object_or_404(
            WritingAttempt,
            pk=attempt_id,
            user=request.user,
            content=self.content,
        )
        self.academic_year = get_current_academic_year()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.attempt
        content = self.content
        user    = self.request.user

        # ── Determine result state ────────────────────────
        is_passed  = attempt.status in (STATUS_PASSED, STATUS_APPROVED)
        is_failed  = attempt.status == STATUS_FAILED
        is_pending = attempt.status == STATUS_PENDING
        is_cooldown = attempt.is_in_cooldown()

        # ── Next stage unlock ─────────────────────────────
        next_content  = None
        next_unlocked = False
        if is_passed:
            next_stage = _get_next_stage_content(content)
            if next_stage:
                next_content  = next_stage
                next_unlocked = True

        # ── Cooldown display ──────────────────────────────
        cooldown_remaining = None
        if is_cooldown:
            remaining = attempt.cooldown_remaining()
            if remaining:
                total_seconds = int(remaining.total_seconds())
                hours         = total_seconds // 3600
                minutes       = (total_seconds % 3600) // 60
                cooldown_remaining = {
                    "hours":        hours,
                    "minutes":      minutes,
                    "ends_at":      attempt.next_attempt_allowed_at,
                    "total_seconds": total_seconds,
                }

        # ── Auto checks display ───────────────────────────
        auto_checks_display = _format_auto_checks(
            attempt.auto_checks
        )

        # ── Interventions ─────────────────────────────────
        interventions = attempt.interventions.all().order_by("id")

        # ── Eval method context ───────────────────────────
        eval_method      = content.stage.eval_method
        is_auto          = eval_method in (EVAL_AUTOMATIC, EVAL_KEYWORD)
        is_teacher_eval  = eval_method == EVAL_TEACHER
        is_ai_teacher    = eval_method == EVAL_AI_TEACHER

        # ── Result message ────────────────────────────────
        result_message = _build_result_message(
            is_passed, is_failed, is_pending,
            is_cooldown, eval_method, attempt,
        )

        context.update({
            # Core
            "unit":           self.unit,
            "stage":          self.stage,
            "content":        content,
            "attempt":        attempt,
            "academic_year":  self.academic_year,

            # Result state
            "is_passed":      is_passed,
            "is_failed":      is_failed,
            "is_pending":     is_pending,
            "is_cooldown":    is_cooldown,

            # Score
            "effective_score": attempt.effective_score(),
            "auto_score":      attempt.auto_score,
            "ai_score":        attempt.ai_score,
            "teacher_score":   attempt.teacher_score,

            # Feedback
            "ai_feedback":      attempt.ai_feedback,
            "teacher_feedback": attempt.teacher_feedback,
            "cooldown_task":    attempt.cooldown_task,
            "result_message":   result_message,

            # Checks and interventions
            "auto_checks_display": auto_checks_display,
            "interventions":       interventions,

            # Cooldown timer
            "cooldown_remaining": cooldown_remaining,

            # Next stage
            "next_content":   next_content,
            "next_unlocked":  next_unlocked,

            # Eval method flags
            "is_auto":         is_auto,
            "is_teacher_eval": is_teacher_eval,
            "is_ai_teacher":   is_ai_teacher,
        })

        return context


# ============================================================
# HELPERS
# ============================================================

def _get_next_stage_content(current_content):
    """
    Return the WritingStageContent for the next stage
    in the same unit, if it exists and is complete.
    """
    from content.models.writing import WritingStageContent
    next_stage_number = current_content.stage.number + 1
    try:
        return WritingStageContent.objects.get(
            unit=current_content.unit,
            stage__number=next_stage_number,
            is_complete=True,
        )
    except WritingStageContent.DoesNotExist:
        return None


def _format_auto_checks(auto_checks):
    """
    Format auto_checks dict into a display-ready list.
    Returns list of dicts with label, passed, and icon.
    """
    if not auto_checks:
        return []

    label_map = {
        "capital_start":             "Starts with a capital letter",
        "full_stop_end":             "Ends with a full stop",
        "min_word_count":            "Meets minimum word count",
        "verb_present":              "Contains a verb",
        "modifier_present":          "Contains a describing word",
        "coordinating_conjunction":  "Uses a joining word (and, but, or…)",
        "subordinating_conjunction": "Uses a relationship word (because, when…)",
        "both_conjunction_types":    "Uses both joining and relationship words",
        "keywords_present":          "Uses required vocabulary words",
    }

    result = []
    for key, value in auto_checks.items():
        if isinstance(value, bool):
            result.append({
                "label":  label_map.get(key, key.replace("_", " ").title()),
                "passed": value,
                "icon":   "✓" if value else "✗",
            })

    return result


def _build_result_message(
    is_passed, is_failed, is_pending,
    is_cooldown, eval_method, attempt,
):
    """
    Build the main result message shown to the student.
    Plain English. Specific to their situation.
    """
    if is_passed:
        return (
            "Well done. You have mastered this stage. "
            "You are ready to move to the next one."
        )

    if is_cooldown:
        return (
            "You did not pass this time. "
            "Complete the tasks below before your next attempt. "
            "You can try again tomorrow."
        )

    if is_pending and eval_method == EVAL_TEACHER:
        return (
            "Your writing has been submitted. "
            "Your teacher will review it and give you feedback. "
            "Check back soon."
        )

    if is_pending and eval_method == EVAL_AI_TEACHER:
        return (
            "Your writing has been evaluated. "
            "Read the feedback below carefully. "
            "Your teacher will also review your work."
        )

    if is_failed:
        return (
            "Not quite there yet. "
            "Read the feedback carefully and try again."
        )

    return "Your response has been recorded."


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