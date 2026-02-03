from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from content.models.grammar import GrammarQuestion, GrammarAttempt
from .core import _chunk_context, get_grammar_objects


@login_required
def grammar_practice(request, chunk_id, focus_id):
    """
    Practice View:
    - Renders chunk-scoped grammar questions
    - Parses plain-text MCQ options in the view layer
    - Provides immediate feedback
    - Records GrammarAttempt per question
    """
    # 1. Resolve core objects
    chunk, focus = get_grammar_objects(chunk_id, focus_id)
    concept = focus.concept

    # 2. Fetch questions for this focus
    questions = GrammarQuestion.objects.filter(
        focus=focus
    ).order_by("id")

    # 3. Normalize questions for template consumption
    for q in questions:
        if q.question_type == GrammarQuestion.TYPE_MCQ:
            q.display_options = q.get_options_list()
        else:
            q.display_options = []

        # Template defaults
        q.user_answer = None
        q.is_correct = None
        q.feedback_ready = False

    submitted = False

    # 4. Handle submission
    if request.method == "POST":
        submitted = True

        for q in questions:
            user_answer = request.POST.get(f"q{q.id}", "").strip()

            if not user_answer:
                continue

            is_correct = (
                user_answer.lower()
                == q.correct_answer.strip().lower()
            )

            GrammarAttempt.objects.create(
                student=request.user,
                question=q,
                selected_answer=user_answer,
                is_correct=is_correct,
            )

            # Attach feedback for UI
            q.user_answer = user_answer
            q.is_correct = is_correct
            q.feedback_ready = True

    # 5. Build context
    context = _chunk_context(chunk, focus, concept)
    context.update({
        "questions": questions,
        "submitted": submitted,
    })

    return render(
        request,
        "content/grammar/practice.html",
        context
    )
