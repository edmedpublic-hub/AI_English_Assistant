# content/punctuation/hub.py

from django.shortcuts import render
from .core import _chunk_context
from content.models.punctuation import (
    ChunkPunctuationFocus,
    PunctuationAttempt,
    PunctuationTestAttempt,
)


def chunk_punctuation_view(request, chunk_id):
    """
    Punctuation Hub:
    Lists all punctuation focuses for a specific chunk and
    computes progress state per focus efficiently.
    """
    context = _chunk_context(chunk_id, focus=None)
    chunk = context["chunk"]

    # 1. Fetch all punctuation focuses (Query 1)
    focuses = list(
        ChunkPunctuationFocus.objects
        .filter(chunk=chunk)
        .select_related("mark")
        .order_by("id")  # deterministic order
    )

    # Default: no progress (safe for anonymous users)
    mastered_focus_ids = set()
    practiced_focus_ids = set()

    if request.user.is_authenticated:
        # 2. Fetch Mastered IDs in bulk (Query 2)
        mastered_focus_ids = set(
            PunctuationTestAttempt.objects.filter(
                student=request.user,
                focus__in=focuses,
                score_percent=100,
            ).values_list("focus_id", flat=True).distinct()
        )

        # 3. Fetch Practiced IDs in bulk (Query 3)
        practiced_focus_ids = set(
            PunctuationAttempt.objects.filter(
                student=request.user,
                question__focus__in=focuses,
            ).values_list("question__focus_id", flat=True)
        )

    # Attach progress state (Python-side logic, no DB hits)
    for focus in focuses:
        focus.is_mastered = focus.id in mastered_focus_ids
        focus.practice_attempted = focus.id in practiced_focus_ids

        if focus.is_mastered:
            focus.progress_state = "mastered"
        elif focus.practice_attempted:
            focus.progress_state = "in_progress"
        else:
            focus.progress_state = "not_started"

    # --- Summary Metrics ---
    total_focuses = len(focuses)
    mastered_count = len(mastered_focus_ids)

    context.update({
        "focuses": focuses,
        "total_focuses": total_focuses,
        "mastered_count": mastered_count,
        "mastery_percent": int((mastered_count / total_focuses) * 100) if total_focuses > 0 else 0,
    })

    return render(
        request,
        "content/chunks/chunk_punctuation.html",
        context,
    )