# content/views/grammar/practice.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from content.models.grammar import (
    GrammarQuestion,
    GrammarAttempt,
    GrammarPracticeAttempt,
)
from .core import _chunk_context, get_grammar_objects


@login_required
def grammar_practice(request, chunk_id, focus_id):
    """
    Grammar Practice View
    - Chunk + focus scoped
    - Safe if no questions
    - Test unlocked if ≥1 correct answer
    """

    # 1. Resolve core objects
    chunk, focus = get_grammar_objects(chunk_id, focus_id)
    concept = focus.concept

    # 2. Fetch questions
    questions = GrammarQuestion.objects.filter(
        focus=focus
    ).order_by("id")

    if not questions.exists():
        messages.error(
            request,
            "This grammar focus has no practice questions yet."
        )
        return redirect(
            "content:chunk_grammar",
            chunk_id=chunk.id
        )

    # 3. Normalize (DO NOT touch parsed_options)
    for q in questions:
        q.user_answer = None
        q.is_correct = None
        q.feedback_ready = False

    submitted = False

    # 4. Handle POST
    if request.method == "POST":
        submitted = True
        any_correct = False
        any_answered = False

        for q in questions:
            user_answer = request.POST.get(f"q{q.id}", "").strip()
            if not user_answer:
                continue

            any_answered = True

            is_correct = (
                user_answer.lower()
                == q.correct_answer.strip().lower()
            )

            if is_correct:
                any_correct = True

            GrammarAttempt.objects.update_or_create(
                student=request.user,
                question=q,
                defaults={
                    "selected_answer": user_answer,
                    "is_correct": is_correct,
                }
            )

            q.user_answer = user_answer
            q.is_correct = is_correct
            q.feedback_ready = True

        if not any_answered:
            messages.warning(
                request,
                "Please attempt at least one question."
            )
        elif any_correct:
            GrammarPracticeAttempt.objects.get_or_create(
                student=request.user,
                focus=focus,
            )
            messages.success(
                request,
                "Practice complete! The Final Test is now unlocked."
            )
        else:
            messages.warning(
                request,
                "You must answer at least one question correctly to unlock the Final Test."
            )

    # 5. Context
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
