from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET
from ..models import Textbook, Unit, Lesson

# -----------------------------
# Index
# -----------------------------
@require_GET
def content_index(request):
    return render(request, "content/main/index.html")

# -----------------------------
# Textbook views
# -----------------------------
@require_GET
def textbook_list(request):
    textbooks = Textbook.objects.all()
    return render(request, "content/main/textbook_list.html", {"textbooks": textbooks})

@require_GET
def textbook_detail(request, pk):
    textbook = get_object_or_404(Textbook, pk=pk)
    units = textbook.units.all()
    return render(request, "content/main/textbook_detail.html", {"textbook": textbook, "units": units})

# -----------------------------
# Unit views
# -----------------------------
@require_GET
def unit_detail(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    lessons = unit.lessons.all()
    return render(request, "content/main/unit_detail.html", {"unit": unit, "lessons": lessons})

# -----------------------------
# Lesson views
# -----------------------------
@require_GET
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    chunks = lesson.chunks.all()
    return render(request, "content/main/lesson_detail.html", {"lesson": lesson, "chunks": chunks})