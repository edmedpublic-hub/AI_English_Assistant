import random
import re

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from ..models import LessonChunk, VocabularyTestAttempt
from .test_engine import build_questions

# -----------------------------
# Vocabulary Fill-in-the-Blank
# -----------------------------
@require_GET
def chunk_vocab_fill(request, chunk_id):
    chunk = get_object_or_404(LessonChunk.objects.select_related("lesson"), id=chunk_id)
    lesson = chunk.lesson

    vocab_items = list(chunk.vocab_items.all())
    questions = []

    for vocab in vocab_items:
        if not vocab.example_sentence:
            continue

        sentences = [s.strip() for s in vocab.example_sentence.split('.') if s.strip()]
        if not sentences:
            continue

        sentence = sentences[0]
        blank = re.sub(re.escape(vocab.word), "____", sentence, flags=re.IGNORECASE)

        distractors = [v.word for v in vocab_items if v.id != vocab.id]
        if not distractors:
            continue

        options = random.sample(distractors, min(3, len(distractors))) + [vocab.word]
        random.shuffle(options)

        questions.append({
            "sentence": blank,
            "options": options,
            "answer": vocab.word,
        })

    return render(request, "content/vocab/chunk_vocab_fill.html", {
        "lesson": lesson,
        "chunk": chunk,
        "questions": questions,
    })


# -----------------------------
# Vocabulary Synonyms
# -----------------------------
@require_GET
def chunk_vocab_synonyms(request, chunk_id):
    chunk = get_object_or_404(LessonChunk.objects.select_related("lesson"), id=chunk_id)
    lesson = chunk.lesson

    vocab_items = list(chunk.vocab_items.all())
    questions = []

    for vocab in vocab_items:
        if not vocab.synonyms:
            continue

        syns = [s.strip() for s in vocab.synonyms.split(",") if s.strip()]
        if not syns:
            continue

        correct = syns[0]
        pool = []

        for other in vocab_items:
            if other.id == vocab.id or not other.synonyms:
                continue
            pool.extend(s.strip() for s in other.synonyms.split(",") if s.strip())

        if len(pool) < 3:
            continue

        options = random.sample(pool, 3) + [correct]
        random.shuffle(options)

        questions.append({
            "sentence": f"The most appropriate synonym of '{vocab.word}' is:",
            "options": options,
            "answer": correct,
        })

    return render(request, "content/vocab/chunk_vocab_synonyms.html", {
        "lesson": lesson,
        "chunk": chunk,
        "questions": questions,
    })


# -----------------------------
# Vocabulary Antonyms
# -----------------------------
@require_GET
def chunk_vocab_antonyms(request, chunk_id):
    chunk = get_object_or_404(LessonChunk.objects.select_related("lesson"), id=chunk_id)
    lesson = chunk.lesson

    vocab_items = list(chunk.vocab_items.all())
    questions = []

    for vocab in vocab_items:
        if not vocab.antonyms:
            continue

        ants = [a.strip() for a in vocab.antonyms.split(",") if a.strip()]
        if not ants:
            continue

        correct = ants[0]
        distractors = [v.word for v in vocab_items if v.id != vocab.id]
        if not distractors:
            continue

        options = random.sample(distractors, min(3, len(distractors))) + [correct]
        random.shuffle(options)

        questions.append({
            "sentence": f"The most appropriate antonym of '{vocab.word}' is:",
            "options": options,
            "answer": correct,
        })

    return render(request, "content/vocab/chunk_vocab_antonyms.html", {
        "lesson": lesson,
        "chunk": chunk,
        "questions": questions,
    })


# -----------------------------
# Vocabulary Practice
# -----------------------------
@require_GET
def chunk_vocabulary_practice(request, chunk_id):
    chunk = get_object_or_404(LessonChunk.objects.select_related("lesson"), id=chunk_id)
    lesson = chunk.lesson
    vocabulary_items = chunk.vocab_items.all()

    return render(request, "content/vocab/chunk_vocabulary_practice.html", {
        "lesson": lesson,
        "chunk": chunk,
        "vocabulary_items": vocabulary_items,
    })


# -----------------------------
# Vocabulary Test
# -----------------------------
def chunk_vocabulary_test(request, chunk_id):
    chunk = get_object_or_404(LessonChunk.objects.select_related("lesson"), id=chunk_id)
    lesson = chunk.lesson

    if request.GET.get("retake") == "1":
        request.session.pop("test_data", None)
        return redirect(request.path)

    if "test_data" not in request.session:
        questions = build_questions(list(chunk.vocab_items.all()))

        if not questions:
            return render(request, "content/vocab/chunk_vocabulary_test.html", {
                "lesson": lesson,
                "chunk": chunk,
                "question": {"question": "No valid test questions available.", "options": []},
                "question_number": 0,
                "total": 0,
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
                total_questions=total,
                questions_data=test["questions"],
            )
            test["saved"] = True
            request.session.modified = True

        return render(request, "content/vocab/test_result.html", {
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

    return render(request, "content/vocab/chunk_vocabulary_test.html", {
        "lesson": lesson,
        "chunk": chunk,
        "question": current,
        "question_number": index + 1,
        "total": len(questions),
    })


# -----------------------------
# Test History
# -----------------------------
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