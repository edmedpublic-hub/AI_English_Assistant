from django.shortcuts import render, get_object_or_404
from ..models import LessonChunk, Lesson, VocabularyItem


def chunk_vocabulary_practice(request, lesson_id, chunk_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunk = get_object_or_404(LessonChunk, id=chunk_id)

    vocabulary_items = VocabularyItem.objects.filter(chunk=chunk)

    return render(request, "content/vocab/chunk_vocabulary_practice.html", {
        "lesson": lesson,
        "chunk": chunk,
        "vocabulary_items": vocabulary_items,
    })
