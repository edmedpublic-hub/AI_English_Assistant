from django.shortcuts import render, get_object_or_404
from ..models import Lesson
from ..serializers import LessonSerializer

def lesson_list(request):
    lessons = Lesson.objects.all()
    serializer = LessonSerializer(lessons, many=True)
    return render(
        request,
        "content/main/lesson_list.html",
        {
            "lessons": lessons,
            "lessons_data": serializer.data,
        }
    )

def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    serializer = LessonSerializer(lesson)
    return render(
        request,
        "content/main/lesson_detail.html",
        {
            "lesson": lesson,
            "lesson_data": serializer.data,
        }
    )
