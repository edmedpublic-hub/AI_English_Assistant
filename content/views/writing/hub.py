from django.shortcuts import render
from django.views.decorators.http import require_GET
from ..chunk_core import build_chunk_context

@require_GET
def chunk_writing_view(request, chunk_id):
    """
    Placeholder hub for the English Writing Mastery section.
    Eventually handles Simple -> Compound -> Complex sentence building.
    """
    context = build_chunk_context(chunk_id)
    return render(request, "content/chunks/chunk_writing.html", context)