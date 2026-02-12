# content/views/punctuation/core.py

from django.shortcuts import get_object_or_404
from content.models.core import LessonChunk
from content.models.punctuation import ChunkPunctuationFocus

def _chunk_context(chunk, focus=None):
    """
    Standardized context for all punctuation templates.
    Assumes 'chunk' is already a resolved object from get_punctuation_objects.
    """
    context = {
        "chunk": chunk,
        "lesson": chunk.lesson,
        "unit": chunk.lesson.unit,
        "textbook": chunk.lesson.unit.textbook,
    }

    if focus:
        context["focus"] = focus
        context["mark"] = focus.mark  # Automatically provide the mark object

    return context


def get_punctuation_objects(chunk_id, focus_id=None):
    """
    Surgical fetch of chunk and focus. 
    Uses select_related to pull the entire hierarchy in ONE database query.
    """
    
    # We use select_related on the focus if focus_id is provided, 
    # because that usually gives us access to the chunk anyway.
    if focus_id:
        focus = get_object_or_404(
            ChunkPunctuationFocus.objects.select_related(
                "mark", 
                "chunk__lesson__unit__textbook"
            ),
            id=focus_id,
            chunk_id=chunk_id
        )
        return focus.chunk, focus

    # If only chunk_id is provided (e.g., for the Hub view)
    chunk = get_object_or_404(
        LessonChunk.objects.select_related("lesson__unit__textbook"),
        id=chunk_id
    )
    return chunk, None