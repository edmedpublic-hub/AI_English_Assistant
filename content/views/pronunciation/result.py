# content/views/pronunciation/result.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .core import _chunk_context, get_pronunciation_objects
from content.models.pronunciation import (
    PronunciationFocus,
    PronunciationAttempt,
    PronunciationMastery,
)


@login_required
def pronunciation_result(request, chunk_id, focus_id):
    """
    Pronunciation Result View:
    Shows attempt history and teacher feedback for a focus.
    """
    chunk, focus = get_pronunciation_objects(chunk_id, focus_id)

    # Get mastery record
    try:
        mastery = PronunciationMastery.objects.get(
            user=request.user,
            focus=focus,
        )
    except PronunciationMastery.DoesNotExist:
        mastery = None

    # Get all attempts
    attempts = PronunciationAttempt.objects.filter(
        user=request.user,
        focus=focus,
    ).order_by("-created_at")

    if not attempts.exists():
        return redirect(
            "content:pronunciation:practice",
            chunk_id=chunk.id,
            focus_id=focus.id,
        )

    latest = attempts.first()

    # Group by cycle
    attempts_by_cycle = {}
    for attempt in attempts:
        if attempt.cycle_number not in attempts_by_cycle:
            attempts_by_cycle[attempt.cycle_number] = []
        attempts_by_cycle[attempt.cycle_number].append(attempt)

    # Next focus for navigation
    next_focus = (
        PronunciationFocus.objects
        .filter(chunk=chunk, sequence_order=focus.sequence_order + 1)
        .first()
    )

    context = _chunk_context(chunk, focus=focus)
    context.update({
        "mastery": mastery,
        "is_mastered": mastery.is_mastered if mastery else False,
        "best_score": mastery.best_score if mastery else None,
        "last_score": mastery.last_score if mastery else None,
        "total_attempts": mastery.total_attempts if mastery else 0,
        "latest_attempt": latest,
        "attempts": attempts,
        "attempts_by_cycle": attempts_by_cycle,
        "next_focus": next_focus,
        "pending_review": latest.ai_score is None,
    })

    return render(request, "content/pronunciation/result.html", context)