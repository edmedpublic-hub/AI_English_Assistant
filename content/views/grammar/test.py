# content/views/grammar/test.py

from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from content.models.grammar import (
    GrammarQuestion,
    GrammarTestAttempt,
    GrammarPracticeAttempt,
)
from .core import _chunk_context, get_grammar_objects


@login_required
def grammar_test(request, chunk_id, focus_id):

    # 1. Resolve objects
    chunk, focus = get_grammar_objects(chunk_id, focus_id)
    concept = focus.concept

    # 2. Practice gate
    if not GrammarPracticeAttempt.objects.filter(
        user=request.user, focus=focus
    ).exists():
        messages.warning(
            request,
            "You must complete the Practice session before taking the test.",
        )
        return redirect(
            "content:grammar:practice",  # FIXED
            chunk_id=chunk.id,
            focus_id=focus.id,
        )

    # 3. Permanent mastery lock
    if GrammarTestAttempt.objects.filter(
        user=request.user, focus=focus, is_mastered=True
    ).exists():
        messages.success(request, "You have already mastered this grammar focus.")
        return redirect("content:chunk_grammar", chunk.id)  # FIXED

    # 4. Cycle & attempt tracking
    latest = (
        GrammarTestAttempt.objects.filter(user=request.user, focus=focus)
        .order_by("-cycle_number", "-attempt_number")
        .first()
    )

    if latest:
        attempts_in_cycle = GrammarTestAttempt.objects.filter(
            user=request.user, focus=focus, cycle_number=latest.cycle_number
        ).count()

        if attempts_in_cycle >= 3:
            cycle_number = latest.cycle_number + 1
            attempt_number = 1
        else:
            cycle_number = latest.cycle_number
            attempt_number = attempts_in_cycle + 1
    else:
        cycle_number = 1
        attempt_number = 1

    # 5. Cooldown after failed attempt
    if latest and not latest.is_mastered:
        cooldown = timedelta(minutes=10)
        elapsed = timezone.now() - latest.created_at

        if elapsed < cooldown:
            remaining_seconds = int((cooldown - elapsed).total_seconds())
            minutes_left = (remaining_seconds // 60) + 1
            messages.error(
                request,
                f"Cooldown active. You can retry in {minutes_left} minute(s).",
            )
            return redirect("content:chunk_grammar", chunk.id)  # FIXED

    # 6. Load questions
    questions = GrammarQuestion.objects.filter(focus=focus).order_by("id")
    total_questions = questions.count()

    if total_questions == 0:
        messages.error(request, "This test is not yet available.")
        return redirect("content:chunk_grammar", chunk.id)  # FIXED

    # 7. GET — render test form
    if request.method == "GET":
        context = _chunk_context(chunk, focus, concept)
        context.update({
            "questions": questions,
            "attempt_number": attempt_number,
            "cycle_number": cycle_number,
            "attempts_remaining": 3 - (attempt_number - 1),
            "last_attempt_score": latest.score_percent if latest else None,
        })
        return render(request, "content/grammar/test.html", context)

    # 8. POST — grade submission
    correct_count = 0
    results = []
    snapshot = {}

    for q in questions:
        user_answer = request.POST.get(f"q{q.id}", "").strip()
        is_correct = user_answer.lower() == q.correct_answer.strip().lower()

        if is_correct:
            correct_count += 1

        results.append({
            "question": q,
            "user_answer": user_answer,
            "is_correct": is_correct,
        })

        snapshot[q.id] = {
            "user_answer": user_answer,
            "is_correct": is_correct,
        }

    score_percent = int(
        (correct_count / total_questions) * 100) if total_questions else 0

    # 9. Persist attempt
    attempt = GrammarTestAttempt.objects.create(
        user=request.user,
        focus=focus,
        attempt_number=attempt_number,
        cycle_number=cycle_number,
        score_percent=score_percent,
        correct_answers=correct_count,
        total_questions=total_questions,
        questions_snapshot=snapshot,
    )

    # 10. Feedback messaging
    if attempt.is_mastered:
        messages.success(
            request,
            f"🎉 Perfect! You have mastered this grammar topic! "
            f"(Attempt {attempt_number}/3, Cycle {cycle_number})",
        )
    else:
        attempts_remaining = 3 - attempt_number
        if attempts_remaining > 0:
            messages.warning(
                request,
                f"You scored {score_percent}%. Need 100% to master. "
                f"Attempts remaining in cycle {cycle_number}: {attempts_remaining}",
            )
        else:
            messages.warning(
                request,
                f"You scored {score_percent}%. All 3 attempts used in cycle {cycle_number}. "
                f"A new cycle will start on your next attempt.",
            )

    # 11. Render result
    mistakes = total_questions - correct_count
    context = _chunk_context(chunk, focus, concept)
    context.update({
        "attempt": attempt,
        "score": score_percent,
        "correct": correct_count,
        "total": total_questions,
        "mistakes": mistakes,
        "results": results,
        "attempt_number": attempt_number,
        "cycle_number": cycle_number,
        "is_mastered": attempt.is_mastered,
        "attempts_remaining": 3 - attempt_number,
        "next_attempt_cycle": cycle_number + (1 if attempt_number >= 3 else 0),
    })

    return render(request, "content/grammar/test_result.html", context)