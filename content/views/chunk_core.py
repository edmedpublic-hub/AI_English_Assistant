# PATH: content/views/chunk_core.py
# ACTION: Replace the entire existing file with this content.
#
# CHANGES FROM ORIGINAL:
#   - chunk_hub now calls get_chunk_mastery() and passes domain
#     statuses into template context so the hub can show per-domain
#     progress badges on each card.
#   - build_chunk_context helper unchanged.
#   - Sequential mastery check unchanged.

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

from content.models.core import LessonChunk
from content.services.chunk_mastery import get_chunk_mastery


def build_chunk_context(chunk_id):
    """
    Standard context builder for any chunk-related page.
    """
    chunk    = get_object_or_404(LessonChunk, id=chunk_id)
    lesson   = chunk.lesson
    unit     = lesson.unit
    textbook = unit.textbook

    return {
        'chunk':    chunk,
        'lesson':   lesson,
        'unit':     unit,
        'textbook': textbook,
    }


@login_required
@require_GET
def chunk_hub(request, chunk_id):
    """
    Chunk hub with per-domain mastery status badges.
    """
    chunk = get_object_or_404(LessonChunk, id=chunk_id)

    # Sequential mastery check
    prev_chunk = LessonChunk.objects.filter(
        lesson=chunk.lesson,
        order__lt=chunk.order,
    ).order_by('-order').first()

    if prev_chunk and not prev_chunk.is_mastered_by(request.user):
        messages.warning(
            request,
            f"Mastery Lock: Please complete Chunk {prev_chunk.order} "
            f"at 100% before starting Chunk {chunk.order}.",
        )
        return redirect('content:lesson_detail', pk=chunk.lesson.pk)

    # Base context
    context = build_chunk_context(chunk_id)
    context['chunk_mastered'] = chunk.is_mastered_by(request.user)

    # Per-domain mastery status
    context['domain_status'] = get_chunk_mastery(request.user, chunk)

    return render(request, "content/chunks/chunk_hub.html", context)