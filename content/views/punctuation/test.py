# content/views/punctuation/test.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from content.models.punctuation import (
    PunctuationQuestion,
    PunctuationTestAttempt,
    PunctuationAttempt,
    ChunkPunctuationFocus,

)
from .core import _chunk_context, get_punctuation_objects


@login_required
def punctuation_test(request, chunk_id, focus_id):
    """
    Punctuation Mastery Test View
    - Requires 100% correct for mastery
    - Uses parsed_options for MCQs
    """

    # 1. Resolve core objects
    chunk, focus = get_punctuation_objects(chunk_id, focus_id)

    # 2. Fetch questions
    questions = PunctuationQuestion.objects.filter(
        focus=focus
    ).order_by("id")

    if not questions.exists():
        messages.error(request, "No test questions available for this focus.")
        return redirect("content:chunk_punctuation", chunk_id=chunk.id)

    # 3. Normalize per-question state
    for q in questions:
        q.user_answer = None
        q.is_correct = None
        q.feedback_ready = False
        # ❌ Do not assign q.parsed_options here — it's a property

    submitted = False
    all_correct = True
    correct_count = 0

    # 4. Handle POST
    if request.method == "POST":
        submitted = True

        for q in questions:
            user_answer = request.POST.get(f"q{q.id}", "").strip()
            if not user_answer:
                all_correct = False
                continue

            is_correct = (
                user_answer.lower()
                == q.correct_answer.strip().lower()
            )

            if is_correct:
                correct_count += 1
            else:
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

        # Save test attempt
        PunctuationTestAttempt.objects.update_or_create(
            student=request.user,
            focus=focus,
            defaults={
                "score_percent": int((correct_count / questions.count()) * 100),
                "correct_answers": correct_count,
                "total_questions": questions.count(),
                "questions_snapshot": {
                    q.id: {"answer": q.user_answer, "is_correct": q.is_correct}
                    for q in questions
                },
            }
        )

        if all_correct and correct_count == questions.count():
            messages.success(request, "Mastery achieved! 100% correct.")
            return redirect(
                "content:punctuation:test_result",
                chunk_id=chunk.id,
                focus_id=focus.id
            )
        else:
            messages.warning(
                request,
                "Mastery requires 100% correct. Please review and try again."
            )

    # 5. Context
    context = _chunk_context(chunk, focus=focus, mark=focus.mark)
    context.update({
        "questions": questions,
        "submitted": submitted,
    })

    return render(
        request,
        "content/punctuation/test.html",
        context
    )
    
@login_required
def punctuation_test_result(request, chunk_id, focus_id):
    """
    Show results of punctuation test attempt.
    Requires that a test attempt exists.
    """

    chunk, focus = get_punctuation_objects(chunk_id, focus_id)

    # Get latest test attempt
    attempt = get_object_or_404(
        PunctuationTestAttempt,
        student=request.user,
        focus=focus
    )

    # Collect stats
    score = attempt.score_percent
    correct = attempt.correct_answers
    total = attempt.total_questions
    mistakes = total - correct

    # Collect detailed results (per question attempts)
    results = PunctuationAttempt.objects.filter(
        student=request.user,
        question__focus=focus
    ).select_related("question")

    # Context
    context = _chunk_context(chunk, focus=focus, mark=focus.mark)
    context.update({
        "score": score,
        "correct": correct,
        "total": total,
        "mistakes": mistakes,
        "results": results,
    })

    return render(
        request,
        "content/punctuation/test_result.html",
        context
    )
