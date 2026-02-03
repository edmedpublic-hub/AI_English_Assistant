# content/views/vocabulary/hub.py
from django.shortcuts import render
from .core import get_vocab_context, _vocab_base_context

def chunk_vocabulary(request, chunk_id):
    """
    The main landing page for a chunk's vocabulary section.
    """
    chunk, lesson = get_vocab_context(chunk_id)
    context = _vocab_base_context(chunk, lesson)
    
    # Get all vocabulary items related to this chunk
    context["vocabulary_items"] = chunk.vocab_items.all() 
    
    return render(request, "content/vocab/chunk_vocabulary.html", context)