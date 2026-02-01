# content/views/grammar/hub.py

from django.shortcuts import render
from .core import _chunk_context, get_grammar_objects
from content.models.grammar import ChunkGrammarFocus, GrammarTestAttempt

def chunk_grammar_view(request, chunk_id):
    """
    The Hub: Lists all grammar focuses for a specific lesson chunk.
    Incorporates Mastery checks to show progress.
    """
    context = _chunk_context(chunk_id, focus=None)
    chunk = context['chunk']

    # Get all focuses and pull the associated concept to avoid extra DB hits
    focuses = ChunkGrammarFocus.objects.filter(chunk=chunk).select_related('concept')

    # Mastery Logic: Check which focuses the student has passed with 100%
    mastered_focus_ids = GrammarTestAttempt.objects.filter(
        student=request.user,
        focus__in=focuses,
        score_percent=100
    ).values_list('focus_id', flat=True).distinct()

    # Attach the mastery status to each focus object for the template
    for focus in focuses:
        focus.is_mastered = focus.id in mastered_focus_ids

    context.update({
        "focuses": focuses,
    })

    return render(request, "content/chunks/chunk_grammar.html", context)


def grammar_teach(request, chunk_id, focus_id):
    """
    Teaching View: Focuses strictly on English rules and examples.
    """
    chunk, focus = get_grammar_objects(chunk_id, focus_id)
    concept = focus.concept

    # Prefetch related examples to ensure fast loading for 300+ students
    rules = concept.rules.all().prefetch_related('examples').order_by("id")

    context = _chunk_context(chunk, focus, concept)
    context.update({
        "rules": rules,
        "focus_title": focus.focus_title,
        "focus_description": focus.focus_description,
    })

    return render(request, "content/grammar/teach.html", context)