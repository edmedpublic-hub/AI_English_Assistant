# reading/api_views.py

from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt  <-- REMOVE THIS
# from django.utils.decorators import method_decorator   <-- REMOVE THIS

from rest_framework.views import APIView
from rest_framework.response import Response
# JSONParser, MultiPartParser, FormParser are automatically used by APIView,
# but can be left for clarity if needed. We'll use request.data instead.
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser 
from rest_framework import status # Import status for better response codes

from .models import ReadingLesson
from .serializers import ReadingLessonSerializer


# ---------------------------------------------------
# LESSON LIST & DETAIL (No changes needed)
# ---------------------------------------------------
class ReadingLessonListAPIView(APIView):
    # ... (Keep existing code)
    def get(self, request):
        lessons = ReadingLesson.objects.all()
        serializer = ReadingLessonSerializer(lessons, many=True)
        return Response(serializer.data)


class ReadingLessonDetailAPIView(APIView):
    # ... (Keep existing code)
    def get(self, request, pk):
        try:
            lesson = ReadingLesson.objects.get(pk=pk)
        except ReadingLesson.DoesNotExist:
            # Use DRF's status codes for clarity
            return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReadingLessonSerializer(lesson)
        return Response(serializer.data)


# ---------------------------------------------------
# TEXT FEEDBACK — REFACTORED TO DRF APIView
# ---------------------------------------------------
# By using APIView, you no longer need @csrf_exempt
class TextFeedbackAPIView(APIView):
    # DRF automatically handles the request and parses the body into request.data

    def post(self, request):
        """
        Accepts JSON:
        {
            "expected": "...",
            "spoken": "...",
            "lesson_id": 3
        }
        """

        # request.data is already parsed by DRF's JSONParser
        data = request.data 
        
        # Check for necessary fields
        spoken = data.get("spoken", "").strip()

        if not spoken:
            # Use DRF's Response instead of JsonResponse
            return Response(
                {"score": 0, "feedback": "No speech text received."}, 
                status=status.HTTP_400_BAD_REQUEST # Use 400 for bad request data
            )
        
        # You could also access 'expected' and 'lesson_id' here if needed.
        # expected = data.get("expected")
        # lesson_id = data.get("lesson_id")


        # Dummy scoring for now
        score = 70
        feedback = "Good attempt! Keep practicing."

        # 🎯 FIX: Return simulated mispronounced words to activate frontend highlighting
        simulated_mispronounced = [
            # The word key must match the structure expected by reading.feedback.js
            {"word": "attempt", "offset": 10, "duration": 500}, 
            {"word": "practicing", "offset": 30, "duration": 800},
        ]
        # If the input text contains these words, the frontend highlighting should now work!

        return Response({ # Use DRF's Response
            "score": score,
            "feedback": feedback,
            "mispronounced": simulated_mispronounced, # <-- Updated to use simulated data
            "attempt_id": None
        }, status=status.HTTP_200_OK)


# ---------------------------------------------------
# AUDIO FEEDBACK (No changes needed, but added status code)
# ---------------------------------------------------
class AudioFeedbackAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        return Response({
            "error": "Audio processing temporarily disabled. Use text feedback only for now."
        }, status=status.HTTP_501_NOT_IMPLEMENTED) # Use 501 for a feature that isn't ready