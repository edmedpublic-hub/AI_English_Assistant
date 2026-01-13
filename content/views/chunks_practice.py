import random
import re

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from ..models import LessonChunk, Lesson, VocabularyItem


# ==========================================================
# Utility (kept outside views to avoid NameError issues)
# ==========================================================

def build_questions(vocab_items):
    questions = []

    for vocab in vocab_items:
        if not vocab.meaning:
            continue

        distractors = [
            v.meaning
            for v in vocab_items
            if v.id != vocab.id and v.meaning
        ]

        if not distractors:
            continue

        distractors = random.sample(distractors, min(3, len(distractors)))
        options = [vocab.meaning] + distractors
        random.shuffle(options)

        questions.append({
            "type": "meaning",
            "question": f"What is the meaning of '{vocab.word}'?",
            "options": options,
            "answer": vocab.meaning
        })

    return questions


# ==========================================================
# Dedicated Practice Pages
# ==========================================================

def chunk_vocabulary_practice(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id)

    vocabulary_items = VocabularyItem.objects.filter(chunk=chunk)

    return render(request, "content/chunk_vocabulary_practice.html", {
        "lesson": lesson,
        "chunk": chunk,
        "vocabulary_items": vocabulary_items,
    })


# ==========================================================
# Vocabulary Practice Exercises
# ==========================================================

def chunk_vocab_fill(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

    vocab_items = list(chunk.vocab_items.all())
    practice_questions = []

    for vocab in vocab_items:
        if not vocab.example_sentence:
            continue

        sentences = [s.strip() for s in vocab.example_sentence.split('.') if s.strip()]
        if not sentences:
            continue

        first_sentence = sentences[0]
        pattern = re.compile(re.escape(vocab.word), re.IGNORECASE)
        blank_sentence = pattern.sub("____", first_sentence)

        distractors = [v.word for v in vocab_items if v.id != vocab.id]
        distractors = random.sample(distractors, min(3, len(distractors)))

        options = [vocab.word] + distractors
        random.shuffle(options)

        practice_questions.append({
            "sentence": blank_sentence,
            "options": options,
            "answer": vocab.word,
        })

    return render(request, "content/chunk_vocab_fill.html", {
        "lesson": lesson,
        "chunk": chunk,
        "questions": practice_questions,
    })


def chunk_vocab_synonyms(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

    vocab_items = list(chunk.vocab_items.all())
    questions = []

    for vocab in vocab_items:
        if not vocab.synonyms:
            continue

        syn_list = [s.strip() for s in vocab.synonyms.split(",") if s.strip()]
        if not syn_list:
            continue

        correct = syn_list[0]

        distractor_pool = []
        for other in vocab_items:
            if other.id == vocab.id or not other.synonyms:
                continue

            distractor_pool.extend(
                s.strip()
                for s in other.synonyms.split(",")
                if s.strip()
            )

        if len(distractor_pool) < 3:
            continue

        distractors = random.sample(distractor_pool, 3)
        options = [correct] + distractors
        random.shuffle(options)

        questions.append({
            "sentence": f"The most appropriate synonym of '{vocab.word}' is:",
            "question": "",
            "options": options,
            "answer": correct,
        })

    return render(request, "content/chunk_vocab_synonyms.html", {
        "lesson": lesson,
        "chunk": chunk,
        "questions": questions,
    })


def chunk_vocab_antonyms(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

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
        distractors = random.sample(distractors, min(3, len(distractors)))

        options = [correct] + distractors
        random.shuffle(options)

        questions.append({
            "word": vocab.word,
            "sentence": f"The most appropriate antonym of '{vocab.word}' is:",
            "options": options,
            "answer": correct,
        })

    return render(request, "content/chunk_vocab_antonyms.html", {
        "lesson": lesson,
        "chunk": chunk,
        "questions": questions,
    })


# ==========================================================
# Vocabulary Test
# ==========================================================

def chunk_vocabulary_test(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

    # --- RETAKE RESET ---
    if request.GET.get("retake") == "1":
        request.session.pop("test_data", None)
        return redirect(request.path)

    # --- INITIALIZE TEST ---
    if "test_data" not in request.session:
        vocab_items = list(chunk.vocab_items.all())
        questions = build_questions(vocab_items)

        random.shuffle(questions)

        request.session["test_data"] = {
            "questions": questions,
            "current": 0,
            "score": 0,
            "start_time": timezone.now().isoformat()
        }

    test_data = request.session["test_data"]
    questions = test_data["questions"]
    current_index = test_data["current"]

    # --- FINISHED ---
    if current_index >= len(questions):
        percent = round((test_data["score"] / len(questions)) * 100)

        return render(request, "content/test_result.html", {
            "lesson": lesson,
            "chunk": chunk,
            "score": percent
        })

    current_question = questions[current_index]

    # --- HANDLE SUBMISSION ---
    if request.method == "POST":
        selected = request.POST.get("option")
        if selected == current_question["answer"]:
            test_data["score"] += 1

        test_data["current"] += 1
        request.session.modified = True
        return redirect(request.path)

    return render(request, "content/chunk_vocabulary_test.html", {
        "lesson": lesson,
        "chunk": chunk,
        "question": current_question,
        "question_number": current_index + 1,
        "total": len(questions)
    })
