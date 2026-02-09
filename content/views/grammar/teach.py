from django.shortcuts import render, redirect
from django.contrib import messages

from .core import _chunk_context, get_grammar_objects


def grammar_teach(request, chunk_id, focus_id):
    """
    English-immersion teaching view.
    Presents grammar rules and examples in a cognitively progressive way.
    This view is always accessible (no mastery gate).
    """

    # 1. Fetch chunk and focus (hard validation)
    chunk, focus = get_grammar_objects(chunk_id, focus_id)

    concept = focus.concept
    if not concept:
        messages.error(request, "This grammar focus is not ready yet.")
        return redirect("content:chunk_grammar", chunk_id=chunk.id)

    # 2. Fetch rules with examples (N+1 safe)
    rules = (
        concept.rules
        .all()
        .prefetch_related("examples")
        .order_by("id")
    )

    if not rules.exists():
        messages.warning(
            request,
            "Teaching content for this topic will be added soon."
        )

    # 3. Base context (FIXED: chunk object, not chunk_id)
    context = _chunk_context(chunk, focus, concept)

    # 4. Teaching-specific context
    context.update({
        "rules": rules,
        "focus_title": focus.focus_title,
        "focus_description": focus.focus_description,
        "has_rules": rules.exists(),
    })

    return render(
        request,
        "content/grammar/teach.html",
        context
    )
