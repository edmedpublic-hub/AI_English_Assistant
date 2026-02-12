from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from content.models.punctuation import (
    PunctuationQuestion,
    PunctuationTestAttempt,
)
from .core import _chunk_context, get_punctuation_objects


@login_required
def punctuation_practice(request, chunk_id, focus_id):
    """
    Practice View (Production-safe):

    - Provides immediate feedback.
    - DOES NOT create real mastery attempts.
    - Creates ONLY a lightweight DB marker when practice is cleared.
    - Mastery Test unlock depends on DB truth, not template state.
    """

    # 1. Resolve objects safely
    chunk, focus = get_punctuation_objects(chunk_id, focus_id)

    # 2. Fetch questions
    questions = list(
        PunctuationQuestion.objects
        .filter(focus=focus)
        .order_by("id")
    )

    if not questions:
        messages.error(request, "This focus has no questions yet.")
        return redirect("content:chunk_punctuation", chunk_id=chunk.id)

    # 3. Check if already cleared in DB
    practice_cleared = PunctuationTestAttempt.objects.filter(
        student=request.user,
        focus=focus,
        is_mastered=False,   # lightweight marker only
    ).exists()

    # Runtime state for template
    for q in questions:
        q.user_answer = None
        q.is_correct = None
        q.feedback_ready = False

    submitted = False

    # 4. Handle submission ONLY if not already cleared
    if request.method == "POST" and not practice_cleared:
        submitted = True
        all_correct = True
        answered_count = 0

        for q in questions:
            user_answer = request.POST.get(f"q{q.id}", "").strip()

            if user_answer:
                answered_count += 1
                is_correct = (
                    user_answer.lower()
                    == q.correct_answer.strip().lower()
                )

                if not is_correct:
                    all_correct = False

                q.user_answer = user_answer
                q.is_correct = is_correct
                q.feedback_ready = True
            else:
                all_correct = False

        # Branching logic
        if answered_count == 0:
            messages.warning(request, "Please attempt the questions before submitting.")

        elif all_correct:
            # Create lightweight DB marker (ONLY if not exists)
            PunctuationTestAttempt.objects.get_or_create(
                student=request.user,
                focus=focus,
                defaults={"is_mastered": False},
            )

            messages.success(
                request,
                "Perfect! Practice cleared. You can now take the Mastery Test."
            )

            return redirect(
                "content:punctuation:test",
                chunk_id=chunk.id,
                focus_id=focus.id,
            )

        else:
            messages.error(
                request,
                "Some answers were incorrect. Review the highlights and try again."
            )

    # 5. Context
    context = _chunk_context(chunk, focus=focus)
    context.update({
        "questions": questions,
        "submitted": submitted,
        "practice_cleared": practice_cleared,
    })

    return render(request, "content/punctuation/practice.html", context)
