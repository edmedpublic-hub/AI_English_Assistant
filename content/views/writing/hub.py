# content/views/writing/hub.py

from django.shortcuts import render
from .core import _chunk_context
from content.models.writing import (
    ChunkWritingFocus,
    WritingPracticeAttempt,
    WritingTestAttempt,
)


def chunk_writing_view(request, chunk_id):
    """
    Writing Hub:
    Lists all writing focuses for a specific chunk and
    computes progress state per focus efficiently.
    """

    context = _chunk_context(chunk_id, focus=None)
    chunk = context["chunk"]

    # 1. Fetch all writing focuses (Query 1)
    focuses = list(
        ChunkWritingFocus.objects
        .filter(chunk=chunk)
        .select_related("concept")  # optional, if concept-like field exists
        .order_by("id")  # deterministic order
    )

    # Default: no progress (safe for anonymous users)
    mastered_focus_ids = set()
    practiced_focus_ids = set()

    if request.user.is_authenticated:
        # 2. Fetch Mastered IDs in bulk (Query 2)
        mastered_focus_ids = set(
            WritingTestAttempt.objects.filter(
                student=request.user,
                focus__in=focuses,
                overall_score=100,
            ).values_list("focus_id", flat=True).distinct()
        )

        # 3. Fetch Practiced IDs in bulk (Query 3)
        practiced_focus_ids = set(
            WritingPracticeAttempt.objects.filter(
                student=request.user,
                focus__in=focuses,
            ).values_list("focus_id", flat=True)
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
        "content/chunks/chunk_writing.html",
        context,
    )