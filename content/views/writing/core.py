# content/views/writing/core.py

from django.shortcuts import get_object_or_404

from content.models.core import LessonChunk, Unit
from content.models.writing import ChunkWritingFocus, UnitWritingTask


def _chunk_context(chunk_or_id, focus=None, task=None):
    """
    Standardized context for all writing views.

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

    if task is not None:
        context["task"] = task

    return context


def get_writing_objects(chunk_id, focus_id=None, unit_id=None, task_id=None):
    """
    Fetch and validate writing navigation objects.

    Always returns:
    - chunk (LessonChunk)
    - focus (ChunkWritingFocus or None)
    - unit (Unit or None)
    - task (UnitWritingTask or None)
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
            ChunkWritingFocus.objects.select_related("chunk"),
            id=focus_id,
            chunk=chunk,
        )

    unit = None
    task = None
    if unit_id is not None:
        unit = get_object_or_404(Unit.objects.select_related("textbook"), id=unit_id)

    if task_id is not None and unit is not None:
        task = get_object_or_404(
            UnitWritingTask.objects.select_related("unit"),
            id=task_id,
            unit=unit,
        )

    return chunk, focus, unit, task