from django.shortcuts import render
from django.db.models import Avg
from ..models import (
    SentenceAttempt,
    VocabularyAttempt,
    GrammarAttempt,
    ComprehensionAttempt,
)


def content_student_dashboard(request, student_id):
    return render(
        request,
        "content/student_dashboard.html",
        {"student_id": student_id},
    )


def content_student_attempts(request, student_id):
    attempts = (
        SentenceAttempt.objects
        .filter(student_id=student_id)
        .order_by("-timestamp")
    )

    return render(
        request,
        "content/student_attempts.html",
        {"attempts": attempts, "student_id": student_id},
    )


def content_student_comprehension_progress(request, student_id):
    attempts = (
        ComprehensionAttempt.objects
        .filter(student_id=student_id)
        .order_by("-timestamp")
    )

    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    incorrect = total - correct
    accuracy = round((correct / total * 100), 2) if total else 0

    return render(
        request,
        "content/student_comprehension_progress.html",
        {
            "student_id": student_id,
            "total": total,
            "correct": correct,
            "incorrect": incorrect,
            "accuracy": accuracy,
            "attempts": attempts,
        },
    )


def content_student_writing_progress(request, student_id):
    attempts = (
        SentenceAttempt.objects
        .filter(student_id=student_id)
        .order_by("-timestamp")
    )

    total = attempts.count()
    avg_score = attempts.aggregate(Avg("ai_score"))["ai_score__avg"] or 0

    return render(
        request,
        "content/student_writing_progress.html",
        {
            "student_id": student_id,
            "total": total,
            "avg_score": round(avg_score, 2),
            "attempts": attempts,
        },
    )


def content_student_vocab_progress(request, student_id):
    attempts = (
        VocabularyAttempt.objects
        .filter(student_id=student_id)
        .order_by("-timestamp")
    )

    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    incorrect = total - correct
    accuracy = round((correct / total * 100), 2) if total else 0

    return render(
        request,
        "content/student_vocab_progress.html",
        {
            "student_id": student_id,
            "total": total,
            "correct": correct,
            "incorrect": incorrect,
            "accuracy": accuracy,
            "attempts": attempts,
        },
    )


def content_student_grammar_progress(request, student_id):
    attempts = (
        GrammarAttempt.objects
        .filter(student_id=student_id)
        .order_by("-timestamp")
    )

    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    incorrect = total - correct
    accuracy = round((correct / total * 100), 2) if total else 0

    return render(
        request,
        "content/student_grammar_progress.html",
        {
            "student_id": student_id,
            "total": total,
            "correct": correct,
            "incorrect": incorrect,
            "accuracy": accuracy,
            "attempts": attempts,
        },
    )
