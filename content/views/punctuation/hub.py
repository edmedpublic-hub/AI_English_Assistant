# content/views/punctuation/hub.py

from django.shortcuts import render
from .core import _chunk_context, get_punctuation_objects
from content.models.punctuation import (
    ChunkPunctuationFocus,
    # PunctuationAttempt removed - we now track progress via TestAttempt
    PunctuationTestAttempt,
)

def chunk_punctuation_view(request, chunk_id):
    """
    Punctuation Hub:
    Lists all punctuation focuses for a specific chunk and
    computes progress state per focus efficiently.
    """
    # Use our audited core helper to get the chunk
    chunk, _ = get_punctuation_objects(chunk_id)
    context = _chunk_context(chunk)

    # 1. Fetch all punctuation focuses for this chunk
    focuses = list(
        ChunkPunctuationFocus.objects
        .filter(chunk=chunk)
        .select_related("mark")
        .order_by("sequence_order", "depth_level", "id")
    )

    mastered_focus_ids = set()
    attempted_focus_ids = set()

    if request.user.is_authenticated and focuses:
        focus_ids = [f.id for f in focuses]

        # 2. Fetch all test attempts for these focuses (Query 2)
        # We pull both mastered and non-mastered attempts in one go
        user_attempts = PunctuationTestAttempt.objects.filter(
            student=request.user,
            focus_id__in=focus_ids
        ).values_list("focus_id", "is_mastered")

        for f_id, is_mastered in user_attempts:
            attempted_focus_ids.add(f_id)
            if is_mastered:
                mastered_focus_ids.add(f_id)

    # 3. Attach progress state (Pure Python logic)
    for focus in focuses:
        is_mastered = focus.id in mastered_focus_ids
        is_attempted = focus.id in attempted_focus_ids

        focus.is_mastered = is_mastered
        focus.practice_attempted = is_attempted # Backward compatible naming for templates

        if is_mastered:
            focus.progress_state = "mastered"
        elif is_attempted:
            focus.progress_state = "in_progress"
        else:
            focus.progress_state = "not_started"

    # --- Summary Metrics ---
    total_focuses = len(focuses)
    mastered_count = len(mastered_focus_ids)

    mastery_percent = (
        int((mastered_count / total_focuses) * 100)
        if total_focuses > 0 else 0
    )

    context.update({
        "focuses": focuses,
        "total_focuses": total_focuses,
        "mastered_count": mastered_count,
        "mastery_percent": mastery_percent,
    })

    return render(
        request,
        "content/chunks/chunk_punctuation.html",
        context,
    )