# ============================================================
# Home & Student Dashboard Views
# ============================================================

from django.shortcuts import render
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate

from ..models import (
    Textbook,
    Unit,
    Lesson,
    VocabularyItem,
    SentenceAttempt,
    ComprehensionAttempt,
    VocabularyAttempt,
    GrammarAttempt,
)

def content_home(request):
    # Prefetch related units, lessons, and vocabulary items for hierarchy
    textbooks = Textbook.objects.prefetch_related(
        "units__lessons__vocab_items"
    )

    context = {
        "textbooks": textbooks,
        "student_id": request.user.username,  # needed for lesson-detail URLs
    }
    return render(request, "content/content_home.html", context)





def content_student_dashboard(request, student_id):
    """Unified dashboard showing a student's progress across modules."""

    # --- Writing progress ---
    writing_attempts = SentenceAttempt.objects.filter(student_id=student_id)
    writing_total = writing_attempts.count()
    writing_avg = writing_attempts.aggregate(Avg("ai_score"))["ai_score__avg"] or 0

    # --- Comprehension progress ---
    comprehension_attempts = ComprehensionAttempt.objects.filter(student_id=student_id)
    comp_total = comprehension_attempts.count()
    comp_correct = comprehension_attempts.filter(is_correct=True).count()
    comp_accuracy = (comp_correct / comp_total * 100) if comp_total > 0 else 0

    # --- Vocabulary progress ---
    vocab_attempts = VocabularyAttempt.objects.filter(student_id=student_id)
    vocab_total = vocab_attempts.count()
    vocab_correct = vocab_attempts.filter(is_correct=True).count()
    vocab_accuracy = (vocab_correct / vocab_total * 100) if vocab_total > 0 else 0

    # --- Grammar progress ---
    grammar_attempts = GrammarAttempt.objects.filter(student_id=student_id)
    grammar_total = grammar_attempts.count()
    grammar_correct = grammar_attempts.filter(is_correct=True).count()
    grammar_accuracy = (grammar_correct / grammar_total * 100) if grammar_total > 0 else 0

    # --- Trend Data for Charts ---
    writing_trend = (
        writing_attempts.annotate(day=TruncDate("timestamp"))
        .values("day")
        .annotate(avg_score=Avg("ai_score"))
        .order_by("day")
    )

    comprehension_trend = (
        comprehension_attempts.annotate(day=TruncDate("timestamp"))
        .values("day")
        .annotate(
            total=Count("id"),
            correct=Count("id", filter=Q(is_correct=True))
        )
        .order_by("day")
    )

    vocab_trend = (
        vocab_attempts.annotate(day=TruncDate("timestamp"))
        .values("day")
        .annotate(
            total=Count("id"),
            correct=Count("id", filter=Q(is_correct=True))
        )
        .order_by("day")
    )

    grammar_trend = (
        grammar_attempts.annotate(day=TruncDate("timestamp"))
        .values("day")
        .annotate(
            total=Count("id"),
            correct=Count("id", filter=Q(is_correct=True))
        )
        .order_by("day")
    )

    return render(request, "content/student_dashboard.html", {
        "student_id": student_id,

        # --- Totals & Averages ---
        "writing_total": writing_total,
        "writing_avg": round(writing_avg, 2),
        "comprehension_total": comp_total,
        "comprehension_correct": comp_correct,
        "comprehension_accuracy": round(comp_accuracy, 2),
        "vocab_total": vocab_total,
        "vocab_correct": vocab_correct,
        "vocab_accuracy": round(vocab_accuracy, 2),
        "grammar_total": grammar_total,
        "grammar_correct": grammar_correct,
        "grammar_accuracy": round(grammar_accuracy, 2),

        # --- Recent Attempts ---
        "writing_attempts": writing_attempts[:5],
        "comprehension_attempts": comprehension_attempts[:5],
        "vocab_attempts": vocab_attempts[:5],
        "grammar_attempts": grammar_attempts[:5],

        # --- Trend Data for Charts ---
        "writing_trend": list(writing_trend),
        "comprehension_trend": list(comprehension_trend),
        "vocab_trend": list(vocab_trend),
        "grammar_trend": list(grammar_trend),
    })