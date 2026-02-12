# views/comprehension/test.py
from rest_framework import generics
from content.models.comprehension import ComprehensionAttempt
from content.serializers.comprehension import ComprehensionAttemptSerializer

class ComprehensionTestResultsView(generics.ListAPIView):
    """
    List comprehension attempts for a student (test results).
    """
    serializer_class = ComprehensionAttemptSerializer

    def get_queryset(self):
        student_id = self.kwargs.get("student_id")
        return ComprehensionAttempt.objects.filter(student_id=student_id)