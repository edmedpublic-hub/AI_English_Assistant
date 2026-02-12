# views/comprehension/practice.py
from rest_framework import generics
from content.models.comprehension import ComprehensionAttempt
from content.serializers.comprehension import ComprehensionAttemptSerializer

class ComprehensionPracticeView(generics.CreateAPIView):
    """
    Record a practice attempt for a comprehension question.
    """
    queryset = ComprehensionAttempt.objects.all()
    serializer_class = ComprehensionAttemptSerializer