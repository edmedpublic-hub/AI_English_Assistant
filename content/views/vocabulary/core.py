from django.shortcuts import get_object_or_404
# Ensure these import paths match your modular models structure
from content.models.core import LessonChunk 

def get_vocab_context(chunk_id):
    """
    Centralized helper to fetch the LessonChunk and its hierarchy.
    Used by practice, testing, and hub views to ensure consistent object fetching.
    """
    chunk = get_object_or_404(
        LessonChunk.objects.select_related(
            "lesson__unit__textbook"
        ), 
        id=chunk_id
    )
    lesson = chunk.lesson
    
    # Return both for flexibility in the calling view
    return chunk, lesson

def _vocab_base_context(chunk, lesson):
    """
    Standardizes the context dictionary for vocabulary templates.
    """
    return {
        "chunk": chunk,
        "lesson": lesson,
        "unit": lesson.unit,
        "textbook": lesson.unit.textbook,
    }