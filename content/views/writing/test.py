# content/views/writing/test.py

from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from content.models.writing import (
    WritingPrompt,
    WritingTestAttempt,
    WritingPracticeAttempt,
    ChunkWritingFocus,
)
from content.models.core import LessonChunk
from .core import _chunk_context, get_writing_objects


@transaction.atomic
def _handle_test_submission(request, chunk, focus, prompts, total_prompts, cycle_number, attempt_number):
    """
    Handle test submission and grading.
    Separated for clarity and transaction atomicity.
    """

    rubric_scores = {}
    correct_count = 0
    results = []
    snapshot = {}
    question_attempts = []

    for prompt in prompts:
        user_response = request.POST.get(f"p{prompt.id}", "").strip()

        is_correct = False
        score_detail = {}

        if prompt.expected_keywords:
            expected_keywords = [
                k.strip().lower()
                for k in prompt.expected_keywords.split(',')
                if k.strip()
            ]

            if expected_keywords:
                response_lower = user_response.lower()
                found_keywords = [
                    keyword for keyword in expected_keywords
                    if keyword in response_lower
                ]

                match_percentage = int((len(found_keywords) / len(expected_keywords)) * 100)
                is_correct = (match_percentage == 100)

                score_detail = {
                    'expected_keywords': expected_keywords,
                    'found_keywords': found_keywords,
                    'match_percentage': match_percentage,
                }
            else:
                is_correct = len(user_response) > 0
                score_detail = {'basic_validation': True}
        else:
            is_correct = len(user_response) > 0
            score_detail = {'basic_validation': True}

        if is_correct:
            correct_count += 1

        result_item = {
            "prompt": prompt,
            "user_response": user_response,
            "is_correct": is_correct,
            "score_detail": score_detail,
        }
        results.append(result_item)

        snapshot[str(prompt.id)] = {
            "user_response": user_response,
            "is_correct": is_correct,
            "score_detail": score_detail,
        }

        question_attempts.append({
            'prompt_id': prompt.id,
            'response': user_response,
            'is_correct': is_correct,
            'score_detail': score_detail,
        })

    score_percent = int((correct_count / total_prompts) * 100) if total_prompts else 0
    is_mastered = (score_percent == 100)

    test_attempt = WritingTestAttempt.objects.create(
        user=request.user,
        focus=focus,
        prompt=prompts[0] if prompts else None,
        attempt_number=attempt_number,
        cycle_number=cycle_number,
        response_text="\n---\n".join([r['user_response'] for r in results]),
        rubric_scores={
            'overall': {
                'score': score_percent,
                'is_mastered': is_mastered,
                'correct_count': correct_count,
                'total_questions': total_prompts,
            },
            'per_prompt': snapshot,
            'question_attempts': question_attempts,
        },
        overall_score=score_percent,
        is_mastered=is_mastered,
        time_spent_seconds=int(request.POST.get('time_taken', 0) or 0),
    )

    if is_mastered:
        messages.success(
            request,
            f"🎉 Perfect! You have mastered this writing focus! "
            f"(Attempt {attempt_number}/3, Cycle {cycle_number})",
        )

        next_focus = ChunkWritingFocus.objects.filter(
            chunk=chunk,
            sequence_order=focus.sequence_order + 1
        ).first()

        if next_focus:
            messages.info(
                request,
                f"You've unlocked: {next_focus.focus_title}"
            )
    else:
        attempts_remaining = 3 - attempt_number

        if attempts_remaining > 0:
            messages.warning(
                request,
                f"You scored {score_percent}% ({correct_count}/{total_prompts}). "
                f"Need 100% to master. "
                f"Attempts remaining in cycle {cycle_number}: {attempts_remaining}",
            )
        else:
            messages.warning(
                request,
                f"You've used all 3 attempts in cycle {cycle_number} with {score_percent}%. "
                f"A new cycle (Cycle {cycle_number + 1}) will start on your next attempt.",
            )

    mistakes = total_prompts - correct_count

    context = _chunk_context(chunk, focus=focus)
    context.update({
        "test_attempt": test_attempt,
        "score": score_percent,
        "correct": correct_count,
        "total": total_prompts,
        "mistakes": mistakes,
        "results": results,
        "attempt_number": attempt_number,
        "cycle_number": cycle_number,
        "is_mastered": is_mastered,
        "attempts_remaining": 3 - attempt_number,
        "next_attempt_cycle": cycle_number + (1 if attempt_number >= 3 else 0),
    })

    return render(
        request,
        "content/writing/test_result.html",
        context,
    )


