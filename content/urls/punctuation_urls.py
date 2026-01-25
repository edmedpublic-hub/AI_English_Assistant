# content/urls/punctuation.py

from rest_framework.routers import DefaultRouter
from content.views.punctuation_views import (
    PunctuationMarkViewSet,
    ChunkPunctuationFocusViewSet,
    PunctuationQuestionViewSet,
)

router = DefaultRouter()

router.register(r"punctuation/marks", PunctuationMarkViewSet, basename="punctuation-mark")
router.register(r"punctuation/focuses", ChunkPunctuationFocusViewSet, basename="punctuation-focus")
router.register(r"punctuation/questions", PunctuationQuestionViewSet, basename="punctuation-question")

urlpatterns = router.urls