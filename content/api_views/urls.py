# api_views/urls.py

"""
URL routing for all API endpoints.
Organized by domain with nested routers for clean URL structure.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view

# Import all viewsets
from . import (
    core,
    grammar,
    punctuation,
    vocabulary,
    comprehension,
    writing,
    pronunciation,
    testing,
    progress,
    mobile
)

# ============================================================
# MAIN API ROUTER
# ============================================================

# Create main router
router = DefaultRouter()

# ============================================================
# CORE CONTENT ROUTES
# ============================================================

# Textbook routes
router.register(r'textbooks', core.TextbookViewSet, basename='textbook')
router.register(r'units', core.UnitViewSet, basename='unit')
router.register(r'lessons', core.LessonViewSet, basename='lesson')
router.register(r'chunks', core.LessonChunkViewSet, basename='chunk')
router.register(r'search', core.SearchViewSet, basename='search')

# ============================================================
# GRAMMAR ROUTES
# ============================================================

# Knowledge layer
router.register(r'grammar/concepts', grammar.GrammarConceptViewSet, basename='grammar-concept')
router.register(r'grammar/rules', grammar.GrammarRuleViewSet, basename='grammar-rule')
router.register(r'grammar/examples', grammar.GrammarExampleViewSet, basename='grammar-example')

# Teaching layer
router.register(r'grammar/focuses', grammar.ChunkGrammarFocusViewSet, basename='grammar-focus')
router.register(r'grammar/questions', grammar.GrammarQuestionViewSet, basename='grammar-question')

# Practice and test
router.register(r'grammar/practice', grammar.GrammarPracticeViewSet, basename='grammar-practice')
router.register(r'grammar/tests', grammar.GrammarTestViewSet, basename='grammar-test')
router.register(r'grammar/question-attempts', grammar.GrammarQuestionAttemptViewSet, basename='grammar-question-attempt')

# Progress
router.register(r'grammar/progress', grammar.GrammarProgressViewSet, basename='grammar-progress')

# Bulk operations
router.register(r'grammar/bulk', grammar.GrammarBulkOperationViewSet, basename='grammar-bulk')

# ============================================================
# PUNCTUATION ROUTES
# ============================================================

# Knowledge layer
router.register(r'punctuation/marks', punctuation.PunctuationMarkViewSet, basename='punctuation-mark')
router.register(r'punctuation/rules', punctuation.PunctuationRuleViewSet, basename='punctuation-rule')
router.register(r'punctuation/examples', punctuation.PunctuationExampleViewSet, basename='punctuation-example')

# Teaching layer
router.register(r'punctuation/focuses', punctuation.ChunkPunctuationFocusViewSet, basename='punctuation-focus')
router.register(r'punctuation/focus-rules', punctuation.ChunkPunctuationFocusRuleViewSet, basename='punctuation-focus-rule')
router.register(r'punctuation/questions', punctuation.PunctuationQuestionViewSet, basename='punctuation-question')

# Practice and test
router.register(r'punctuation/practice', punctuation.PunctuationPracticeViewSet, basename='punctuation-practice')
router.register(r'punctuation/tests', punctuation.PunctuationTestViewSet, basename='punctuation-test')

# Progress
router.register(r'punctuation/progress', punctuation.PunctuationProgressViewSet, basename='punctuation-progress')

# Bulk operations
router.register(r'punctuation/bulk', punctuation.PunctuationBulkOperationViewSet, basename='punctuation-bulk')

# ============================================================
# VOCABULARY ROUTES
# ============================================================

# Vocabulary items
router.register(r'vocabulary/items', vocabulary.VocabularyItemViewSet, basename='vocabulary-item')

# Practice and mastery
router.register(r'vocabulary/practice', vocabulary.VocabularyPracticeViewSet, basename='vocabulary-practice')
router.register(r'vocabulary/mastery', vocabulary.StudentVocabMasteryViewSet, basename='vocabulary-mastery')

# Progress
router.register(r'vocabulary/progress', vocabulary.VocabularyProgressViewSet, basename='vocabulary-progress')

# Flashcard mode
router.register(r'vocabulary/flashcards', vocabulary.FlashcardViewSet, basename='vocabulary-flashcard')

# Bulk operations
router.register(r'vocabulary/bulk', vocabulary.VocabularyBulkOperationViewSet, basename='vocabulary-bulk')

# ============================================================
# COMPREHENSION ROUTES
# ============================================================

# Teaching layer
router.register(r'comprehension/focuses', comprehension.ChunkComprehensionFocusViewSet, basename='comprehension-focus')
router.register(r'comprehension/questions', comprehension.ComprehensionQuestionViewSet, basename='comprehension-question')

# Practice and test
router.register(r'comprehension/practice', comprehension.ComprehensionPracticeViewSet, basename='comprehension-practice')
router.register(r'comprehension/tests', comprehension.ComprehensionTestViewSet, basename='comprehension-test')
router.register(r'comprehension/question-attempts', comprehension.ComprehensionQuestionAttemptViewSet, basename='comprehension-question-attempt')

# Progress
router.register(r'comprehension/progress', comprehension.ComprehensionProgressViewSet, basename='comprehension-progress')

# Bulk operations
router.register(r'comprehension/bulk', comprehension.ComprehensionBulkOperationViewSet, basename='comprehension-bulk')

# ============================================================
# WRITING ROUTES
# ============================================================

# Teaching layer
router.register(r'writing/chunk-focuses', writing.ChunkWritingFocusViewSet, basename='writing-chunk-focus')
router.register(r'writing/unit-tasks', writing.UnitWritingTaskViewSet, basename='writing-unit-task')
router.register(r'writing/prompts', writing.WritingPromptViewSet, basename='writing-prompt')

# Practice and test
router.register(r'writing/practice', writing.WritingPracticeViewSet, basename='writing-practice')
router.register(r'writing/tests', writing.WritingTestViewSet, basename='writing-test')

# Progress
router.register(r'writing/progress', writing.WritingProgressViewSet, basename='writing-progress')

# Bulk operations
router.register(r'writing/bulk', writing.WritingBulkOperationViewSet, basename='writing-bulk')

# ============================================================
# PRONUNCIATION ROUTES
# ============================================================

# Teaching layer
router.register(r'pronunciation/focuses', pronunciation.PronunciationFocusViewSet, basename='pronunciation-focus')

# Practice and mastery
router.register(r'pronunciation/attempts', pronunciation.PronunciationAttemptViewSet, basename='pronunciation-attempt')
router.register(r'pronunciation/mastery', pronunciation.PronunciationMasteryViewSet, basename='pronunciation-mastery')

# Audio processing
router.register(r'pronunciation/audio', pronunciation.PronunciationAudioViewSet, basename='pronunciation-audio')

# Progress
router.register(r'pronunciation/progress', pronunciation.PronunciationProgressViewSet, basename='pronunciation-progress')

# Bulk operations
router.register(r'pronunciation/bulk', pronunciation.PronunciationBulkOperationViewSet, basename='pronunciation-bulk')

# ============================================================
# TESTING ROUTES
# ============================================================

# Test sessions
router.register(r'testing/sessions', testing.UnitTestSessionViewSet, basename='test-session')
router.register(r'testing/questions', testing.UnitTestQuestionViewSet, basename='test-question')
router.register(r'testing/answers', testing.UnitTestAnswerViewSet, basename='test-answer')

# Progress
router.register(r'testing/progress', testing.UnitTestProgressViewSet, basename='test-progress')

# Test generation
router.register(r'testing/generate', testing.TestGenerationViewSet, basename='test-generate')

# Legacy migration
router.register(r'testing/migrate', testing.LegacyMigrationViewSet, basename='test-migrate')

# ============================================================
# PROGRESS & DASHBOARD ROUTES
# ============================================================

router.register(r'dashboard', progress.DashboardViewSet, basename='dashboard')
router.register(r'progress/units', progress.UnitProgressViewSet, basename='progress-unit')
router.register(r'progress/lessons', progress.LessonProgressViewSet, basename='progress-lesson')
router.register(r'analytics', progress.AnalyticsViewSet, basename='analytics')

# ============================================================
# MOBILE-OPTIMIZED ROUTES
# ============================================================

# Mobile content
router.register(r'mobile/content', mobile.MobileContentViewSet, basename='mobile-content')

# Mobile domain-specific
router.register(r'mobile/grammar', mobile.MobileGrammarViewSet, basename='mobile-grammar')
router.register(r'mobile/punctuation', mobile.MobilePunctuationViewSet, basename='mobile-punctuation')
router.register(r'mobile/vocabulary', mobile.MobileVocabularyViewSet, basename='mobile-vocabulary')
router.register(r'mobile/comprehension', mobile.MobileComprehensionViewSet, basename='mobile-comprehension')
router.register(r'mobile/writing', mobile.MobileWritingViewSet, basename='mobile-writing')
router.register(r'mobile/pronunciation', mobile.MobilePronunciationViewSet, basename='mobile-pronunciation')
router.register(r'mobile/testing', mobile.MobileTestingViewSet, basename='mobile-testing')

# Mobile dashboard
router.register(r'mobile/dashboard', mobile.MobileDashboardViewSet, basename='mobile-dashboard')

# Mobile submissions
router.register(r'mobile/submit', mobile.MobileSubmissionViewSet, basename='mobile-submit')

# Mobile sync and batch
router.register(r'mobile/sync', mobile.MobileSyncViewSet, basename='mobile-sync')
router.register(r'mobile/batch', mobile.MobileBatchViewSet, basename='mobile-batch')

# Mobile notifications
router.register(r'mobile/notifications', mobile.MobileNotificationViewSet, basename='mobile-notification')


# ============================================================
# CUSTOM URL PATTERNS
# ============================================================

# Custom URL patterns for non-standard endpoints
custom_urlpatterns = [
    # Grammar custom endpoints
    path('grammar/concepts/categories/', grammar.GrammarConceptViewSet.as_view({'get': 'categories'}), name='grammar-concept-categories'),
    path('grammar/concepts/progression/', grammar.GrammarConceptViewSet.as_view({'get': 'progression'}), name='grammar-concept-progression'),
    
    # Punctuation custom endpoints
    path('punctuation/marks/by-order/', punctuation.PunctuationMarkViewSet.as_view({'get': 'list'}), name='punctuation-mark-order'),
    
    # Vocabulary custom endpoints
    path('vocabulary/parts-of-speech/', vocabulary.VocabularyItemViewSet.as_view({'get': 'parts_of_speech'}), name='vocabulary-parts-of-speech'),
    path('vocabulary/needs-review/', vocabulary.StudentVocabMasteryViewSet.as_view({'get': 'needs_review'}), name='vocabulary-needs-review'),
    
    # Comprehension custom endpoints
    path('comprehension/bloom-levels/', comprehension.ChunkComprehensionFocusViewSet.as_view({'get': 'bloom_levels'}), name='comprehension-bloom-levels'),
    
    # Writing custom endpoints
    path('writing/stages/', writing.UnitWritingTaskViewSet.as_view({'get': 'stages'}), name='writing-stages'),
    
    # Testing custom endpoints
    path('testing/active-session/', testing.UnitTestSessionViewSet.as_view({'get': 'active'}), name='test-active-session'),
    path('testing/history/', testing.UnitTestSessionViewSet.as_view({'get': 'history'}), name='test-history'),
    path('testing/domain-breakdown/', testing.UnitTestProgressViewSet.as_view({'get': 'domain_breakdown'}), name='test-domain-breakdown'),
    
    # Progress custom endpoints
    path('dashboard/overview/', progress.DashboardViewSet.as_view({'get': 'overview'}), name='dashboard-overview'),
    path('dashboard/summary/', progress.DashboardViewSet.as_view({'get': 'summary'}), name='dashboard-summary'),
    path('progress/unit-detail/', progress.UnitProgressViewSet.as_view({'get': 'detail'}), name='progress-unit-detail'),
    path('progress/lesson-detail/', progress.LessonProgressViewSet.as_view({'get': 'detail'}), name='progress-lesson-detail'),
    
    # Mobile custom endpoints
    path('mobile/dashboard/summary/', mobile.MobileDashboardViewSet.as_view({'get': 'summary'}), name='mobile-dashboard-summary'),
    path('mobile/dashboard/recent/', mobile.MobileDashboardViewSet.as_view({'get': 'recent_activity'}), name='mobile-dashboard-recent'),
    path('mobile/dashboard/recommendations/', mobile.MobileDashboardViewSet.as_view({'get': 'recommendations'}), name='mobile-dashboard-recommendations'),
    path('mobile/dashboard/streak/', mobile.MobileDashboardViewSet.as_view({'get': 'streak'}), name='mobile-dashboard-streak'),
    path('mobile/submit/practice/', mobile.MobileSubmissionViewSet.as_view({'post': 'submit_practice'}), name='mobile-submit-practice'),
    path('mobile/submit/test/', mobile.MobileSubmissionViewSet.as_view({'post': 'submit_test'}), name='mobile-submit-test'),
    path('mobile/sync/status/', mobile.MobileSyncViewSet.as_view({'get': 'status'}), name='mobile-sync-status'),
    path('mobile/notifications/preferences/', mobile.MobileNotificationViewSet.as_view({'get': 'preferences', 'post': 'update_preferences'}), name='mobile-notification-preferences'),
]


# ============================================================
# API INFO ENDPOINT
# ============================================================

@api_view(['GET'])
def get_api_info(request):
    """
    Endpoint to get API information and available routes.
    """
    api_info = {
        'version': '1.0.0',
        'title': 'LMS API',
        'description': 'Complete REST API for Learning Management System',
        'domains': [
            'core', 'grammar', 'punctuation', 'vocabulary',
            'comprehension', 'writing', 'pronunciation', 'testing',
            'progress', 'mobile'
        ],
        'total_endpoints': len(router.urls) + len(custom_urlpatterns)
    }
    return Response(api_info)


# Add API info endpoint to custom patterns
custom_urlpatterns.append(
    path('info/', get_api_info, name='api-info')
)


# ============================================================
# VERSIONED API URLS
# ============================================================

urlpatterns = [
    # API v1 endpoints
    path('v1/', include(router.urls)),
    path('v1/', include(custom_urlpatterns)),
    
    # Root API endpoint (redirects to v1)
    path('', include(router.urls)),
    path('', include(custom_urlpatterns)),
]