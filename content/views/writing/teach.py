# content/views/writing/teach.py

from django.shortcuts import render, redirect
from django.contrib import messages

from .core import _chunk_context, get_writing_objects


def writing_teach(request, chunk_id, focus_id):
    """
    Writing Teaching View:
    Presents writing prompts and scaffolding in a cognitively progressive way.
    This view is always accessible (no mastery gate).
    """

    # 1. Fetch chunk and focus (hard validation)
    chunk, focus, unit, task = get_writing_objects(chunk_id, focus_id=focus_id)

    if not focus:
        messages.error(request, "This writing focus is not ready yet.")
        return redirect("content:chunk_writing", chunk_id=chunk.id)

    # 2. Fetch prompts with rubric/keywords (N+1 safe)
    prompts = (
        focus.prompts
        .all()
        .prefetch_related("responses")
        .order_by("id")
    )

    if not prompts.exists():
        messages.warning(
            request,
            "Teaching content for this writing focus will be added soon."
        )

    # 3. Base context (FIXED: chunk object, not chunk_id)
    context = _chunk_context(chunk, focus, task)

    # 4. Teaching-specific context
    context.update({
        "prompts": prompts,
        "focus_title": focus.focus_title,
        "focus_description": focus.focus_description,
        "has_prompts": prompts.exists(),
    })

    return render(
        request,
        "content/writing/teach.html",
        context
    )