# content/views/pronunciation/practice.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .core import _chunk_context, get_pronunciation_objects
from content.models.pronunciation import (
    PronunciationFocus,
    PronunciationAttempt,
    PronunciationMastery,
)


# ============================================================
# SCORING FUNCTION
# ============================================================
# This is the ONLY function that needs to change when AI scoring
# becomes available. Swap the body of this function with an API
# call to OpenAI Whisper, Azure Speech, or similar service.
#
# Expected return:
#   {
#       'score': int (0-100),
#       'feedback': str,
#   }
#   or None if scoring is not yet available (manual review mode)
# ============================================================

def score_pronunciation(attempt):
    """
    Score a pronunciation attempt.

    Currently returns None — triggers manual review mode.
    When AI scoring is enabled, replace this body with an API call.

    Example future implementation:
        response = openai.audio.transcriptions.create(...)
        score = assess_pronunciation(response)
        return {'score': score, 'feedback': '...'}
    """
    return None


def _update_mastery(user, focus, attempt):
    """
    Update PronunciationMastery record after a scored attempt.
    Called automatically when ai_score is set.
    """
    from django.utils import timezone

    mastery, _ = PronunciationMastery.objects.get_or_create(
        user=user,
        focus=focus,
    )

    mastery.total_attempts += 1
    mastery.last_score = attempt.ai_score
    mastery.last_attempted = timezone.now()

    if attempt.ai_score is not None:
        if mastery.best_score is None or attempt.ai_score > mastery.best_score:
            mastery.best_score = attempt.ai_score

        if attempt.ai_score >= 90 and not mastery.is_mastered:
            mastery.is_mastered = True
            mastery.mastered_at = timezone.now()

    mastery.save()
    return mastery


@login_required
def pronunciation_practice(request, chunk_id, focus_id):
    """
    Pronunciation Practice View:

    - Student uploads a recording
    - score_pronunciation() is called immediately after upload
    - If AI scoring returns None → manual review mode (teacher scores via admin)
    - If AI scoring returns a score → mastery updated automatically
    - 3 attempts max per cycle
    """
    chunk, focus = get_pronunciation_objects(chunk_id, focus_id)

    # Sequential focus lock
    previous_focus = (
        PronunciationFocus.objects
        .filter(chunk=chunk, sequence_order__lt=focus.sequence_order)
        .order_by("-sequence_order")
        .first()
    )

    if previous_focus and not PronunciationMastery.objects.filter(
        user=request.user,
        focus=previous_focus,
        is_mastered=True,
    ).exists():
        messages.warning(
            request,
            "Mastery Lock: Complete the previous pronunciation focus first."
        )
        return redirect("content:chunk_pronunciation", chunk_id=chunk.id)

    # Check if already mastered
    is_mastered = PronunciationMastery.objects.filter(
        user=request.user,
        focus=focus,
        is_mastered=True,
    ).exists()

    if is_mastered:
        messages.success(request, "You have already mastered this focus.")
        return redirect(
            "content:pronunciation:result",
            chunk_id=chunk.id,
            focus_id=focus.id,
        )

    # Get attempt history
    attempts = PronunciationAttempt.objects.filter(
        user=request.user,
        focus=focus,
        attempt_type='practice',
    ).order_by("-created_at")

    # Calculate current cycle and attempt number
    latest = attempts.first()

    if latest:
        attempts_in_cycle = attempts.filter(
            cycle_number=latest.cycle_number
        ).count()

        if attempts_in_cycle >= 3:
            cycle_number = latest.cycle_number + 1
            attempt_number = 1
        else:
            cycle_number = latest.cycle_number
            attempt_number = attempts_in_cycle + 1
    else:
        cycle_number = 1
        attempt_number = 1

    # Handle POST — student submits recording
    scoring_result = None

    if request.method == "POST":
        recording = request.FILES.get("recording")

        if not recording:
            messages.error(request, "Please upload a recording before submitting.")
        else:
            attempt = PronunciationAttempt.objects.create(
                user=request.user,
                focus=focus,
                attempt_number=attempt_number,
                cycle_number=cycle_number,
                recording=recording,
                attempt_type='practice',
            )

            # Try AI scoring immediately
            scoring_result = score_pronunciation(attempt)

            if scoring_result is not None:
                # AI scoring available — update attempt and mastery
                attempt.ai_score = scoring_result['score']
                attempt.ai_feedback = scoring_result.get('feedback', '')
                attempt.save()

                mastery = _update_mastery(request.user, focus, attempt)

                if mastery.is_mastered:
                    messages.success(
                        request,
                        f"Excellent! You scored {attempt.ai_score}% and have mastered this focus!"
                    )
                    return redirect(
                        "content:pronunciation:result",
                        chunk_id=chunk.id,
                        focus_id=focus.id,
                    )
                else:
                    messages.info(
                        request,
                        f"You scored {attempt.ai_score}%. Need 90% to master. "
                        f"Attempt {attempt_number}/3 in cycle {cycle_number}."
                    )
            else:
                # Manual review mode — teacher will score via admin
                messages.success(
                    request,
                    f"Recording submitted (Attempt {attempt_number}/3, Cycle {cycle_number}). "
                    "Your teacher will review and score it shortly."
                )

            return redirect(
                "content:pronunciation:practice",
                chunk_id=chunk.id,
                focus_id=focus.id,
            )

    context = _chunk_context(chunk, focus=focus)
    context.update({
        "attempts": attempts,
        "attempt_number": attempt_number,
        "cycle_number": cycle_number,
        "attempts_remaining": 3 - (attempt_number - 1),
        "is_mastered": is_mastered,
        "ai_scoring_enabled": False,  # Set to True when score_pronunciation() is live
    })

    return render(request, "content/pronunciation/practice.html", context)