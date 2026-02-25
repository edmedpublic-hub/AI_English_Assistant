# content/views/punctuation/result.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from content.models.punctuation import (
    ChunkPunctuationFocus,
    PunctuationTestAttempt,
    PunctuationPracticeAttempt,
)
from .core import _chunk_context, get_punctuation_objects


@login_required
def punctuation_test_result(request, chunk_id, focus_id):
    """
    Displays the result of the latest punctuation test attempt.
    """
    chunk, focus = get_punctuation_objects(chunk_id, focus_id)

    # Fetch latest test attempt
    latest_attempt = (
        PunctuationTestAttempt.objects
        .filter(user=request.user, focus=focus)
        .order_by("-created_at")
        .first()
    )

    if not latest_attempt:
        return redirect(
            "content:punctuation:test",
            chunk_id=chunk.id,
            focus_id=focus.id
        )

    # All attempts for history context
    all_attempts = (
        PunctuationTestAttempt.objects
        .filter(user=request.user, focus=focus)
        .order_by("-cycle_number", "-attempt_number")
    )

    # Calculate next steps
    next_steps = {}

    if latest_attempt.is_mastered:
        next_focus = (
            ChunkPunctuationFocus.objects
            .filter(
                chunk=chunk,
                sequence_order=focus.sequence_order + 1
            )
            .first()
        )

        if next_focus:
            next_steps = {
                'action': 'unlock_next',
                'focus': next_focus,
                'message': f'You have unlocked: {next_focus.focus_title}'
            }
        else:
            next_steps = {
                'action': 'chunk_complete',
                'message': 'Congratulations! You have completed all punctuation focuses in this chunk.'
            }
    else:
        attempts_this_cycle = all_attempts.filter(
            cycle_number=latest_attempt.cycle_number
        ).count()

        attempts_remaining = 3 - attempts_this_cycle

        if attempts_remaining > 0:
            next_steps = {
                'action': 'retry_test',
                'attempts_remaining': attempts_remaining,
                'message': f'You have {attempts_remaining} attempt(s) remaining in cycle {latest_attempt.cycle_number}.'
            }
        else:
            next_steps = {
                'action': 'new_cycle',
                'next_cycle': latest_attempt.cycle_number + 1,
                'message': f'All 3 attempts used in cycle {latest_attempt.cycle_number}. Start a new cycle to try again.'
            }

    context = _chunk_context(chunk, focus=focus)
    context.update({
        # Attempt details
        'attempt': latest_attempt,
        'score': latest_attempt.score_percent,
        'correct_count': latest_attempt.correct_answers,
        'total_questions': latest_attempt.total_questions,
        'attempt_number': latest_attempt.attempt_number,
        'cycle_number': latest_attempt.cycle_number,
        'is_mastered': latest_attempt.is_mastered,

        # History
        'all_attempts': all_attempts,
        'attempts_in_current_cycle': all_attempts.filter(
            cycle_number=latest_attempt.cycle_number
        ).count(),

        # Next steps
        'next_steps': next_steps,
        'show_retry_options': not latest_attempt.is_mastered,
    })

    return render(request, "content/punctuation/test_result.html", context)


@login_required
def punctuation_attempt_detail(request, chunk_id, focus_id, attempt_id):
    """
    View details of a specific punctuation test attempt.
    """
    chunk, focus = get_punctuation_objects(chunk_id, focus_id)

    attempt = get_object_or_404(
        PunctuationTestAttempt,
        id=attempt_id,
        user=request.user,
        focus=focus,
    )

    # Reconstruct question results from snapshot
    questions_data = attempt.questions_data or {}
    questions = questions_data.get('questions', [])

    latest = (
        PunctuationTestAttempt.objects
        .filter(user=request.user, focus=focus)
        .order_by('-created_at')
        .first()
    )

    context = _chunk_context(chunk, focus=focus)
    context.update({
        'attempt': attempt,
        'questions': questions,
        'score': attempt.score_percent,
        'correct_count': attempt.correct_answers,
        'total_questions': attempt.total_questions,
        'is_mastered': attempt.is_mastered,
        'is_current_attempt': latest is not None and attempt.id == latest.id,
    })

    return render(request, "content/punctuation/attempt_detail.html", context)