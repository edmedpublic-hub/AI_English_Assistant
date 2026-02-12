# views/comprehension/core.py
from rest_framework import generics
from content.models.comprehension import ChunkComprehensionFocus, ComprehensionQuestion
from content.serializers.comprehension import (
    ChunkComprehensionFocusSerializer,
    ComprehensionQuestionSerializer,
)

class ComprehensionFocusListView(generics.ListAPIView):
    """
    List comprehension focuses for a given chunk.
    """
    serializer_class = ChunkComprehensionFocusSerializer

    def get_queryset(self):
        chunk_id = self.kwargs.get("chunk_id")
        return ChunkComprehensionFocus.objects.filter(chunk_id=chunk_id)


class ComprehensionQuestionListView(generics.ListAPIView):
    """
    List comprehension questions for a given focus.
    """
    serializer_class = ComprehensionQuestionSerializer

    def get_queryset(self):
        focus_id = self.kwargs.get("focus_id")
        return ComprehensionQuestion.objects.filter(focus_id=focus_id)