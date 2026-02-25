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


@login_required
def pronunciation_practice(request, chunk_id, focus_id):
    """
    Pronunciation Practice View:

    - Student uploads a recording
    - Teacher scores it via admin (ai_score field)
    - System checks score >= 90 and updates mastery
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
    if request.method == "POST":
        recording = request.FILES.get("recording")

        if not recording:
            messages.error(request, "Please upload a recording before submitting.")
        else:
            PronunciationAttempt.objects.create(
                user=request.user,
                focus=focus,
                attempt_number=attempt_number,
                cycle_number=cycle_number,
                recording=recording,
                attempt_type='practice',
            )

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
    })

    return render(request, "content/pronunciation/practice.html", context)