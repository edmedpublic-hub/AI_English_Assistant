# ============================================================
# Textbook & Unit API + Template Views
# ============================================================

from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets

from ..models import Textbook, Unit
from ..serializers import TextbookSerializer, UnitSerializer


# ============================================================
# API VIEWSETS
# ============================================================

class TextbookViewSet(viewsets.ModelViewSet):
    """API endpoint for managing textbooks."""
    queryset = Textbook.objects.all().order_by("class_level", "title")
    serializer_class = TextbookSerializer


class UnitViewSet(viewsets.ModelViewSet):
    """
    API endpoint for units.
    Optionally filters by textbook_id when provided in the URL.
    """
    queryset = Unit.objects.all().order_by("number")
    serializer_class = UnitSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        textbook_id = self.kwargs.get("textbook_id")

        if textbook_id:
            queryset = queryset.filter(textbook_id=textbook_id)

        return queryset


# ============================================================
# TEMPLATE VIEWS
# ============================================================

def content_textbook_list(request):
    """Render list of all textbooks."""
    textbooks = Textbook.objects.all().order_by("class_level", "title")
    context = {"textbooks": textbooks}
    return render(request, "content/textbooks_list.html", context)


def content_unit_list(request, textbook_id, student_id=None):
    """Render all units belonging to a specific textbook."""
    textbook = get_object_or_404(Textbook, id=textbook_id)

    units = (
        textbook.units.all()
        .order_by("number")
    )

    context = {
        "textbook": textbook,
        "units": units,
        "student_id": student_id,  # preserved for routing
    }

    return render(request, "content/unit_list.html", context)
