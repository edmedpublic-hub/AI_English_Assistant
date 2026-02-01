from django.shortcuts import get_object_or_404
from ...models import LessonChunk, ChunkGrammarFocus

# content/views/grammar/core.py

from django.shortcuts import get_object_or_404
from content.models.core import LessonChunk

def _chunk_context(chunk_or_id, focus=None, concept=None):
    """
    Standardized context for all grammar views.
    Handles both chunk objects and integer IDs to prevent 'int object' errors.
    """
    # Check if we were passed an ID or an Object
    if isinstance(chunk_or_id, (int, str)):
        chunk = get_object_or_404(LessonChunk, id=chunk_or_id)
    else:
        chunk = chunk_or_id

    # Now we are guaranteed that 'chunk' is an object
    context = {
        "chunk": chunk,
        "lesson": chunk.lesson,
        "unit": chunk.lesson.unit,
        "textbook": chunk.lesson.unit.textbook,
    }

    if focus:
        context["focus"] = focus
    if concept:
        context["concept"] = concept
        
    return context

def get_grammar_objects(chunk_id, focus_id=None):
    """
    Helper to fetch the chunk and focus consistently.
    """
    chunk = get_object_or_404(
        LessonChunk.objects.select_related("lesson__unit__textbook"), 
        id=chunk_id
    )
    focus = None
    if focus_id:
        focus = get_object_or_404(
            ChunkGrammarFocus.objects.select_related("concept"),
            id=focus_id,
            chunk=chunk,
        )
    return chunk, focus