from django.shortcuts import render
from ..chunk_core import build_chunk_context

def chunk_punctuation_view(request, chunk_id):
    context = build_chunk_context(chunk_id)
    # Using your existing template path
    return render(request, "content/chunks/chunk_punctuation.html", context)