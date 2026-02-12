# content/views/writing/test.py

from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from content.models.writing import (
    WritingPrompt,
    WritingTestAttempt,
    WritingPracticeAttempt,
    WritingResponse,
)
from .core import _chunk_context, get_writing_objects


@login_required
def writing_test(request, chunk_id, focus_id):
    """
    Final Writing Test View

    Guarantees:
    - Practice must be completed before test access
    - Cooldown enforced after failed attempt
    - Unlimited retries allowed
    - Mastery defined as 100% overall_score
    - Safe against empty prompt sets
    """

    # ---------------------------------------------------------
    # 1. Resolve core objects safely
    # ---------------------------------------------------------
    chunk, focus, unit, task = get_writing_objects(chunk_id, focus_id=focus_id)

    # ---------------------------------------------------------
    # 2. HARD PRACTICE GATE
    # ---------------------------------------------------------
    if not WritingPracticeAttempt.objects.filter(
        student=request.user,
        focus=focus,
    ).exists():
        messages.warning(
            request,
            "You must complete the Practice session before taking the test.",
        )
        return redirect(
            "content:writing_practice",
            chunk_id=chunk.id,
            focus_id=focus.id,
        )

    # ---------------------------------------------------------
    # 3. COOLDOWN AFTER FAILED ATTEMPT
    # ---------------------------------------------------------
    last_attempt = (
        WritingTestAttempt.objects.filter(
            student=request.user,
            focus=focus,
        )
        .order_by("-created_at")
        .first()
    )

    if last_attempt and last_attempt.overall_score < 100:
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
                "content:chunk_writing",
                chunk_id=chunk.id,
            )

    # ---------------------------------------------------------
    # 4. LOAD PROMPTS (content safety)
    # ---------------------------------------------------------
    prompts = WritingPrompt.objects.filter(focus=focus).order_by("id")
    total_prompts = prompts.count()

    if total_prompts == 0:
        messages.error(request, "This test is not yet available.")
        return redirect(
            "content:chunk_writing",
            chunk_id=chunk.id,
        )

    # ---------------------------------------------------------
    # 5. GET → Render test form
    # ---------------------------------------------------------
    if request.method == "GET":
        context = _chunk_context(chunk, focus, task)
        context.update({
            "prompts": prompts,
        })
        return render(
            request,
            "content/writing/test.html",
            context,
        )

    # ---------------------------------------------------------
    # 6. POST → Grade submission
    # ---------------------------------------------------------
    rubric_scores = {}
    correct_count = 0
    results = []
    snapshot = {}

    for p in prompts:
        user_response = request.POST.get(f"p{p.id}", "").strip()

        # Basic scoring logic: exact match with expected keywords
        is_correct = (
            user_response.lower() == p.expected_keywords.strip().lower()
        ) if p.expected_keywords else False

        if is_correct:
            correct_count += 1

        results.append({
            "prompt": p,
            "user_response": user_response,
            "is_correct": is_correct,
        })

        snapshot[p.id] = {
            "user_response": user_response,
            "is_correct": is_correct,
        }

    # Guarded percentage calculation
    score_percent = int((correct_count / total_prompts) * 100) if total_prompts else 0

    # ---------------------------------------------------------
    # 7. Persist attempt (append-only for analytics)
    # ---------------------------------------------------------
    WritingTestAttempt.objects.create(
        student=request.user,
        focus=focus,
        overall_score=score_percent,
        rubric_scores=rubric_scores,  # placeholder for extended rubric logic
        created_at=timezone.now(),
    )

    # ---------------------------------------------------------
    # 8. User feedback messaging
    # ---------------------------------------------------------
    if score_percent == 100:
        messages.success(
            request,
            "Perfect! You have mastered this writing focus.",
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
    mistakes = total_prompts - correct_count

    context = _chunk_context(chunk, focus, task)
    context.update({
        "score": score_percent,
        "correct": correct_count,
        "total": total_prompts,
        "mistakes": mistakes,
        "results": results,
    })

    return render(
        request,
        "content/writing/test_result.html",
        context,
    )