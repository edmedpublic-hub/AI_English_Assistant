from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import VocabularyTestAttempt


@login_required
def test_history(request):
    attempts = (
        VocabularyTestAttempt.objects
        .filter(user=request.user)
        .select_related("lesson", "chunk")
        .order_by("-created_at")
    )

    return render(request, "content/vocab/test_history.html", {
        "attempts": attempts
    })


@login_required
def attempt_detail(request, attempt_id):
    attempt = get_object_or_404(
        VocabularyTestAttempt,
        id=attempt_id,
        user=request.user
    )

    return render(request, "content/vocab/attempt_detail.html", {
        "attempt": attempt,
        "questions": attempt.questions_data or []
    })
