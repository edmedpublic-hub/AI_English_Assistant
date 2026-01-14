from django.shortcuts import render, get_object_or_404, redirect
from ..models import LessonChunk, Lesson, VocabularyTestAttempt
from .test_engine import build_questions


def chunk_vocabulary_test(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

    if request.GET.get("retake") == "1":
        request.session.pop("test_data", None)
        return redirect(request.path)

    if "test_data" not in request.session:
        questions = build_questions(list(chunk.vocab_items.all()))

        if not questions:
            return render(request, "content/chunk_vocabulary_test.html", {
                "lesson": lesson,
                "chunk": chunk,
                "question": {"question": "No valid test questions available.", "options": []},
                "question_number": 0,
                "total": 0
            })

        request.session["test_data"] = {
            "questions": questions,
            "current": 0,
            "score": 0,
        }

    test = request.session["test_data"]
    questions = test["questions"]
    index = test["current"]

    if index >= len(questions):
        total = len(questions)
        correct = test["score"]
        percent = round((correct / total) * 100)

        if not test.get("saved"):
            VocabularyTestAttempt.objects.create(
                user=request.user,
                lesson=lesson,
                chunk=chunk,
                score_percent=percent,
                correct_answers=correct,
                total_questions=total
            )
            test["saved"] = True
            request.session.modified = True

        return render(request, "content/test_result.html", {
            "lesson": lesson,
            "chunk": chunk,
            "score": percent,
            "passed": percent == 100,
            "can_retake": percent < 80,
        })

    current = questions[index]

    if request.method == "POST":
        if request.POST.get("option") == current["answer"]:
            test["score"] += 1
        test["current"] += 1
        request.session.modified = True
        return redirect(request.path)

    return render(request, "content/chunk_vocabulary_test.html", {
        "lesson": lesson,
        "chunk": chunk,
        "question": current,
        "question_number": index + 1,
        "total": len(questions)
    })
