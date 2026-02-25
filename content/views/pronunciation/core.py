# content/views/pronunciation/core.py

from django.shortcuts import get_object_or_404
from content.models.core import LessonChunk
from content.models.pronunciation import PronunciationFocus


def _chunk_context(chunk, focus=None):
    """
    Standardized context for all pronunciation templates.
    """
    context = {
        "chunk": chunk,
        "lesson": chunk.lesson,
        "unit": chunk.lesson.unit,
        "textbook": chunk.lesson.unit.textbook,
    }

    if focus is not None:
        context["focus"] = focus

    return context


def get_pronunciation_objects(chunk_id, focus_id=None):
    """
    Fetch chunk and optionally focus.
    Uses select_related to pull hierarchy in one query.
    """
    if focus_id:
        focus = get_object_or_404(
            PronunciationFocus.objects.select_related(
                "chunk__lesson__unit__textbook"
            ),
            id=focus_id,
            chunk_id=chunk_id,
        )
        return focus.chunk, focus

    chunk = get_object_or_404(
        LessonChunk.objects.select_related("lesson__unit__textbook"),
        id=chunk_id,
    )
    return chunk, None