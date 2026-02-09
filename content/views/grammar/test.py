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
    """
    Final Grammar Test View

    Guarantees:
    - Practice must be completed before test access
    - Cooldown enforced after failed attempt
    - Unlimited retries allowed
    - Mastery defined as 100%
    - Safe against empty question sets
    - No template arithmetic required (future-proof)
    """

    # ---------------------------------------------------------
    # 1. Resolve core objects safely
    # ---------------------------------------------------------
    chunk, focus = get_grammar_objects(chunk_id, focus_id)
    concept = focus.concept

    # ---------------------------------------------------------
    # 2. HARD PRACTICE GATE
    # ---------------------------------------------------------
    if not GrammarPracticeAttempt.objects.filter(
        student=request.user,
        focus=focus,
    ).exists():
        messages.warning(
            request,
            "You must complete the Practice session before taking the test.",
        )
        return redirect(
            "content:grammar_practice",
            chunk_id=chunk.id,
            focus_id=focus.id,
        )

    # ---------------------------------------------------------
    # 3. COOLDOWN AFTER FAILED ATTEMPT
    # ---------------------------------------------------------
    last_attempt = (
        GrammarTestAttempt.objects.filter(
            student=request.user,
            focus=focus,
        )
        .order_by("-created_at")
        .first()
    )

    if last_attempt and last_attempt.score_percent < 100:
        cooldown = timedelta(minutes=10)
        elapsed = timezone.now() - last_attempt.created_at

        if elapsed < cooldown:
            remaining_seconds = int((cooldown - elapsed).total_seconds())
            minutes_left = (remaining_seconds // 60) + 1

            messages.error(
                request,
                f"Cooldown active. You can retry in {minutes_left} minute(s).",
            )
            return redirect(
                "content:chunk_grammar",
                chunk_id=chunk.id,
            )

    # ---------------------------------------------------------
    # 4. LOAD QUESTIONS (content safety)
    # ---------------------------------------------------------
    questions = GrammarQuestion.objects.filter(
        focus=focus
    ).order_by("id")

    total_questions = questions.count()

    if total_questions == 0:
        messages.error(request, "This test is not yet available.")
        return redirect(
            "content:chunk_grammar",
            chunk_id=chunk.id,
        )

    # ---------------------------------------------------------
    # 5. GET → Render test form
    # ---------------------------------------------------------
    if request.method == "GET":
        context = _chunk_context(chunk, focus, concept)
        context.update({
            "questions": questions,
        })
        return render(
            request,
            "content/grammar/test.html",
            context,
        )

    # ---------------------------------------------------------
    # 6. POST → Grade submission
    # ---------------------------------------------------------
    correct_count = 0
    results = []
    snapshot = {}

    for q in questions:
        user_answer = request.POST.get(f"q{q.id}", "").strip()

        is_correct = (
            user_answer.lower() == q.correct_answer.strip().lower()
        )

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

    # Guarded percentage calculation
    score_percent = int((correct_count / total_questions) * 100) if total_questions else 0

    # ---------------------------------------------------------
    # 7. Persist attempt (append-only for analytics)
    # ---------------------------------------------------------
    GrammarTestAttempt.objects.create(
        student=request.user,
        focus=focus,
        score_percent=score_percent,
        correct_answers=correct_count,
        total_questions=total_questions,
        questions_snapshot=snapshot,
    )

    # ---------------------------------------------------------
    # 8. User feedback messaging
    # ---------------------------------------------------------
    if score_percent == 100:
        messages.success(
            request,
            "Perfect! You have mastered this grammar topic.",
        )
    elif score_percent >= 80:
        messages.info(
            request,
            f"Very close ({score_percent}%). Review and try again.",
        )
    elif score_percent >= 50:
        messages.warning(
            request,
            f"You scored {score_percent}%. More practice is recommended.",
        )
    else:
        messages.error(
            request,
            f"Score: {score_percent}%. Please revisit the Teach section.",
        )

    # ---------------------------------------------------------
    # 9. Render result page (NO template math required)
    # ---------------------------------------------------------
    mistakes = total_questions - correct_count

    context = _chunk_context(chunk, focus, concept)
    context.update({
        "score": score_percent,
        "correct": correct_count,
        "total": total_questions,
        "mistakes": mistakes,   # ← prevents template crash forever
        "results": results,
    })

    return render(
        request,
        "content/grammar/test_result.html",
        context,
    )
