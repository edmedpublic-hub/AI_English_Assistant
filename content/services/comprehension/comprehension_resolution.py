# content/services/comprehension_resolution.py

from typing import Optional, Tuple
from django.shortcuts import get_object_or_404

from content.models.core import LessonChunk
from content.models.comprehension import ChunkComprehensionFocus


# ---------------------------------------------------------
# Chunk Resolution Helpers
# ---------------------------------------------------------

def get_comprehension_objects(
    chunk_id: int,
    focus_id: Optional[int] = None,
) -> Tuple[LessonChunk, Optional[ChunkComprehensionFocus]]:
    """
    Safely resolve comprehension-related objects.

    Returns:
        (chunk, focus) where focus may be None.

    Guarantees:
    - Valid chunk always returned or 404
    - Focus belongs to the same chunk (no cross-chunk leakage)
    """

    chunk = get_object_or_404(LessonChunk, id=chunk_id)

    focus = None
    if focus_id is not None:
        focus = get_object_or_404(
            ChunkComprehensionFocus,
            id=focus_id,
            chunk=chunk,
        )

    return chunk, focus


# ---------------------------------------------------------
# Shared Template Context
# ---------------------------------------------------------

def build_chunk_context(chunk: LessonChunk) -> dict:
    lesson = chunk.lesson
    unit = lesson.unit
    return {
        "chunk": chunk,
        "chunk_id": chunk.id,
        "unit": unit,
        "lesson": lesson,
    }
