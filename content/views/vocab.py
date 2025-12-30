# ============================================================
# Vocabulary API + Template Views
# ============================================================

from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets

from ..models import Lesson, VocabularyItem
from ..serializers import VocabularyItemSerializer


# ============================================================
# API VIEWSET
# ============================================================

class VocabularyItemViewSet(viewsets.ModelViewSet):
    """
    CRUD API endpoint for Vocabulary Items.

    Supports both:
    - /api/content/vocabulary/
    - /api/content/lessons/<lesson_id>/vocabulary/
    """
    serializer_class = VocabularyItemSerializer

    queryset = (
        VocabularyItem.objects
        .select_related("lesson")
        .order_by("lesson_id", "id")
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        # Optional nested filtering by lesson
        lesson_id = self.kwargs.get("lesson_id")
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)

        return queryset


# ============================================================
# TEMPLATE VIEWS
# ============================================================

def content_vocab_list(request, student_id, lesson_id):
    """
    Render all vocabulary items for a given lesson.
    """
    lesson = get_object_or_404(
        Lesson.objects.prefetch_related("vocab_items"),
        id=lesson_id
    )

    items = lesson.vocab_items.all()

    context = {
        "lesson": lesson,
        "items": items,
        "student_id": student_id,
    }

    return render(request, "content/lesson_vocabulary.html", context)


def content_vocab_item_detail(request, student_id, item_id):
    """
    Render a single vocabulary item detail page.
    """
    item = get_object_or_404(
        VocabularyItem.objects.select_related("lesson"),
        id=item_id
    )

    context = {
        "item": item,
        "student_id": student_id,
    }

    return render(request, "content/vocab_item_detail.html", context)
