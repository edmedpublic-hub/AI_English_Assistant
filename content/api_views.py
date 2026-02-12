# content/api_views.py

from rest_framework import viewsets
from .models import (
    Textbook,
    Unit,
    Lesson,
    VocabularyItem,
    VocabularyAttempt,
    GrammarAttempt,
    ComprehensionAttempt,
    PronunciationAttempt,
    WritingResponse,
    WritingAttempt,
    WritingTestAttempt,
)
from .serializers import (
    TextbookSerializer,
    UnitSerializer,
    LessonSerializer,
    VocabularyItemSerializer,
    VocabularyAttemptSerializer,
    GrammarAttemptSerializer,
    ComprehensionAttemptSerializer,
    PronunciationAttemptSerializer,
    WritingResponseAdminSerializer,
    WritingAttemptAdminSerializer,
    WritingTestAttemptAdminSerializer,
)

# -------------------------------
# Curriculum ViewSets
# -------------------------------
class TextbookViewSet(viewsets.ModelViewSet):
    queryset = Textbook.objects.all()
    serializer_class = TextbookSerializer

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

class VocabularyItemViewSet(viewsets.ModelViewSet):
    queryset = VocabularyItem.objects.all()
    serializer_class = VocabularyItemSerializer

# -------------------------------
# Attempt ViewSets (student activity)
# -------------------------------
class VocabularyAttemptViewSet(viewsets.ModelViewSet):
    queryset = VocabularyAttempt.objects.all()
    serializer_class = VocabularyAttemptSerializer

class GrammarAttemptViewSet(viewsets.ModelViewSet):
    queryset = GrammarAttempt.objects.all()
    serializer_class = GrammarAttemptSerializer

class ComprehensionAttemptViewSet(viewsets.ModelViewSet):
    queryset = ComprehensionAttempt.objects.all()
    serializer_class = ComprehensionAttemptSerializer

class PronunciationAttemptViewSet(viewsets.ModelViewSet):
    queryset = PronunciationAttempt.objects.all()
    serializer_class = PronunciationAttemptSerializer

# -------------------------------
# Writing ViewSets
# -------------------------------
class WritingResponseViewSet(viewsets.ModelViewSet):
    queryset = WritingResponse.objects.all()
    serializer_class = WritingResponseAdminSerializer

class WritingAttemptViewSet(viewsets.ModelViewSet):
    queryset = WritingAttempt.objects.all()
    serializer_class = WritingAttemptAdminSerializer

class WritingTestAttemptViewSet(viewsets.ModelViewSet):
    queryset = WritingTestAttempt.objects.all()
    serializer_class = WritingTestAttemptAdminSerializer