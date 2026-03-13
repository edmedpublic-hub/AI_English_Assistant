# content/views/punctuation/teach.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from content.models.punctuation import (
    ChunkPunctuationFocusRule,
    ChunkPunctuationFocus,
    PunctuationTestAttempt,
)
from .core import _chunk_context, get_punctuation_objects


@login_required
def teach_punctuation_view(request, chunk_id, focus_id):
    chunk, focus = get_punctuation_objects(chunk_id, focus_id)

    # Sequential focus lock
    previous_focus = (
        ChunkPunctuationFocus.objects
        .filter(chunk=chunk, sequence_order__lt=focus.sequence_order)
        .order_by("-sequence_order")
        .first()
    )

    if previous_focus and not PunctuationTestAttempt.objects.filter(
        user=request.user,
        focus=previous_focus,
        is_mastered=True,  # FIXED: was is_mastery
    ).exists():
        messages.warning(
            request,
            "Mastery Lock: Complete previous punctuation focus before continuing."
        )
        return redirect("content:chunk_punctuation", chunk_id=chunk.id)

    # Load all rules linked to this focus
    focus_rules = (
        ChunkPunctuationFocusRule.objects
        .filter(focus=focus)
        .select_related("rule")
        .prefetch_related("rule__examples")
        .order_by("order")
    )

    rules = [fr.rule for fr in focus_rules]

    context = _chunk_context(chunk, focus=focus)
    context.update({
        "rules": rules,
        "focus_rules": focus_rules,
    })

    return render(request, "content/punctuation/teach.html", context)