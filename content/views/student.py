# ============================================================
# Student Progress Views
# ============================================================

from django.shortcuts import render
from django.db.models import Avg
from ..models import SentenceAttempt, VocabularyAttempt, GrammarAttempt, ComprehensionAttempt


def content_student_attempts(request, student_id):
    """Show all sentence attempts for a student."""
    attempts = SentenceAttempt.objects.filter(student_id=student_id).order_by("-timestamp")
    return render(request, "content/student_attempts.html", {
        "attempts": attempts,
        "student_id": student_id
    })


def content_student_comprehension_progress(request, student_id):
    """Show comprehension progress for a student."""
    attempts = ComprehensionAttempt.objects.filter(student_id=student_id)
    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    incorrect = total - correct
    accuracy = (correct / total * 100) if total > 0 else 0

    return render(request, "content/student_comprehension_progress.html", {
        "student_id": student_id,
        "total": total,
        "correct": correct,
        "incorrect": incorrect,   # ✅ added
        "accuracy": round(accuracy, 2),
        "attempts": attempts,
    })


def content_student_writing_progress(request, student_id):
    """Show writing progress for a student."""
    attempts = SentenceAttempt.objects.filter(student_id=student_id)
    total = attempts.count()
    avg_score = attempts.aggregate(Avg("ai_score"))["ai_score__avg"] or 0

    return render(request, "content/student_writing_progress.html", {
        "student_id": student_id,
        "total": total,
        "avg_score": round(avg_score, 2),
        "attempts": attempts,
    })


def content_student_vocab_progress(request, student_id):
    """Show vocabulary progress for a student."""
    attempts = VocabularyAttempt.objects.filter(student_id=student_id)
    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    incorrect = total - correct
    accuracy = (correct / total * 100) if total > 0 else 0

    return render(request, "content/student_vocab_progress.html", {
        "student_id": student_id,
        "total": total,
        "correct": correct,
        "incorrect": incorrect,   # ✅ added
        "accuracy": round(accuracy, 2),
        "attempts": attempts,
    })


def content_student_grammar_progress(request, student_id):
    """Show grammar progress for a student."""
    attempts = GrammarAttempt.objects.filter(student_id=student_id)
    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    incorrect = total - correct
    accuracy = (correct / total * 100) if total > 0 else 0

    return render(request, "content/student_grammar_progress.html", {
        "student_id": student_id,
        "total": total,
        "correct": correct,
        "incorrect": incorrect,   # ✅ added
        "accuracy": round(accuracy, 2),
        "attempts": attempts,
    })