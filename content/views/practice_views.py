import random
import re
from django.shortcuts import render, get_object_or_404
from ..models import LessonChunk, Lesson


def chunk_vocab_fill(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

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
        options = random.sample(distractors, min(3, len(distractors))) + [vocab.word]
        random.shuffle(options)

        questions.append({
            "sentence": blank,
            "options": options,
            "answer": vocab.word
        })

    return render(request, "content/chunk_vocab_fill.html", {
        "lesson": lesson,
        "chunk": chunk,
        "questions": questions,
    })


def chunk_vocab_synonyms(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

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
            "answer": correct
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
        options = random.sample(distractors, min(3, len(distractors))) + [correct]
        random.shuffle(options)

        questions.append({
            "sentence": f"The most appropriate antonym of '{vocab.word}' is:",
            "options": options,
            "answer": correct
        })

    return render(request, "content/chunk_vocab_antonyms.html", {
        "lesson": lesson,
        "chunk": chunk,
        "questions": questions,
    })
