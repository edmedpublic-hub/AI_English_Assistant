# ============================================================
# Textbook & Unit API ViewSets
# ============================================================

from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404
from ..models import Textbook, Unit
from ..serializers import TextbookSerializer, UnitSerializer


class TextbookViewSet(viewsets.ModelViewSet):
    """API endpoint for textbooks."""
    queryset = Textbook.objects.all().order_by("class_level", "title")
    serializer_class = TextbookSerializer


class UnitViewSet(viewsets.ModelViewSet):
    """API endpoint for units belonging to a textbook."""
    queryset = Unit.objects.all().order_by("number")
    serializer_class = UnitSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        textbook_id = self.kwargs.get("textbook_id")
        if textbook_id:
            qs = qs.filter(textbook_id=textbook_id)
        return qs


# ============================================================
# Textbook & Unit Template Views
# ============================================================

def content_textbook_list(request):
    """Render a list of all textbooks for students/teachers."""
    textbooks = Textbook.objects.all().order_by("class_level", "title")
    return render(request, "content/textbooks_list.html", {"textbooks": textbooks})


def content_unit_list(request, textbook_id, student_id=None):
    """Render all units belonging to a given textbook."""
    textbook = get_object_or_404(Textbook, id=textbook_id)
    units = textbook.units.all().order_by("number")
    context = {
        "textbook": textbook,
        "units": units,
        "student_id": student_id,  # needed for lesson-list links
    }
    return render(request, "content/unit_list.html", context)