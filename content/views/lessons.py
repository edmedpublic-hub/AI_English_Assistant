# ============================================================
# Lesson API ViewSets
# ============================================================

from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404
from ..models import Lesson, Unit, LessonChunk
from ..serializers import LessonSerializer


class LessonViewSet(viewsets.ModelViewSet):
    """API endpoint for lessons belonging to a unit."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        unit_id = self.kwargs.get("unit_id")
        if unit_id:
            qs = qs.filter(unit_id=unit_id)
        return qs


# ============================================================
# Lesson Template Views
# ============================================================

def content_lesson_list(request, student_id, unit_id):
    """Show list of lessons for a given unit and student."""
    unit = get_object_or_404(Unit, id=unit_id)
    lessons = unit.lessons.all()
    context = {
        "unit": unit,
        "lessons": lessons,
        "student_id": student_id,  # ✅ ensures templates can link back to dashboard
    }
    return render(request, "content/lesson_list.html", context)


from django.shortcuts import render, get_object_or_404
from ..models import Lesson

def content_lesson_detail(request, student_id, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chunks = list(lesson.chunks.all())
    total = len(chunks)

    # pick current chunk (1-based index)
    current = request.GET.get("chunk")
    try:
        idx = max(1, min(int(current or 1), total))  # clamp between 1 and total
    except ValueError:
        idx = 1

    chunk = chunks[idx - 1] if total > 0 else None

    context = {
        "lesson": lesson,
        "chunk": chunk,
        "student_id": student_id,
        "total_chunks": total,
    }
    return render(request, "content/lesson_detail.html", context)