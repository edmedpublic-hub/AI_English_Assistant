from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets

from ..models import Lesson, Unit
from ..serializers import LessonSerializer


# ============================================================
# API VIEWSET
# ============================================================

class LessonViewSet(viewsets.ModelViewSet):
    """
    CRUD API endpoint for Lessons.
    Supports:
    - /api/content/lessons/
    - /api/content/units/<unit_id>/lessons/
    """
    serializer_class = LessonSerializer

    def get_queryset(self):
        queryset = (
            Lesson.objects
            .select_related("unit")
            .order_by("order", "id")
        )

        unit_id = self.kwargs.get("unit_id")
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)

        return queryset


# ============================================================
# TEMPLATE VIEWS
# ============================================================

def content_lesson_list(request, student_id, unit_id):
    unit = get_object_or_404(
        Unit.objects.prefetch_related("lessons"),
        id=unit_id
    )

    lessons = unit.lessons.all().order_by("order", "id")

    return render(
        request,
        "content/lesson_list.html",
        {
            "unit": unit,
            "lessons": lessons,
            "student_id": student_id,
        },
    )


def content_lesson_detail(request, student_id, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.prefetch_related("chunks"),
        id=lesson_id
    )

    chunks = list(lesson.chunks.all().order_by("order", "id"))
    total_chunks = len(chunks)

    try:
        current_idx = int(request.GET.get("chunk", 1))
    except ValueError:
        current_idx = 1

    if total_chunks > 0:
        current_idx = max(1, min(current_idx, total_chunks))
        current_chunk = chunks[current_idx - 1]
    else:
        current_idx = 0
        current_chunk = None

    return render(
        request,
        "content/lesson_detail.html",
        {
            "lesson": lesson,
            "chunk": current_chunk,
            "student_id": student_id,
            "total_chunks": total_chunks,
            "current_chunk": current_idx,
        },
    )
