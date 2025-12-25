# ============================================================
# Writing API ViewSets
# ============================================================

from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404, redirect
from ..models import WritingTask, SentenceAttempt
from ..serializers import WritingTaskSerializer, SentenceAttemptSerializer
from ..forms import SentenceAttemptForm


class WritingTaskViewSet(viewsets.ModelViewSet):
    """API endpoint for writing tasks belonging to a lesson."""
    queryset = WritingTask.objects.all()
    serializer_class = WritingTaskSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        lesson_id = self.kwargs.get("lesson_id")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        return qs


class SentenceAttemptViewSet(viewsets.ModelViewSet):
    """API endpoint for student sentence attempts."""
    queryset = SentenceAttempt.objects.all()
    serializer_class = SentenceAttemptSerializer


# ============================================================
# Writing Task Template Views
# ============================================================

def content_writing_task_detail(request, task_id):
    """Show a writing task and allow sentence submission."""
    task = get_object_or_404(WritingTask, id=task_id)

    if request.method == "POST":
        form = SentenceAttemptForm(request.POST)
        if form.is_valid():
            attempt = form.save(commit=False)
            attempt.writing_task = task
            # Naive score (placeholder) — replace with better logic later
            attempt.ai_score = len(attempt.sentence.split())
            attempt.feedback = "Submitted successfully."
            attempt.save()
            return redirect("content:writing-task-detail", task_id=task.id)
    else:
        form = SentenceAttemptForm()

    attempts = SentenceAttempt.objects.filter(writing_task=task).order_by("-timestamp")

    return render(
        request,
        "content/writing_task_detail.html",
        {
            "task": task,
            "form": form,
            "attempts": attempts,
        },
    )