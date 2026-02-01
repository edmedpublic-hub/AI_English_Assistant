# content/views/grammar/teach.py

from django.shortcuts import render
from .core import _chunk_context, get_grammar_objects

def grammar_teach(request, chunk_id, focus_id):
    """
    English-immersion teaching view. 
    Focuses on the logical link between Rules and their Examples 
    to encourage cognitive growth without over-reliance on translation.
    """
    # 1. Fetch the chunk and the specific focus (e.g., 'Kinds of Nouns')
    # get_grammar_objects handles the 404 logic for us.
    chunk, focus = get_grammar_objects(chunk_id, focus_id)
    concept = focus.concept

    # 2. Optimized Query: Fetch rules and prefetch their related examples.
    # This prevents the 'N+1' database problem when looping in the template.
    rules = concept.rules.all().prefetch_related('examples').order_by("id")

    # 3. Build context using the centralized helper.
    # We pass 'focus' and 'concept' so the breadcrumbs and headers are accurate.
    context = _chunk_context(chunk_id, focus, concept)
    
    # 4. Inject teaching-specific data.
    context.update({
        "rules": rules,
        "focus_title": focus.focus_title,
        "focus_description": focus.focus_description,
    })

    # 5. Render the high-immersion teaching template.
    return render(request, "content/grammar/teach.html", context)