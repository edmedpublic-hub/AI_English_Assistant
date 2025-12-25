# ============================================================
# Comprehension API ViewSets
# ============================================================

from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404
from ..models import ComprehensionQuestion, ComprehensionAttempt
from ..serializers import ComprehensionQuestionSerializer
from ..forms import ComprehensionAttemptForm


class ComprehensionQuestionViewSet(viewsets.ModelViewSet):
    """API endpoint for comprehension questions."""
    queryset = ComprehensionQuestion.objects.all()
    serializer_class = ComprehensionQuestionSerializer


# ============================================================
# Comprehension Template Views
# ============================================================

def content_comprehension_question_detail(request, cq_id):
    """Show a comprehension question and allow student attempts."""
    cq = get_object_or_404(ComprehensionQuestion, id=cq_id)
    feedback = None

    if request.method == "POST":
        form = ComprehensionAttemptForm(request.POST)
        if form.is_valid():
            student_id = form.cleaned_data.get("student_id")
            student_answer = form.cleaned_data["answer"].strip().lower()
            correct_answer = cq.answer.strip().lower()

            is_correct = student_answer == correct_answer

            # Save attempt
            ComprehensionAttempt.objects.create(
                student_id=student_id,
                question=cq,
                answer=form.cleaned_data["answer"],
                is_correct=is_correct,
            )

            feedback = "✅ Correct!" if is_correct else f"❌ Not quite. Correct answer: {cq.answer}"
    else:
        form = ComprehensionAttemptForm()

    attempts = cq.attempts.order_by("-timestamp")

    return render(request, "content/comprehension_question_detail.html", {
        "cq": cq,
        "form": form,
        "feedback": feedback,
        "attempts": attempts,
    })