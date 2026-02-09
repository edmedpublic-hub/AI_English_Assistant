# content/views/punctuation/core.py

from django.shortcuts import get_object_or_404
from content.models.core import LessonChunk
from content.models.punctuation import ChunkPunctuationFocus


def _chunk_context(chunk_or_id, focus=None, mark=None):
    """
    Standardized context for all punctuation views.

    Accepts either:
    - LessonChunk instance
    - LessonChunk ID (int)

    Guarantees that 'chunk' is always a resolved object.
    """

    # Resolve chunk safely
    if isinstance(chunk_or_id, (int, str)):
        chunk = get_object_or_404(
            LessonChunk.objects.select_related(
                "lesson__unit__textbook"
            ),
            id=chunk_or_id,
        )
    else:
        chunk = chunk_or_id

    context = {
        "chunk": chunk,
        "lesson": chunk.lesson,
        "unit": chunk.lesson.unit,
        "textbook": chunk.lesson.unit.textbook,
    }

    if focus is not None:
        context["focus"] = focus

    if mark is not None:
        context["mark"] = mark

    return context


def get_punctuation_objects(chunk_id, focus_id=None):
    """
    Fetch and validate punctuation navigation objects.

    Always returns:
    - chunk (LessonChunk)
    - focus (ChunkPunctuationFocus or None)
    """

    chunk = get_object_or_404(
        LessonChunk.objects.select_related(
            "lesson__unit__textbook"
        ),
        id=chunk_id,
    )

    focus = None
    if focus_id is not None:
        focus = get_object_or_404(
            ChunkPunctuationFocus.objects.select_related("mark"),
            id=focus_id,
            chunk=chunk,
        )

    return chunk, focus