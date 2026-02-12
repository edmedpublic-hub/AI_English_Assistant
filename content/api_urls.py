# content/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()

# Curriculum endpoints
router.register(r'textbooks', api_views.TextbookViewSet, basename='textbook')
router.register(r'units', api_views.UnitViewSet, basename='unit')
router.register(r'lessons', api_views.LessonViewSet, basename='lesson')
router.register(r'vocab', api_views.VocabularyItemViewSet, basename='vocab')

# Attempt endpoints (student activity)
router.register(r'vocab-attempts', api_views.VocabularyAttemptViewSet, basename='vocab-attempt')
router.register(r'grammar-attempts', api_views.GrammarAttemptViewSet, basename='grammar-attempt')
router.register(r'comprehension-attempts', api_views.ComprehensionAttemptViewSet, basename='comprehension-attempt')
router.register(r'pronunciation-attempts', api_views.PronunciationAttemptViewSet, basename='pronunciation-attempt')

# Writing endpoints (new)
router.register(r'writing-responses', api_views.WritingResponseViewSet, basename='writing-response')
router.register(r'writing-attempts', api_views.WritingAttemptViewSet, basename='writing-attempt')
router.register(r'writing-test-attempts', api_views.WritingTestAttemptViewSet, basename='writing-test-attempt')

urlpatterns = [
    path('', include(router.urls)),
]