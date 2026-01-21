import random, re
from django.shortcuts import render, get_object_or_404
from ..models import LessonChunk, Lesson, GrammarPoint

# -------------------------------
# Core chunk view
# -------------------------------
def chunk_detail(request, pk):
    chunk = get_object_or_404(LessonChunk, pk=pk)
    return render(request, "content/chunk_detail.html", {"chunk": chunk})

# -------------------------------
# Study views
# -------------------------------
def chunk_vocabulary(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)
    return render(request, "content/vocab/chunk_vocabulary.html", {"lesson": lesson, "chunk": chunk})

# chunk_core.py

def chunk_grammar(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id, lesson=lesson)

    grammar_points = GrammarPoint.objects.filter(chunk=chunk)

    return render(
        request,
        "content/grammar/chunk_grammar.html",
        {
            "lesson": lesson,
            "chunk": chunk,
            "grammar_points": grammar_points,
        },
    )

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