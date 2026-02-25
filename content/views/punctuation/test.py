from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from content.models.core import LessonChunk
from content.models.punctuation import (
    PunctuationQuestion,
    PunctuationTestAttempt,
    PunctuationPracticeAttempt,
    ChunkPunctuationFocus,
)
from .core import _chunk_context, get_punctuation_objects


@login_required
def punctuation_test(request, chunk_id: int, focus_id: int):

    chunk, focus = get_punctuation_objects(chunk_id, focus_id)

    # ------------------------------------------------------------
    # 1. CHUNK SEQUENTIAL LOCK
    # ------------------------------------------------------------
    prev_chunk = LessonChunk.objects.filter(
        lesson=chunk.lesson,
        order__lt=chunk.order
    ).order_by("-order").first()

    if prev_chunk and not prev_chunk.is_mastered_by(request.user):
        messages.warning(
            request,
            "Mastery Lock: Complete previous chunk before this test."
        )
        return redirect("content:lesson_detail", pk=chunk.lesson.pk)

    # ------------------------------------------------------------
    # 2. FOCUS SEQUENTIAL LOCK
    # ------------------------------------------------------------
    previous_focus = (
        ChunkPunctuationFocus.objects
        .filter(chunk=chunk, sequence_order__lt=focus.sequence_order)
        .order_by("-sequence_order")
        .first()
    )

    if previous_focus and not PunctuationTestAttempt.objects.filter(
        user=request.user,
        focus=previous_focus,
        is_mastered=True
    ).exists():
        messages.warning(
            request,
            "Mastery Lock: Complete previous punctuation focus first."
        )
        return redirect("content:chunk_punctuation", chunk_id=chunk.id)

    # ------------------------------------------------------------
    # 3. PERMANENT MASTERY LOCK
    # ------------------------------------------------------------
    existing_mastery = PunctuationTestAttempt.objects.filter(
        user=request.user,
        focus=focus,
        is_mastered=True,
    ).first()

    if existing_mastery:
        return redirect(
            "content:punctuation:test_result",
            chunk_id=chunk.id,
            focus_id=focus.id,
        )

    # ------------------------------------------------------------
    # 4. PRACTICE CLEARANCE GATE
    # ------------------------------------------------------------
    practice_cleared = PunctuationPracticeAttempt.objects.filter(
        user=request.user,
        focus=focus,
        is_passed=True,
    ).exists()

    if not practice_cleared:
        messages.warning(
            request,
            "Complete practice perfectly before attempting the test."
        )
        return redirect(
            "content:punctuation:practice",
            chunk_id=chunk.id,
            focus_id=focus.id
        )

    # ------------------------------------------------------------
    # 5. LOAD QUESTIONS
    # ------------------------------------------------------------
    questions = list(
        PunctuationQuestion.objects.filter(focus=focus).order_by("id")
    )

    if not questions:
        messages.error(request, "No test questions available yet.")
        return redirect("content:chunk_punctuation", chunk_id=chunk.id)

    submitted = False
    correct_count = 0
    total_questions = len(questions)

    # ------------------------------------------------------------
    # 6. HANDLE POST → CREATE NEW ATTEMPT
    # ------------------------------------------------------------
    if request.method == "POST":
        submitted = True

        for q in questions:
            user_answer = request.POST.get(f"q{q.id}", "").strip()

            is_correct = (
                user_answer.lower() == q.correct_answer.strip().lower()
                if user_answer else False
            )

            if is_correct:
                correct_count += 1

            q.user_answer = user_answer
            q.is_correct = is_correct
            q.feedback_ready = True

        score_percent = int((correct_count / total_questions) * 100) if total_questions else 0

        # Calculate current cycle and attempt number
        latest = PunctuationTestAttempt.objects.filter(
            user=request.user,
            focus=focus,
        ).order_by("-cycle_number", "-attempt_number").first()

        if latest:
            cycle_number = latest.cycle_number
            attempt_number = latest.attempt_number + 1
            if attempt_number > 3:
                cycle_number += 1
                attempt_number = 1
        else:
            cycle_number = 1
            attempt_number = 1

        attempt = PunctuationTestAttempt.objects.create(
            user=request.user,
            focus=focus,
            attempt_number=attempt_number,
            cycle_number=cycle_number,
            total_questions=total_questions,
            correct_answers=correct_count,
            score_percent=score_percent,
        )

        if attempt.is_mastered:
            messages.success(request, "Congratulations! Mastery achieved (100%).")
            return redirect(
                "content:punctuation:test_result",
                chunk_id=chunk.id,
                focus_id=focus.id,
            )
        else:
            messages.warning(
                request,
                f"You got {correct_count}/{total_questions} correct. "
                "100% is required for Mastery. Try again!"
            )

    # ------------------------------------------------------------
    # 7. CONTEXT
    # ------------------------------------------------------------
    context = _chunk_context(chunk, focus=focus)
    context.update({
        "questions": questions,
        "submitted": submitted,
    })

    return render(request, "content/punctuation/test.html", context)