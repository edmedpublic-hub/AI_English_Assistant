# ============================================================
# Vocabulary API ViewSets
# ============================================================

from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404
from ..models import Lesson, VocabularyItem
from ..serializers import VocabularyItemSerializer


class VocabularyItemViewSet(viewsets.ModelViewSet):
    """API endpoint for vocabulary items belonging to a lesson."""
    queryset = VocabularyItem.objects.all()
    serializer_class = VocabularyItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        lesson_id = self.kwargs.get("lesson_id")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        return qs


# ============================================================
# Vocabulary Template Views
# ============================================================

def content_vocab_list(request, student_id, lesson_id):
    """List all vocabulary items for a given lesson."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    items = VocabularyItem.objects.filter(lesson=lesson)

    context = {
        "lesson": lesson,
        "items": items,
        "student_id": student_id,  # ✅ pass along for navigation links
    }
    return render(request, "content/lesson_vocabulary.html", context)


def content_vocab_item_detail(request, item_id):
    """Detail view for a single vocabulary item."""
    item = get_object_or_404(VocabularyItem, id=item_id)

    context = {
        "item": item,
        "student_id": request.user.username,  # ✅ ensures back links work
    }
    return render(request, "content/vocab_item_detail.html", context)