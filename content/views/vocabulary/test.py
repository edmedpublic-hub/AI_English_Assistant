# content/views/vocabulary/test.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from content.models.testing import VocabularyTestAttempt
from ..test_engine import build_questions  # Ensure this file exists!
from .core import get_vocab_context, _vocab_base_context

@login_required # Added to ensure request.user exists for the save
def chunk_vocabulary_test(request, chunk_id):
    """
    High-stakes vocabulary assessment with session-based progress.
    """
    chunk, lesson = get_vocab_context(chunk_id)

    # Handle retake logic
    if request.GET.get("retake") == "1":
        request.session.pop("test_data", None)
        return redirect(request.path)

    # Initialize test in session if not present
    if "test_data" not in request.session:
        # Use the related_name="vocab_items" confirmed in your models
        vocab_list = list(chunk.vocab_items.all())
        questions = build_questions(vocab_list)

        if not questions:
            context = _vocab_base_context(chunk, lesson)
            context.update({
                "question": {"question": "No valid test questions available.", "options": []},
                "question_number": 0,
                "total": 0,
            })
            return render(request, "content/vocab/chunk_vocabulary_test.html", context)

        request.session["test_data"] = {
            "questions": questions,
            "current": 0,
            "score": 0,
        }

    test = request.session["test_data"]
    questions = test["questions"]
    index = test["current"]

    # --- Test Completion Logic ---
    if index >= len(questions):
        total = len(questions)
        correct = test["score"]
        percent = round((correct / total) * 100) if total > 0 else 0

        # Save result to database if not already saved for this session
        if not test.get("saved"):
            VocabularyTestAttempt.objects.create(
                user=request.user,
                lesson=lesson,
                chunk=chunk,
                score_percent=percent,
                correct_answers=correct,
                total_questions=total,
                questions_data=test["questions"],
            )
            test["saved"] = True
            request.session.modified = True

        context = _vocab_base_context(chunk, lesson)
        context.update({
            "score": percent,
            "passed": percent == 100,
            "can_retake": percent < 100, # Requirement: 100% to unlock next
        })
        return render(request, "content/vocab/test_result.html", context)

    # --- Active Question Logic ---
    current = questions[index]

    if request.method == "POST":
        if request.POST.get("option") == current["answer"]:
            test["score"] += 1
        test["current"] += 1
        request.session.modified = True
        return redirect(request.path)

    context = _vocab_base_context(chunk, lesson)
    context.update({
        "question": current,
        "question_number": index + 1,
        "total": len(questions),
    })
    return render(request, "content/vocab/chunk_vocabulary_test.html", context)

@login_required
def test_history(request):
    attempts = (
        VocabularyTestAttempt.objects
        .filter(user=request.user)
        .select_related("lesson", "chunk")
        .order_by("-created_at")
    )
    return render(request, "content/vocab/test_history.html", {"attempts": attempts})

@login_required
def attempt_detail(request, attempt_id):
    attempt = get_object_or_404(VocabularyTestAttempt, id=attempt_id, user=request.user)
    return render(request, "content/vocab/attempt_detail.html", {
        "attempt": attempt,
        "questions": attempt.questions_data or [],
    })