@login_required
def writing_test(request, chunk_id, focus_id):
    """
    Final Writing Test View

    Features:
    - Practice must be completed before test access
    - 3 attempts max per cycle
    - Cooldown between attempts
    - Mastery defined as 100% overall_score for chunk-level
    - Safe against empty prompt sets
    """

    # 1. Resolve core objects safely
    chunk, focus, unit, task = get_writing_objects(chunk_id, focus_id=focus_id)

    # 2. Load prompts
    prompts = list(WritingPrompt.objects.filter(focus=focus).order_by("id"))
    total_prompts = len(prompts)

    if total_prompts == 0:
        messages.error(request, "This test is not yet available.")
        return redirect("content:chunk_writing", chunk_id=chunk.id)

    # 3. PRACTICE GATE — single bulk query
    practiced_prompts = set(
        WritingPracticeAttempt.objects.filter(
            user=request.user,
            focus=focus,
            prompt__in=prompts
        ).values_list('prompt_id', flat=True).distinct()
    )

    if len(practiced_prompts) < total_prompts:
        unpracticed = [p.id for p in prompts if p.id not in practiced_prompts]
        messages.warning(
            request,
            f"You must practice all prompts before taking the test. "
            f"Unpracticed prompts: {', '.join(map(str, unpracticed))}",
        )
        return redirect(
            "content:writing:practice",
            chunk_id=chunk.id,
            focus_id=focus.id,
        )

    # 4. CYCLE & ATTEMPT TRACKING
    latest_attempt = (
        WritingTestAttempt.objects.filter(
            user=request.user,
            focus=focus
        )
        .order_by("-created_at")
        .first()
    )

    if latest_attempt:
        if latest_attempt.is_mastered:
            messages.success(
                request,
                "You have already mastered this focus! Review your results below."
            )
            return redirect(
                "content:writing:test-result",
                chunk_id=chunk.id,
                focus_id=focus.id,
                attempt_id=latest_attempt.id
            )

        attempts_in_current_cycle = WritingTestAttempt.objects.filter(
            user=request.user,
            focus=focus,
            cycle_number=latest_attempt.cycle_number
        ).count()

        if attempts_in_current_cycle >= 3:
            current_cycle = latest_attempt.cycle_number + 1
            attempt_number = 1
        else:
            current_cycle = latest_attempt.cycle_number
            attempt_number = attempts_in_current_cycle + 1
    else:
        current_cycle = 1
        attempt_number = 1

    # 5. COOLDOWN CHECK
    if latest_attempt and not latest_attempt.is_mastered:
        cooldown_minutes = 10
        cooldown = timedelta(minutes=cooldown_minutes)
        elapsed = timezone.now() - latest_attempt.created_at

        if elapsed < cooldown:
            remaining_seconds = int((cooldown - elapsed).total_seconds())
            minutes_left = (remaining_seconds // 60) + 1

            messages.error(
                request,
                f"Cooldown active. You can retry in {minutes_left} minute(s). "
                f"(Attempt {attempt_number - 1}/3 in cycle {current_cycle})",
            )
            return redirect("content:chunk_writing", chunk_id=chunk.id)

    # 6. GET → Render test form
    if request.method == "GET":
        context = _chunk_context(chunk, focus=focus)
        context.update({
            "prompts": prompts,
            "attempt_number": attempt_number,
            "cycle_number": current_cycle,
            "attempts_remaining": 3 - (attempt_number - 1) if attempt_number > 1 else 3,
            "last_attempt_score": latest_attempt.overall_score if latest_attempt else None,
        })
        return render(request, "content/writing/test.html", context)

    # 7. POST → Grade submission
    return _handle_test_submission(
        request, chunk, focus, prompts,
        total_prompts, current_cycle, attempt_number
    )


@login_required
def writing_test_result_detail(request, chunk_id, focus_id, attempt_id):
    """
    View details of a specific test attempt.
    """
    chunk = get_object_or_404(LessonChunk, id=chunk_id)
    focus = get_object_or_404(ChunkWritingFocus, id=focus_id, chunk=chunk)

    attempt = get_object_or_404(
        WritingTestAttempt,
        id=attempt_id,
        user=request.user,
        focus=focus
    )

    results = []
    if 'per_prompt' in attempt.rubric_scores:
        prompts = {p.id: p for p in WritingPrompt.objects.filter(focus=focus)}

        for prompt_id_str, data in attempt.rubric_scores['per_prompt'].items():
            prompt_id = int(prompt_id_str)
            if prompt_id in prompts:
                results.append({
                    'prompt': prompts[prompt_id],
                    'user_response': data.get('user_response', ''),
                    'is_correct': data.get('is_correct', False),
                    'score_detail': data.get('score_detail', {}),
                })

    latest = (
        WritingTestAttempt.objects
        .filter(user=request.user, focus=focus)
        .order_by('-created_at')
        .first()
    )

    context = _chunk_context(chunk, focus=focus)
    context.update({
        'attempt': attempt,
        'results': results,
        'score': attempt.overall_score,
        'correct': attempt.rubric_scores.get('overall', {}).get('correct_count', 0),
        'total': attempt.rubric_scores.get('overall', {}).get('total_questions', 0),
        'is_mastered': attempt.is_mastered,
        'is_current': latest is not None and attempt.id == latest.id,
    })

    return render(request, "content/writing/test_attempt_detail.html", context)


@login_required
def writing_test_history(request, chunk_id, focus_id):
    """
    View all test attempts for a focus.
    """
    chunk = get_object_or_404(LessonChunk, id=chunk_id)
    focus = get_object_or_404(ChunkWritingFocus, id=focus_id, chunk=chunk)

    attempts = WritingTestAttempt.objects.filter(
        user=request.user,
        focus=focus
    ).order_by('-cycle_number', '-attempt_number')

    attempts_by_cycle = {}
    for attempt in attempts:
        if attempt.cycle_number not in attempts_by_cycle:
            attempts_by_cycle[attempt.cycle_number] = []
        attempts_by_cycle[attempt.cycle_number].append(attempt)

    context = _chunk_context(chunk, focus=focus)
    context.update({
        'attempts': attempts,
        'attempts_by_cycle': attempts_by_cycle,
        'total_attempts': attempts.count(),
        'mastered': attempts.filter(is_mastered=True).exists(),
    })

    return render(request, "content/writing/test_history.html", context)