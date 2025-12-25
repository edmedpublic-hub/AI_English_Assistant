# reading/views.py
from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from .models import ReadingLesson
from .serializers import ReadingLessonSerializer

# --- API views ---
class ReadingLessonListView(generics.ListAPIView):
    queryset = ReadingLesson.objects.all()
    serializer_class = ReadingLessonSerializer

class ReadingLessonDetailView(generics.RetrieveAPIView):
    queryset = ReadingLesson.objects.all()
    serializer_class = ReadingLessonSerializer
    lookup_field = "pk"

# --- Template views ---
def reading_home(request):
    """Render the lesson list page (templates/reading/reading.html)."""
    return render(request, "reading/reading.html")

def reading_detail(request, pk):
    """Render a single lesson detail page (templates/reading/reading_detail.html)."""
    lesson = get_object_or_404(ReadingLesson, pk=pk)
    return render(request, "reading/reading_detail.html", {"lesson": lesson})
