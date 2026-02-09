from django.shortcuts import render
from .core import _chunk_context
from content.models.grammar import (
    ChunkGrammarFocus,
    GrammarPracticeAttempt,
    GrammarTestAttempt,
)

def chunk_grammar_view(request, chunk_id):
    """
    Grammar Hub:
    Lists all grammar focuses for a specific chunk and
    computes progress state per focus efficiently.
    """
    context = _chunk_context(chunk_id, focus=None)
    chunk = context["chunk"]

    # 1. Fetch all grammar focuses (Query 1)
    focuses = list(
        ChunkGrammarFocus.objects
        .filter(chunk=chunk)
        .select_related("concept")
        .order_by("id")  # deterministic order
    )

    # Default: no progress (safe for anonymous users)
    mastered_focus_ids = set()
    practiced_focus_ids = set()

    if request.user.is_authenticated:
        # 2. Fetch Mastered IDs in bulk (Query 2)
        mastered_focus_ids = set(
            GrammarTestAttempt.objects.filter(
                student=request.user,
                focus__in=focuses,
                score_percent=100,
            ).values_list("focus_id", flat=True).distinct()
        )

        # 3. Fetch Practiced IDs in bulk (Query 3)
        practiced_focus_ids = set(
            GrammarPracticeAttempt.objects.filter(
                student=request.user,
                focus__in=focuses,
            ).values_list("focus_id", flat=True)
        )

    # Attach progress state (Python-side logic, no DB hits)
    for focus in focuses:
        focus.is_mastered = focus.id in mastered_focus_ids
        focus.practice_attempted = focus.id in practiced_focus_ids

        if focus.is_mastered:
            focus.progress_state = "mastered"
        elif focus.practice_attempted:
            focus.progress_state = "in_progress"
        else:
            focus.progress_state = "not_started"

    # --- Summary Metrics ---
    total_focuses = len(focuses)
    mastered_count = len(mastered_focus_ids)

    context.update({
        "focuses": focuses,
        "total_focuses": total_focuses,
        "mastered_count": mastered_count,
        "mastery_percent": int((mastered_count / total_focuses) * 100) if total_focuses > 0 else 0,
    })

    return render(
        request,
        "content/chunks/chunk_grammar.html",
        context,
    )
