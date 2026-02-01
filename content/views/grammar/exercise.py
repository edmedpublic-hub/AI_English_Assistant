from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from content.models.grammar import GrammarQuestion, GrammarAttempt
from .core import _chunk_context, get_grammar_objects


@login_required
def grammar_exercise(request, chunk_id, focus_id):
    # Resolve core objects
    chunk, focus = get_grammar_objects(chunk_id, focus_id)
    concept = focus.concept

    # Fetch questions
    questions = GrammarQuestion.objects.filter(
        focus=focus
    ).order_by("id")

    # Normalize options for template consumption
    for q in questions:
        if q.question_type == GrammarQuestion.TYPE_MCQ:
            q.parsed_options = q.get_options_list()
        else:
            q.parsed_options = []

        # Defaults for template
        q.user_answer = None
        q.is_correct = None
        q.feedback_ready = False

    submitted = False

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

            # Record attempt
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

    context = _chunk_context(chunk, focus, concept)
    context.update({
        "questions": questions,
        "submitted": submitted,
    })

    return render(
        request,
        "content/grammar/exercise.html",
        context
    )
