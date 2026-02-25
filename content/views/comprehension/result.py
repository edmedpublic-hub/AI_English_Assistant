# views/comprehension/result.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch

from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionTestAttempt,
    ComprehensionPracticeAttempt,  # Added missing import
    ComprehensionQuestionAttempt,
)


@login_required
def comprehension_result_view(request, chunk_id, focus_id):
    """
    Displays mastery result for the latest test attempt of the
    authenticated student within a specific focus.

    Features:
    - Student isolation (request.user only)
    - Latest attempt determinism
    - Correct mistake reconstruction
    - Attempt cycle tracking
    - LMS-safe rendering
    """

    student = request.user

    # --------------------------------------------------
    # Validate focus belongs to chunk
    # --------------------------------------------------
    focus = get_object_or_404(
        ChunkComprehensionFocus.objects.select_related('chunk'),
        id=focus_id,
        chunk_id=chunk_id,
    )

    # --------------------------------------------------
    # Fetch latest test attempt for this student + focus
    # --------------------------------------------------
    latest_attempt = (
        ComprehensionTestAttempt.objects
        .filter(user=student, focus=focus)
        .select_related('focus')
        .order_by("-created_at")
        .first()
    )

    if not latest_attempt:
        # No attempt yet → redirect back to test start
        return redirect("content:comprehension:test", chunk_id=chunk_id, focus_id=focus.id)

    # --------------------------------------------------
    # Fetch all test attempts for history context
    # --------------------------------------------------
    all_attempts = (
        ComprehensionTestAttempt.objects
        .filter(user=student, focus=focus)
        .order_by("-cycle_number", "-attempt_number")
    )

    # --------------------------------------------------
    # Fetch per-question attempts for this specific test
    # --------------------------------------------------
    question_attempts = (
        ComprehensionQuestionAttempt.objects
        .filter(
            user=student,
            test_attempt=latest_attempt,
            question__focus=focus,
        )
        .select_related("question")
        .order_by("question_id")
    )

    # Separate correct/incorrect for analysis
    correct_answers = [qa for qa in question_attempts if qa.is_correct]
    mistakes = [qa for qa in question_attempts if not qa.is_correct]

    # Group mistakes by question for template display
    mistakes_by_question = {}
    for mistake in mistakes:
        q_id = mistake.question_id
        if q_id not in mistakes_by_question:
            mistakes_by_question[q_id] = {
                'question': mistake.question,
                'attempts': [],
                'last_attempt': mistake,
            }
        mistakes_by_question[q_id]['attempts'].append(mistake)

    # --------------------------------------------------
    # Calculate next steps based on result
    # --------------------------------------------------
    next_steps = {}
    
    if latest_attempt.is_mastered:
        # Check if next focus is available
        next_focus = (
            ChunkComprehensionFocus.objects
            .filter(
                chunk=focus.chunk,
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
            # Check if this is the last focus in the chunk
            next_steps = {
                'action': 'chunk_complete',
                'message': 'Congratulations! You have completed all comprehension focuses in this chunk.'
            }
    else:
        # Calculate attempts remaining in current cycle
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
                'message': f'You have used all 3 attempts in cycle {latest_attempt.cycle_number}. Start a new cycle to try again.'
            }

    # --------------------------------------------------
    # Context for template
    # --------------------------------------------------
    context = {
        # Core objects
        "focus": focus,
        "chunk": focus.chunk,
        
        # Current attempt details
        "attempt": latest_attempt,
        "attempt_number": latest_attempt.attempt_number,
        "cycle_number": latest_attempt.cycle_number,
        "score": latest_attempt.score_percent,
        "correct_count": latest_attempt.correct_answers,
        "total_questions": latest_attempt.total_questions,
        
        # Performance breakdown
        "question_attempts": question_attempts,
        "correct_answers": correct_answers,
        "mistakes": mistakes,
        "mistakes_by_question": mistakes_by_question,
        "mistake_count": len(mistakes),
        
        # History and progression
        "all_attempts": all_attempts,
        "attempts_in_current_cycle": all_attempts.filter(
            cycle_number=latest_attempt.cycle_number
        ).count(),
        
        # Next steps
        "next_steps": next_steps,
        "is_mastered": latest_attempt.is_mastered,
        
        # Template flags
        "show_mistakes": len(mistakes) > 0,
        "show_retry_options": not latest_attempt.is_mastered,
    }

    return render(
        request,
        "content/comprehension/test_result.html",
        context,
    )


@login_required
def comprehension_attempt_detail_view(request, chunk_id, focus_id, attempt_id):
    """
    View details of a specific test attempt (for history browsing)
    """
    student = request.user

    attempt = get_object_or_404(
        ComprehensionTestAttempt,
        id=attempt_id,
        user=student,
        focus_id=focus_id,
        focus__chunk_id=chunk_id,
    )

    question_attempts = (
        ComprehensionQuestionAttempt.objects
        .filter(
            user=student,
            test_attempt=attempt,
            question__focus_id=focus_id,
        )
        .select_related("question")
        .order_by("question_id")
    )

    latest = (
        ComprehensionTestAttempt.objects
        .filter(user=student, focus=attempt.focus)
        .order_by("-created_at")
        .first()
    )

    context = {
        "focus": attempt.focus,
        "chunk": attempt.focus.chunk,
        "attempt": attempt,
        "question_attempts": question_attempts,
        "correct_answers": [qa for qa in question_attempts if qa.is_correct],
        "mistakes": [qa for qa in question_attempts if not qa.is_correct],
        "is_current_attempt": latest is not None and attempt.id == latest.id,
    }

    return render(
        request,
        "content/comprehension/attempt_detail.html",
        context,
    )


@login_required
def comprehension_practice_result_view(request, chunk_id, focus_id, practice_id=None):
    """
    Displays practice attempt results
    """
    student = request.user

    focus = get_object_or_404(
        ChunkComprehensionFocus,
        id=focus_id,
        chunk_id=chunk_id,
    )

    if practice_id:
        # Specific practice attempt
        practice_attempt = get_object_or_404(
            ComprehensionPracticeAttempt,
            id=practice_id,
            user=student,
            focus=focus,
        )
    else:
        # Latest practice attempt
        practice_attempt = (
            ComprehensionPracticeAttempt.objects
            .filter(user=student, focus=focus)
            .order_by("-attempted_at")
            .first()
        )

        if not practice_attempt:
            return redirect("content:comprehension:practice", chunk_id=chunk_id, focus_id=focus.id)

    question_attempts = (
        ComprehensionQuestionAttempt.objects
        .filter(
            user=student,
            practice_attempt=practice_attempt,
            question__focus=focus,
        )
        .select_related("question")
        .order_by("question_id")
    )

    context = {
        "focus": focus,
        "chunk": focus.chunk,
        "practice_attempt": practice_attempt,
        "question_attempts": question_attempts,
        "score": practice_attempt.score_percent,
        "correct_count": practice_attempt.correct_answers,
        "total_questions": practice_attempt.total_questions,
        "is_passed": practice_attempt.is_passed,
        "attempt_number": practice_attempt.attempt_number,
        "cycle_number": practice_attempt.cycle_number,
    }

    return render(
        request,
        "content/comprehension/practice_result.html",
        context,
    )