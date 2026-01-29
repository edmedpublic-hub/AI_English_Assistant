from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET
from ..models import LessonChunk

# -------------------------------
# Helper function
# -------------------------------
def build_chunk_context(chunk_id):
    chunk = get_object_or_404(LessonChunk, id=chunk_id)
    return {
        "chunk": chunk,
        "lesson": chunk.lesson,
        "unit": chunk.lesson.unit,
        "textbook": chunk.lesson.unit.textbook,
    }

# -------------------------------
# Core chunk hub
# -------------------------------
@require_GET
def chunk_hub(request, chunk_id):
    context = build_chunk_context(chunk_id)
    return render(request, "content/chunks/chunk_hub.html", context)

# -------------------------------
# Section views
# -------------------------------
@require_GET
def chunk_vocabulary(request, chunk_id):
    context = build_chunk_context(chunk_id)
    return render(request, "content/vocab/chunk_vocabulary.html", context)

@require_GET
def chunk_grammar(request, chunk_id):
    context = build_chunk_context(chunk_id)
    return render(request, "content/grammar/chunk_grammar.html", context)

@require_GET
def chunk_comprehension(request, chunk_id):
    context = build_chunk_context(chunk_id)
    return render(request, "content/comprehension/chunk_comprehension.html", context)

@require_GET
def chunk_punctuation(request, chunk_id):
    context = build_chunk_context(chunk_id)
    return render(request, "content/punctuation/chunk_punctuation.html", context)

@require_GET
def chunk_writing(request, chunk_id):
    context = build_chunk_context(chunk_id)
    return render(request, "content/writing/chunk_writing.html", context)

@require_GET
def chunk_progress(request, chunk_id):
    context = build_chunk_context(chunk_id)
    return render(request, "content/progress/chunk_progress.html", context)