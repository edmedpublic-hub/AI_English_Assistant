from django.shortcuts import render
from django.views.decorators.http import require_GET
from ..chunk_core import build_chunk_context

@require_GET
def chunk_comprehension_view(request, chunk_id):
    """
    Placeholder hub for the Comprehension section.
    Renders the existing comprehension template with full chunk context.
    """
    # Use the centralized helper to get chunk, lesson, unit, and textbook
    context = build_chunk_context(chunk_id)
    
    # Add any specific comprehension-related context here in the future
    # e.g., context['questions'] = chunk.comprehension_questions.all()

    return render(request, "content/chunks/chunk_comprehension.html", context)