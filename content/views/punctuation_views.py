# content/views/punctuation_views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from content.models.punctuation import (
    PunctuationMark,
    ChunkPunctuationFocus,
    PunctuationQuestion,
    PunctuationAttempt,
    PunctuationTestAttempt,
)

from content.serializers.punctuation import (
    PunctuationMarkSerializer,
    ChunkPunctuationFocusSerializer,
    PunctuationQuestionSerializer,
    PunctuationAttemptSerializer,
    PunctuationTestAttemptSerializer,
)


# --------------------------------------------------
# Placeholder ViewSets (no logic yet)
# --------------------------------------------------

class PunctuationMarkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PunctuationMark.objects.all()
    serializer_class = PunctuationMarkSerializer


class ChunkPunctuationFocusViewSet(viewsets.ModelViewSet):
    queryset = ChunkPunctuationFocus.objects.all()
    serializer_class = ChunkPunctuationFocusSerializer
    permission_classes = [IsAuthenticated]


class PunctuationQuestionViewSet(viewsets.ModelViewSet):
    queryset = PunctuationQuestion.objects.all()
    serializer_class = PunctuationQuestionSerializer
    permission_classes = [IsAuthenticated]