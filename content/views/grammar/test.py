from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from content.models.grammar import GrammarQuestion, GrammarTestAttempt
from .core import _chunk_context, get_grammar_objects


@login_required
def grammar_test(request, chunk_id, focus_id):
    """
    Final Grammar Test View:
    - One-shot assessment
    - No immediate feedback
    - Records GrammarTestAttempt
    - Requires 100% for mastery
    """
    chunk, focus = get_grammar_objects(chunk_id, focus_id)
    concept = focus.concept

    # GET: randomized order
    if request.method == "GET":
        questions = GrammarQuestion.objects.filter(
            focus=focus
        ).order_by("?")

        context = _chunk_context(chunk, focus, concept)
        context.update({
            "questions": questions,
        })

        return render(request, "content/grammar/test.html", context)

    # POST: stable order (correctness > randomness)
    questions = GrammarQuestion.objects.filter(
        focus=focus
    ).order_by("id")

    correct_count = 0
    total_questions = questions.count()

    results_list = []
    results_snapshot = {}

    for q in questions:
        user_answer = request.POST.get(f"q{q.id}", "").strip()
        is_correct = (
            user_answer.lower()
            == q.correct_answer.strip().lower()
        )

        if is_correct:
            correct_count += 1

        results_list.append({
            "question": q,
            "user_answer": user_answer,
            "is_correct": is_correct,
        })

        results_snapshot[q.id] = {
            "user_answer": user_answer,
            "is_correct": is_correct,
        }

    score_percent = (
        int((correct_count / total_questions) * 100)
        if total_questions > 0 else 0
    )

    GrammarTestAttempt.objects.create(
        student=request.user,
        focus=focus,
        score_percent=score_percent,
        correct_answers=correct_count,
        total_questions=total_questions,
        questions_snapshot=results_snapshot,
    )

    context = _chunk_context(chunk, focus, concept)
    context.update({
        "score": score_percent,
        "correct": correct_count,
        "correct_neg": -correct_count,  # template utility
        "total": total_questions,
        "results": results_list,
        "submitted": True,
    })

    return render(
        request,
        "content/grammar/test_result.html",
        context
    )
