# content/views/punctuation/practice.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from content.models.punctuation import (
    PunctuationQuestion,
    PunctuationAttempt,
    PunctuationTestAttempt,   # for mastery check
    ChunkPunctuationFocus,
)
from .core import _chunk_context, get_punctuation_objects


@login_required
def punctuation_practice(request, chunk_id, focus_id):
    """
    Punctuation Practice View
    - Chunk + focus scoped
    - Safe if no questions
    - Redirect logic:
        * If all correct → go to Test
        * If any incorrect → go to Teach
        * If none attempted → stay on Practice
    """

    # 1. Resolve core objects
    chunk, focus = get_punctuation_objects(chunk_id, focus_id)

    # 2. Fetch questions
    questions = PunctuationQuestion.objects.filter(
        focus=focus
    ).order_by("id")

    if not questions.exists():
        messages.error(
            request,
            "This punctuation focus has no practice questions yet."
        )
        return redirect(
            "content:chunk_punctuation",
            chunk_id=chunk.id
        )

    # 3. Normalize (prepare per-question state)
    for q in questions:
        q.user_answer = None
        q.is_correct = None
        q.feedback_ready = False

    submitted = False

    # 4. Handle POST
    if request.method == "POST":
        submitted = True
        any_answered = False
        all_correct = True  # assume true until proven otherwise

        for q in questions:
            user_answer = request.POST.get(f"q{q.id}", "").strip()
            if not user_answer:
                all_correct = False
                continue

            any_answered = True

            is_correct = (
                user_answer.lower()
                == q.correct_answer.strip().lower()
            )

            if not is_correct:
                all_correct = False

            PunctuationAttempt.objects.update_or_create(
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

        # Branching logic
        if not any_answered:
            messages.warning(
                request,
                "Please attempt at least one question."
            )
        elif all_correct:
            # Mark practice complete → unlock test
            PunctuationTestAttempt.objects.get_or_create(
                student=request.user,
                focus=focus,
                defaults={
                    "score_percent": 0,
                    "correct_answers": 0,
                    "total_questions": questions.count(),
                    "questions_snapshot": {},
                }
            )
            messages.success(
                request,
                "Excellent! All practice answers correct. Proceed to the Final Test."
            )
            return redirect(
                "content:punctuation:test",
                chunk_id=chunk.id,
                focus_id=focus.id
            )
        else:
            messages.warning(
                request,
                "Some answers were incorrect. Review the theory before retrying."
            )
            return redirect(
                "content:punctuation:teach",
                chunk_id=chunk.id,
                focus_id=focus.id
            )

    # 5. Context
    context = _chunk_context(chunk, focus=focus, mark=focus.mark)
    context.update({
        "questions": questions,
        "submitted": submitted,
    })

    return render(
        request,
        "content/punctuation/practice.html",
        context
    )