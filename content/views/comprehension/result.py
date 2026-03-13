# PATH: content/views/comprehension/result.py
# ACTION: Replace the entire existing file with this content.
#
# CHANGES FROM ORIGINAL:
#   - comprehension_result_view: removed attempt_id from redirect target
#     (test-result URL no longer takes attempt_id — uses latest attempt)
#   - Fixed context variable names to match test_result.html template:
#       "score" → kept (template uses {{ score_percent }} AND {{ score }},
#        added both to be safe)
#       "results" added (template iterates {% for res in results %})
#       "next_focus" added at top level (template uses {{ next_focus }})
#       "mistakes" kept as integer count AND as list
#   - comprehension_practice_result_view: fixed context to match
#     practice_result.html (score, correct_count, total_questions,
#     is_passed, attempt_number, cycle_number, question_attempts)
#   - comprehension_attempt_detail_view: unchanged
#   - All DB queries unchanged

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionTestAttempt,
    ComprehensionPracticeAttempt,
    ComprehensionQuestionAttempt,
)


# ═══════════════════════════════════════════════════════════════
#  TEST RESULT VIEW
# ═══════════════════════════════════════════════════════════════

@login_required
def comprehension_result_view(request, chunk_id, focus_id):
    """
    Displays mastery result for the latest test attempt.
    Renders test_result.html.
    """
    student = request.user

    focus = get_object_or_404(
        ChunkComprehensionFocus.objects.select_related("chunk"),
        id=focus_id,
        chunk_id=chunk_id,
    )

    latest_attempt = (
        ComprehensionTestAttempt.objects
        .filter(user=student, focus=focus)
        .select_related("focus")
        .order_by("-created_at")
        .first()
    )

    if not latest_attempt:
        return redirect(
            "content:comprehension:test",
            chunk_id=chunk_id,
            focus_id=focus.id,
        )

    # Per-question attempts for this test
    question_attempts = list(
        ComprehensionQuestionAttempt.objects
        .filter(user=student, test_attempt=latest_attempt)
        .select_related("question")
        .order_by("question_id")
    )

    mistakes_list   = [qa for qa in question_attempts if not qa.is_correct]
    correct_list    = [qa for qa in question_attempts if qa.is_correct]

    # Next focus for "Continue" button on pass
    next_focus = (
        ChunkComprehensionFocus.objects
        .filter(chunk=focus.chunk, sequence_order=focus.sequence_order + 1)
        .first()
    )

    # All attempts for history
    all_attempts = (
        ComprehensionTestAttempt.objects
        .filter(user=student, focus=focus)
        .order_by("-cycle_number", "-attempt_number")
    )

    attempts_this_cycle = all_attempts.filter(
        cycle_number=latest_attempt.cycle_number
    ).count()

    context = {
        # Core objects
        "focus":          focus,
        "chunk":          focus.chunk,

        # Attempt details — both names for template compatibility
        "attempt":         latest_attempt,
        "score_percent":   latest_attempt.score_percent,
        "score":           latest_attempt.score_percent,
        "correct_answers": latest_attempt.correct_answers,
        "total_questions": latest_attempt.total_questions,
        "is_mastered":     latest_attempt.is_mastered,
        "attempt_number":  latest_attempt.attempt_number,
        "cycle_number":    latest_attempt.cycle_number,

        # Question breakdown
        "results":          question_attempts,   # template: {% for res in results %}
        "question_attempts": question_attempts,
        "correct_list":     correct_list,
        "mistakes":         mistakes_list,       # template: {{ mistakes }} count display
        "mistake_count":    len(mistakes_list),

        # Navigation
        "next_focus":       next_focus,

        # History
        "all_attempts":             all_attempts,
        "attempts_in_current_cycle": attempts_this_cycle,
    }

    return render(request, "content/comprehension/test_result.html", context)


# ═══════════════════════════════════════════════════════════════
#  PRACTICE RESULT VIEW
# ═══════════════════════════════════════════════════════════════

@login_required
def comprehension_practice_result_view(request, chunk_id, focus_id, practice_id=None):
    """
    Displays practice attempt results.
    Renders practice_result.html.
    """
    student = request.user

    focus = get_object_or_404(
        ChunkComprehensionFocus.objects.select_related("chunk"),
        id=focus_id,
        chunk_id=chunk_id,
    )

    if practice_id:
        practice_attempt = get_object_or_404(
            ComprehensionPracticeAttempt,
            id=practice_id,
            user=student,
            focus=focus,
        )
    else:
        practice_attempt = (
            ComprehensionPracticeAttempt.objects
            .filter(user=student, focus=focus)
            .order_by("-attempted_at")
            .first()
        )
        if not practice_attempt:
            return redirect(
                "content:comprehension:practice",
                chunk_id=chunk_id,
                focus_id=focus.id,
            )

    question_attempts = list(
        ComprehensionQuestionAttempt.objects
        .filter(user=student, practice_attempt=practice_attempt)
        .select_related("question")
        .order_by("question_id")
    )

    context = {
        "focus":           focus,
        "chunk":           focus.chunk,
        "practice_attempt": practice_attempt,
        "question_attempts": question_attempts,
        "score":           practice_attempt.score_percent,
        "correct_count":   practice_attempt.correct_answers,
        "total_questions": practice_attempt.total_questions,
        "is_passed":       practice_attempt.is_passed,
        "attempt_number":  practice_attempt.attempt_number,
        "cycle_number":    practice_attempt.cycle_number,
    }

    return render(request, "content/comprehension/practice_result.html", context)


# ═══════════════════════════════════════════════════════════════
#  ATTEMPT DETAIL VIEW  (history browsing)
# ═══════════════════════════════════════════════════════════════

@login_required
def comprehension_attempt_detail_view(request, chunk_id, focus_id, attempt_id):
    """
    View details of a specific historical test attempt.
    """
    student = request.user

    attempt = get_object_or_404(
        ComprehensionTestAttempt,
        id=attempt_id,
        user=student,
        focus_id=focus_id,
        focus__chunk_id=chunk_id,
    )

    question_attempts = list(
        ComprehensionQuestionAttempt.objects
        .filter(user=student, test_attempt=attempt, question__focus_id=focus_id)
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
        "focus":            attempt.focus,
        "chunk":            attempt.focus.chunk,
        "attempt":          attempt,
        "question_attempts": question_attempts,
        "correct_answers":  [qa for qa in question_attempts if qa.is_correct],
        "mistakes":         [qa for qa in question_attempts if not qa.is_correct],
        "is_current_attempt": latest is not None and attempt.id == latest.id,
    }

    return render(request, "content/comprehension/attempt_detail.html", context)