# content/views/punctuation/teach.py

from django.shortcuts import render, get_object_or_404
from .core import _chunk_context, get_punctuation_objects
from content.models.punctuation import (
    ChunkPunctuationFocus,
    PunctuationRule,
    PunctuationExample,
)


def teach_punctuation_view(request, chunk_id, focus_id):
    """
    Teach View:
    Displays the teaching content for a specific punctuation focus.
    Includes rules and examples tied to the focus's mark.
    """

    # Resolve chunk + focus safely
    chunk, focus = get_punctuation_objects(chunk_id, focus_id)

    # Fetch rules for this mark (global curriculum layer)
    rules = (
        PunctuationRule.objects
        .filter(mark=focus.mark)
        .prefetch_related("examples")
        .order_by("id")
    )

    # Flatten examples for template convenience
    examples = PunctuationExample.objects.filter(rule__mark=focus.mark).order_by("id")

    # Build context
    context = _chunk_context(chunk, focus=focus, mark=focus.mark)
    context.update({
        "focus": focus,
        "rules": rules,
        "examples": examples,
    })

    return render(
        request,
        "content/punctuation/teach.html",
        context,
    )