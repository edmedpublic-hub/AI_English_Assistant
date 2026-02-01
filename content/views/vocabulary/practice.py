# content/views/vocabulary/practice.py

import random
import re
from django.shortcuts import render
from django.views.decorators.http import require_GET
from .core import get_vocab_context, _vocab_base_context

@require_GET
def chunk_vocabulary_practice(request, chunk_id):
    """
    General practice hub for a specific chunk.
    """
    chunk, lesson = get_vocab_context(chunk_id)
    vocabulary_items = chunk.vocab_items.all()

    context = _vocab_base_context(chunk, lesson)
    context.update({
        "vocabulary_items": vocabulary_items,
    })
    return render(request, "content/vocab/chunk_vocabulary_practice.html", context)


@require_GET
def chunk_vocab_fill(request, chunk_id):
    """
    Fill-in-the-blank practice mode.
    """
    chunk, lesson = get_vocab_context(chunk_id)
    vocab_items = list(chunk.vocab_items.all())
    questions = []

    for vocab in vocab_items:
        if not vocab.example_sentence:
            continue

        sentences = [s.strip() for s in vocab.example_sentence.split('.') if s.strip()]
        if not sentences:
            continue

        sentence = sentences[0]
        # Replace the word with blanks
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

    context = _vocab_base_context(chunk, lesson)
    context.update({
        "questions": questions,
    })
    return render(request, "content/vocab/chunk_vocab_fill.html", context)


@require_GET
def chunk_vocab_synonyms(request, chunk_id):
    """
    Synonym matching practice mode.
    """
    chunk, lesson = get_vocab_context(chunk_id)
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

        # Build a pool of synonyms from other words to use as distractors
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

    context = _vocab_base_context(chunk, lesson)
    context.update({
        "questions": questions,
    })
    return render(request, "content/vocab/chunk_vocab_synonyms.html", context)


@require_GET
def chunk_vocab_antonyms(request, chunk_id):
    """
    Antonym matching practice mode.
    """
    chunk, lesson = get_vocab_context(chunk_id)
    vocab_items = list(chunk.vocab_items.all())
    questions = []

    for vocab in vocab_items:
        if not vocab.antonyms:
            continue

        ants = [a.strip() for a in vocab.antonyms.split(",") if a.strip()]
        if not ants:
            continue

        correct = ants[0]
        # Use words from the chunk as distractors
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

    context = _vocab_base_context(chunk, lesson)
    context.update({
        "questions": questions,
    })
    return render(request, "content/vocab/chunk_vocab_antonyms.html", context)