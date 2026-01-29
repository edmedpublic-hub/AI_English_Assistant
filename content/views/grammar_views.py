from django.shortcuts import render, get_object_or_404, redirect
from ..models import LessonChunk, GrammarQuestion, GrammarAttempt


def _chunk_context(chunk):
    """Shared navigation context for all grammar views."""
    return {
        "chunk": chunk,
        "lesson": chunk.lesson,
        "unit": chunk.lesson.unit,
        "textbook": chunk.lesson.unit.textbook,
    }


# -------------------------------
# Grammar: Teach view
# -------------------------------
def grammar_teach(request, chunk_id, point_id):
    chunk = get_object_or_404(LessonChunk, id=chunk_id)

    context = _chunk_context(chunk)
    context["point_id"] = point_id  # placeholder for now

    return render(request, "content/grammar/teach.html", context)


# -------------------------------
# Grammar: Exercise view
# -------------------------------
def grammar_exercise(request, chunk_id, point_id):
    chunk = get_object_or_404(LessonChunk, id=chunk_id)

    context = _chunk_context(chunk)
    context["point_id"] = point_id

    feedback = []

    # NOTE: You will later plug real question filtering here
    questions = GrammarQuestion.objects.filter(chunk=chunk)

    if request.method == "POST":
        for q in questions:
            user_answer = request.POST.get(f"q{q.id}")
            if user_answer:
                is_correct = (
                    user_answer.strip().lower()
                    == q.correct_answer.strip().lower()
                )

                GrammarAttempt.objects.create(
                    student=request.user,
                    grammar_question=q,
                    selected_answer=user_answer,
                    is_correct=is_correct,
                )

                feedback.append({
                    "question": q.question_text,
                    "your_answer": user_answer,
                    "correct_answer": q.correct_answer,
                    "is_correct": is_correct,
                })

    context["questions"] = questions
    context["feedback"] = feedback

    return render(request, "content/grammar/exercise.html", context)


# -------------------------------
# Grammar: Test view
# -------------------------------
def grammar_test(request, chunk_id, point_id):
    chunk = get_object_or_404(LessonChunk, id=chunk_id)

    context = _chunk_context(chunk)
    context["point_id"] = point_id

    return render(request, "content/grammar/test.html", context)