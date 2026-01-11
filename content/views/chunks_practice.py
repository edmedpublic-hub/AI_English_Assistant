import random, re
from django.shortcuts import render, get_object_or_404
from ..models import LessonChunk, Lesson, VocabularyItem

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

# -------------------------------
# Vocabulary practice exercises
# -------------------------------
def chunk_vocab_fill(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

    vocab_items = list(chunk.vocab_items.all())
    practice_questions = []

    for vocab in vocab_items:
        if vocab.example_sentence:
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
        if vocab.synonyms:
            syns = [s.strip() for s in vocab.synonyms.split(",") if s.strip()]
            if not syns:
                continue

            correct = syns[0]
            distractors = [v.word for v in vocab_items if v.id != vocab.id]
            distractors = random.sample(distractors, min(3, len(distractors)))
            options = [correct] + distractors
            random.shuffle(options)

            questions.append({
                "word": vocab.word,
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
        if vocab.antonyms:
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
                "options": options,
                "answer": correct,
            })

    return render(request, "content/chunk_vocab_antonyms.html", {
        "lesson": lesson,
        "chunk": chunk,
        "questions": questions,
    })


def chunk_vocabulary_test(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

    vocab_items = list(chunk.vocab_items.all())
    test_questions = []

    for vocab in vocab_items:
        if vocab.meaning:
            distractors = [v.meaning for v in vocab_items if v.id != vocab.id and v.meaning]
            distractors = random.sample(distractors, min(3, len(distractors)))

            options = [vocab.meaning] + distractors
            random.shuffle(options)

            test_questions.append({
                "question": f"What is the meaning of '{vocab.word}'?",
                "options": options,
                "answer": vocab.meaning,
            })

    return render(request, "content/chunk_vocabulary_test.html", {
        "lesson": lesson,
        "chunk": chunk,
        "test_questions": test_questions,
    })