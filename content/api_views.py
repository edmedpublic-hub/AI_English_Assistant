# content/api_views.py
from rest_framework import viewsets
from .models import (
    Textbook,
    Unit,
    Lesson,
    VocabularyItem,
    VocabularyAttempt,
    SentenceAttempt,
    GrammarAttempt,
    ComprehensionAttempt,
    PronunciationAttempt,
)
from .serializers import (
    TextbookSerializer,
    UnitSerializer,
    LessonSerializer,
    VocabularyItemSerializer,
    VocabularyAttemptSerializer,
    SentenceAttemptSerializer,
    GrammarAttemptSerializer,
    ComprehensionAttemptSerializer,
    PronunciationAttemptSerializer,
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

class SentenceAttemptViewSet(viewsets.ModelViewSet):
    queryset = SentenceAttempt.objects.all()
    serializer_class = SentenceAttemptSerializer

class GrammarAttemptViewSet(viewsets.ModelViewSet):
    queryset = GrammarAttempt.objects.all()
    serializer_class = GrammarAttemptSerializer

class ComprehensionAttemptViewSet(viewsets.ModelViewSet):
    queryset = ComprehensionAttempt.objects.all()
    serializer_class = ComprehensionAttemptSerializer

class PronunciationAttemptViewSet(viewsets.ModelViewSet):
    queryset = PronunciationAttempt.objects.all()
    serializer_class = PronunciationAttemptSerializer
