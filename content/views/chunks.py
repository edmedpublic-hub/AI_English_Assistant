import random, re
from django.shortcuts import render, get_object_or_404
from ..models import LessonChunk, Lesson

# -------------------------------
# Core chunk view
# -------------------------------
def chunk_detail(request, pk):
    chunk = get_object_or_404(LessonChunk, pk=pk)
    return render(
        request,
        "content/chunk_detail.html",
        {"chunk": chunk}
    )

# -------------------------------
# Study views
# -------------------------------
def chunk_vocabulary(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)
    return render(request, "content/chunk_vocabulary.html", {"lesson": lesson, "chunk": chunk})

def chunk_grammar(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)
    return render(request, "content/chunk_grammar.html", {"lesson": lesson, "chunk": chunk})

def chunk_comprehension(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)
    return render(request, "content/chunk_comprehension.html", {"lesson": lesson, "chunk": chunk})

def chunk_punctuation(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)
    return render(request, "content/chunk_punctuation.html", {"lesson": lesson, "chunk": chunk})

def chunk_writing(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)
    return render(request, "content/chunk_writing.html", {"lesson": lesson, "chunk": chunk})

def chunk_progress(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)
    return render(request, "content/chunk_progress.html", {"lesson": lesson, "chunk": chunk})

# -------------------------------
# Vocabulary Practice
# -------------------------------
def chunk_vocabulary_practice(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

    vocab_items = list(chunk.vocab_items.all())
    practice_questions = []
    synonym_questions = []
    antonym_questions = []

    # Fill-in-the-blank question (only keep one for now)
    for vocab in vocab_items:
        if vocab.example_sentence:
            # Split into sentences
            sentences = [s.strip() for s in vocab.example_sentence.split('.') if s.strip()]
            if sentences:
                # Take the first sentence only
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
            break   # <-- stop after the first question

        # Synonym question
        if vocab.synonyms:
            syn_list = [s.strip() for s in vocab.synonyms.split(",") if s.strip()]
            if syn_list:
                correct_syn = syn_list[0]
                distractors = [v.word for v in vocab_items if v.id != vocab.id]
                distractors = random.sample(distractors, min(3, len(distractors)))
                options = [correct_syn] + distractors
                random.shuffle(options)

                synonym_questions.append({
                    "sentence": f"The word {vocab.word} appears in this chunk.",
                    "question": "Choose the correct synonym:",
                    "options": options,
                    "answer": correct_syn,
                })

        # Antonym question
        if vocab.antonyms:
            ant_list = [a.strip() for a in vocab.antonyms.split(",") if a.strip()]
            if ant_list:
                correct_ant = ant_list[0]
                distractors = [v.word for v in vocab_items if v.id != vocab.id]
                distractors = random.sample(distractors, min(3, len(distractors)))
                options = [correct_ant] + distractors
                random.shuffle(options)

                antonym_questions.append({
                    "sentence": f"The word {vocab.word} appears in this chunk.",
                    "question": "Choose the correct antonym:",
                    "options": options,
                    "answer": correct_ant,
                })

    return render(request, "content/chunk_vocabulary_practice.html", {
        "lesson": lesson,
        "chunk": chunk,
        "practice_questions": practice_questions,
        "synonym_questions": synonym_questions,
        "antonym_questions": antonym_questions,
    })

# -------------------------------
# Vocabulary Test
# -------------------------------
def chunk_vocabulary_test(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

    vocab_items = list(chunk.vocab_items.all())
    test_questions = []

    for vocab in vocab_items:
        # Simple MCQ: word → choose correct meaning
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