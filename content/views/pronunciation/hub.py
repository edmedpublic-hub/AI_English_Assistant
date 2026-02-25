# content/views/pronunciation/hub.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .core import _chunk_context, get_pronunciation_objects
from content.models.pronunciation import PronunciationFocus, PronunciationMastery


@login_required
def chunk_pronunciation_view(request, chunk_id):
    """
    Pronunciation Hub:
    Lists all pronunciation focuses for a chunk with progress state.
    """
    chunk, _ = get_pronunciation_objects(chunk_id)
    context = _chunk_context(chunk)

    # Fetch all focuses in order
    focuses = list(
        PronunciationFocus.objects
        .filter(chunk=chunk)
        .order_by("sequence_order")
    )

    mastered_focus_ids = set()
    attempted_focus_ids = set()

    if focuses:
        focus_ids = [f.id for f in focuses]

        # Single bulk query for mastery records
        mastery_records = PronunciationMastery.objects.filter(
            user=request.user,
            focus_id__in=focus_ids,
        ).values_list("focus_id", "is_mastered")

        for f_id, is_mastered in mastery_records:
            attempted_focus_ids.add(f_id)
            if is_mastered:
                mastered_focus_ids.add(f_id)

    # Attach progress state
    previous_mastered = True
    for focus in focuses:
        focus.is_mastered = focus.id in mastered_focus_ids
        focus.is_attempted = focus.id in attempted_focus_ids
        focus.is_locked = not previous_mastered

        if focus.is_mastered:
            focus.progress_state = "mastered"
        elif focus.is_attempted:
            focus.progress_state = "in_progress"
        else:
            focus.progress_state = "not_started"

        previous_mastered = focus.is_mastered

    total_focuses = len(focuses)
    mastered_count = len(mastered_focus_ids)

    context.update({
        "focuses": focuses,
        "total_focuses": total_focuses,
        "mastered_count": mastered_count,
        "mastery_percent": int((mastered_count / total_focuses) * 100) if total_focuses > 0 else 0,
    })

    return render(request, "content/chunks/chunk_pronunciation.html", context)