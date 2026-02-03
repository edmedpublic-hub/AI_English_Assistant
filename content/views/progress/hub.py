from django.shortcuts import render
from django.views.decorators.http import require_GET
from ..chunk_core import build_chunk_context

@require_GET
def chunk_progress_view(request, chunk_id):
    """
    Placeholder for the student's progress dashboard for this specific chunk.
    """
    context = build_chunk_context(chunk_id)
    # Future: Add logic to calculate progress percentages here
    return render(request, "content/chunks/chunk_progress.html", context)