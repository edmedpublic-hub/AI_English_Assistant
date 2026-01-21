# content/views/grammar_views.py

from django.shortcuts import render, get_object_or_404
from ..models import Lesson, LessonChunk, GrammarPoint, GrammarQuestion

# -------------------------------
# Grammar: Teach view
# -------------------------------
def grammar_teach(request, lesson_id, chunk_id, point_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)
    point = get_object_or_404(GrammarPoint, id=point_id, chunk=chunk)

    return render(
        request,
        "content/grammar/teach.html",
        {"lesson": lesson, "chunk": chunk, "point": point},
    )

# -------------------------------
# Grammar: Exercise view
# -------------------------------
# content/views/grammar_views.py

from django.shortcuts import render, get_object_or_404, redirect
from ..models import Lesson, LessonChunk, GrammarPoint, GrammarQuestion, GrammarAttempt

# -------------------------------
# Grammar: Exercise view
# -------------------------------
def grammar_exercise(request, lesson_id, chunk_id, point_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)
    point = get_object_or_404(GrammarPoint, id=point_id, chunk=chunk)
    questions = GrammarQuestion.objects.filter(grammar_point=point)

    feedback = []

    if request.method == "POST":
        for q in questions:
            user_answer = request.POST.get(f"q{q.id}")
            if user_answer:
                is_correct = (user_answer.strip().lower() == q.correct_answer.strip().lower())
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

    return render(
        request,
        "content/grammar/exercise.html",
        {
            "lesson": lesson,
            "chunk": chunk,
            "point": point,
            "questions": questions,
            "feedback": feedback,
        },
    )
# -------------------------------
# Grammar: Test view
# -------------------------------
def grammar_test(request, lesson_id, chunk_id, point_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)
    point = get_object_or_404(GrammarPoint, id=point_id, chunk=chunk)
    questions = GrammarQuestion.objects.filter(grammar_point=point)

    return render(
        request,
        "content/grammar/test.html",
        {"lesson": lesson, "chunk": chunk, "point": point, "questions": questions},
    )