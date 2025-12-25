from django.urls import path
# from django.views.decorators.csrf import csrf_exempt  <-- 1. Removed: Not needed for DRF APIView

from .api_views import (
    ReadingLessonListAPIView,
    ReadingLessonDetailAPIView,
    TextFeedbackAPIView,    # <-- 2. Changed from feedback_view to TextFeedbackAPIView
    AudioFeedbackAPIView
)

urlpatterns = [

    # Lessons list
    path("lessons/", ReadingLessonListAPIView.as_view(), name="lesson-list"),

    # Lesson detail
    path("lessons/<int:pk>/", ReadingLessonDetailAPIView.as_view(), name="lesson-detail"),

    # TEXT feedback (Now a DRF APIView, CSRF is handled automatically)
    path("feedback/", TextFeedbackAPIView.as_view(), name="lesson-feedback"),
    #                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ <-- 3. Changed from csrf_exempt(feedback_view) to .as_view()

    # AUDIO feedback
    path("audio-feedback/", AudioFeedbackAPIView.as_view(), name="audio-feedback"),
]