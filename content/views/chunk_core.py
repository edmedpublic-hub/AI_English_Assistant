from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_GET
from content.models.core import LessonChunk
from django.contrib.auth.decorators import login_required

def build_chunk_context(chunk_id):
    """
    Refined helper to build the standard context for any chunk-related page.
    """
    chunk = get_object_or_404(LessonChunk, id=chunk_id)
    lesson = chunk.lesson
    unit = lesson.unit
    textbook = unit.textbook

    return {
        'chunk': chunk,
        'lesson': lesson,
        'unit': unit,
        'textbook': textbook,
    }
@login_required
@require_GET
def chunk_hub(request, chunk_id):
    """
    Displays the hub for a single chunk with Mastery Lockout enforcement.
    """
    chunk = get_object_or_404(LessonChunk, id=chunk_id)

    # 1. Sequential Mastery Check
    # Find the previous chunk to see if it is mastered
    prev_chunk = LessonChunk.objects.filter(
        lesson=chunk.lesson, 
        order__lt=chunk.order
    ).order_by('-order').first()

    if prev_chunk and not prev_chunk.is_mastered_by(request.user):
        messages.warning(
            request, 
            f"Mastery Lock: Please complete Chunk {prev_chunk.order} at 100% before starting Chunk {chunk.order}."
        )
        return redirect('content:lesson_detail', pk=chunk.lesson.pk)

    # 2. Build the basic context
    context = build_chunk_context(chunk_id)
    
    # 3. Add mastery status for the template checkmark
    context['chunk_mastered'] = chunk.is_mastered_by(request.user)

    return render(request, "content/chunks/chunk_hub.html", context)