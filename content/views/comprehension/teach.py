# content/views/comprehension/teach.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.exceptions import PermissionDenied

from .core import get_comprehension_objects, build_chunk_context
from content.models.comprehension import ChunkComprehensionFocus
from content.services.comprehension.comprehension_mastery import is_focus_mastered


@login_required
def comprehension_teach_view(request, chunk_id, focus_id):
    """
    Comprehension Teach View (HTML LMS)

    Responsibilities:
    - Resolve chunk + focus safely
    - Enforce sequential mastery lock
    - Provide stable LMS template context
    - Prepare navigation toward practice/test
    """

    # --- 1. Safe object resolution ---
    chunk, focus = get_comprehension_objects(chunk_id, focus_id)

    # --- 2. Sequential mastery enforcement ---
    previous_focus = (
        ChunkComprehensionFocus.objects
        .filter(chunk=chunk, sequence_order__lt=focus.sequence_order)
        .order_by("-sequence_order")
        .first()
    )

    if previous_focus and not is_focus_mastered(request.user, previous_focus):
        raise PermissionDenied("You must master the previous focus first.")

    # --- 3. Base LMS context ---
    context = build_chunk_context(chunk)

    # --- 4. Page-specific context ---
    context.update({
        "focus": focus,
        "is_mastered": is_focus_mastered(request.user, focus),
    })

    # --- 5. Render LMS teaching template ---
    return render(
        request,
        "content/comprehension/teach.html",
        context,
    )
