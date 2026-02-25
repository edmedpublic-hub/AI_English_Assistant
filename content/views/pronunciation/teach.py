# content/views/pronunciation/teach.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .core import _chunk_context, get_pronunciation_objects
from content.models.pronunciation import PronunciationFocus, PronunciationMastery


@login_required
def pronunciation_teach(request, chunk_id, focus_id):
    """
    Pronunciation Teach View:
    Presents phoneme/stress pattern instruction for a specific focus.
    Always accessible — no mastery gate on teaching content.
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

    context = _chunk_context(chunk, focus=focus)
    context.update({
        "is_mastered": is_mastered,
    })

    return render(request, "content/pronunciation/teach.html", context)