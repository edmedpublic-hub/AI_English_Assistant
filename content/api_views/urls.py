# content/api_views/urls.py

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
    mobile,
)

# ============================================================
# MAIN API ROUTER
# ============================================================

router = DefaultRouter()

# ============================================================
# CORE CONTENT ROUTES
# ============================================================

router.register(r'textbooks', core.TextbookViewSet,     basename='textbook')
router.register(r'units',     core.UnitViewSet,         basename='unit')
router.register(r'lessons',   core.LessonViewSet,        basename='lesson')
router.register(r'chunks',    core.LessonChunkViewSet,   basename='chunk')
router.register(r'search',    core.SearchViewSet,        basename='search')

# ============================================================
# GRAMMAR ROUTES
# ============================================================

router.register(r'grammar/concepts',          grammar.GrammarConceptViewSet,          basename='grammar-concept')
router.register(r'grammar/rules',             grammar.GrammarRuleViewSet,             basename='grammar-rule')
router.register(r'grammar/examples',          grammar.GrammarExampleViewSet,          basename='grammar-example')
router.register(r'grammar/focuses',           grammar.ChunkGrammarFocusViewSet,       basename='grammar-focus')
router.register(r'grammar/questions',         grammar.GrammarQuestionViewSet,         basename='grammar-question')
router.register(r'grammar/practice',          grammar.GrammarPracticeViewSet,         basename='grammar-practice')
router.register(r'grammar/tests',             grammar.GrammarTestViewSet,             basename='grammar-test')
router.register(r'grammar/question-attempts', grammar.GrammarQuestionAttemptViewSet,  basename='grammar-question-attempt')
router.register(r'grammar/progress',          grammar.GrammarProgressViewSet,         basename='grammar-progress')
router.register(r'grammar/bulk',              grammar.GrammarBulkOperationViewSet,    basename='grammar-bulk')

# ============================================================
# PUNCTUATION ROUTES
# ============================================================

router.register(r'punctuation/marks',        punctuation.PunctuationMarkViewSet,             basename='punctuation-mark')
router.register(r'punctuation/rules',        punctuation.PunctuationRuleViewSet,             basename='punctuation-rule')
router.register(r'punctuation/examples',     punctuation.PunctuationExampleViewSet,          basename='punctuation-example')
router.register(r'punctuation/focuses',      punctuation.ChunkPunctuationFocusViewSet,       basename='punctuation-focus')
router.register(r'punctuation/focus-rules',  punctuation.ChunkPunctuationFocusRuleViewSet,   basename='punctuation-focus-rule')
router.register(r'punctuation/questions',    punctuation.PunctuationQuestionViewSet,         basename='punctuation-question')
router.register(r'punctuation/practice',     punctuation.PunctuationPracticeViewSet,         basename='punctuation-practice')
router.register(r'punctuation/tests',        punctuation.PunctuationTestViewSet,             basename='punctuation-test')
router.register(r'punctuation/progress',     punctuation.PunctuationProgressViewSet,         basename='punctuation-progress')
router.register(r'punctuation/bulk',         punctuation.PunctuationBulkOperationViewSet,    basename='punctuation-bulk')

# ============================================================
# VOCABULARY ROUTES
# ============================================================

router.register(r'vocabulary/items',       vocabulary.VocabularyItemViewSet,         basename='vocabulary-item')
router.register(r'vocabulary/practice',    vocabulary.VocabularyPracticeViewSet,     basename='vocabulary-practice')
router.register(r'vocabulary/mastery',     vocabulary.StudentVocabMasteryViewSet,    basename='vocabulary-mastery')
router.register(r'vocabulary/progress',    vocabulary.VocabularyProgressViewSet,     basename='vocabulary-progress')
router.register(r'vocabulary/flashcards',  vocabulary.FlashcardViewSet,              basename='vocabulary-flashcard')
router.register(r'vocabulary/bulk',        vocabulary.VocabularyBulkOperationViewSet, basename='vocabulary-bulk')

# ============================================================
# COMPREHENSION ROUTES
# ============================================================

router.register(r'comprehension/focuses',           comprehension.ChunkComprehensionFocusViewSet,       basename='comprehension-focus')
router.register(r'comprehension/questions',          comprehension.ComprehensionQuestionViewSet,         basename='comprehension-question')
router.register(r'comprehension/practice',           comprehension.ComprehensionPracticeViewSet,         basename='comprehension-practice')
router.register(r'comprehension/tests',              comprehension.ComprehensionTestViewSet,             basename='comprehension-test')
router.register(r'comprehension/question-attempts',  comprehension.ComprehensionQuestionAttemptViewSet,  basename='comprehension-question-attempt')
router.register(r'comprehension/progress',           comprehension.ComprehensionProgressViewSet,         basename='comprehension-progress')
router.register(r'comprehension/bulk',               comprehension.ComprehensionBulkOperationViewSet,    basename='comprehension-bulk')

# ============================================================
# WRITING ROUTES
# New three-tier architecture.
# Old routes (chunk-focuses, unit-tasks, prompts) are replaced
# with stage-based routes.
# ============================================================

# Academic year — system configuration
router.register(
    r'writing/academic-years',
    writing.WritingAcademicYearViewSet,
    basename='writing-academic-year',
)

# Stages — read-only, seeded via migration
router.register(
    r'writing/stages',
    writing.WritingStageViewSet,
    basename='writing-stage',
)

# Stage content — admin enters per stage per unit
router.register(
    r'writing/content',
    writing.WritingStageContentViewSet,
    basename='writing-content',
)

# Attempts — student submissions
router.register(
    r'writing/attempts',
    writing.WritingAttemptViewSet,
    basename='writing-attempt',
)

# Mastery — read-only records
router.register(
    r'writing/mastery',
    writing.WritingStageMasteryViewSet,
    basename='writing-mastery',
)

# Interventions — sentence-level fix exercises
router.register(
    r'writing/interventions',
    writing.WritingInterventionViewSet,
    basename='writing-intervention',
)

# Progress
router.register(
    r'writing/progress',
    writing.WritingProgressViewSet,
    basename='writing-progress',
)

# ============================================================
# PRONUNCIATION ROUTES
# ============================================================

router.register(r'pronunciation/focuses',   pronunciation.PronunciationFocusViewSet,        basename='pronunciation-focus')
router.register(r'pronunciation/attempts',  pronunciation.PronunciationAttemptViewSet,      basename='pronunciation-attempt')
router.register(r'pronunciation/mastery',   pronunciation.PronunciationMasteryViewSet,      basename='pronunciation-mastery')
router.register(r'pronunciation/audio',     pronunciation.PronunciationAudioViewSet,        basename='pronunciation-audio')
router.register(r'pronunciation/progress',  pronunciation.PronunciationProgressViewSet,     basename='pronunciation-progress')
router.register(r'pronunciation/bulk',      pronunciation.PronunciationBulkOperationViewSet, basename='pronunciation-bulk')

# ============================================================
# TESTING ROUTES
# ============================================================

router.register(r'testing/sessions',   testing.UnitTestSessionViewSet,  basename='test-session')
router.register(r'testing/questions',  testing.UnitTestQuestionViewSet, basename='test-question')
router.register(r'testing/answers',    testing.UnitTestAnswerViewSet,   basename='test-answer')
router.register(r'testing/progress',   testing.UnitTestProgressViewSet, basename='test-progress')
router.register(r'testing/generate',   testing.TestGenerationViewSet,   basename='test-generate')
router.register(r'testing/migrate',    testing.LegacyMigrationViewSet,  basename='test-migrate')

# ============================================================
# PROGRESS & DASHBOARD ROUTES
# ============================================================

router.register(r'dashboard',        progress.DashboardViewSet,      basename='dashboard')
router.register(r'progress/units',   progress.UnitProgressViewSet,   basename='progress-unit')
router.register(r'progress/lessons', progress.LessonProgressViewSet, basename='progress-lesson')
router.register(r'analytics',        progress.AnalyticsViewSet,      basename='analytics')

# ============================================================
# MOBILE-OPTIMIZED ROUTES
# ============================================================

router.register(r'mobile/content',       mobile.MobileContentViewSet,      basename='mobile-content')
router.register(r'mobile/grammar',       mobile.MobileGrammarViewSet,       basename='mobile-grammar')
router.register(r'mobile/punctuation',   mobile.MobilePunctuationViewSet,   basename='mobile-punctuation')
router.register(r'mobile/vocabulary',    mobile.MobileVocabularyViewSet,    basename='mobile-vocabulary')
router.register(r'mobile/comprehension', mobile.MobileComprehensionViewSet, basename='mobile-comprehension')
router.register(r'mobile/writing',       mobile.MobileWritingViewSet,       basename='mobile-writing')
router.register(r'mobile/pronunciation', mobile.MobilePronunciationViewSet, basename='mobile-pronunciation')
router.register(r'mobile/testing',       mobile.MobileTestingViewSet,       basename='mobile-testing')
router.register(r'mobile/dashboard',     mobile.MobileDashboardViewSet,     basename='mobile-dashboard')
router.register(r'mobile/submit',        mobile.MobileSubmissionViewSet,    basename='mobile-submit')
router.register(r'mobile/sync',          mobile.MobileSyncViewSet,          basename='mobile-sync')
router.register(r'mobile/batch',         mobile.MobileBatchViewSet,         basename='mobile-batch')
router.register(r'mobile/notifications', mobile.MobileNotificationViewSet,  basename='mobile-notification')


# ============================================================
# CUSTOM URL PATTERNS
# ============================================================

custom_urlpatterns = [
    # Grammar
    path(
        'grammar/concepts/categories/',
        grammar.GrammarConceptViewSet.as_view({'get': 'categories'}),
        name='grammar-concept-categories',
    ),
    path(
        'grammar/concepts/progression/',
        grammar.GrammarConceptViewSet.as_view({'get': 'progression'}),
        name='grammar-concept-progression',
    ),

    # Punctuation
    path(
        'punctuation/marks/by-order/',
        punctuation.PunctuationMarkViewSet.as_view({'get': 'list'}),
        name='punctuation-mark-order',
    ),

    # Vocabulary
    path(
        'vocabulary/parts-of-speech/',
        vocabulary.VocabularyItemViewSet.as_view({'get': 'parts_of_speech'}),
        name='vocabulary-parts-of-speech',
    ),
    path(
        'vocabulary/needs-review/',
        vocabulary.StudentVocabMasteryViewSet.as_view({'get': 'needs_review'}),
        name='vocabulary-needs-review',
    ),

    # Comprehension
    path(
        'comprehension/bloom-levels/',
        comprehension.ChunkComprehensionFocusViewSet.as_view({'get': 'bloom_levels'}),
        name='comprehension-bloom-levels',
    ),

    # Writing — new three-tier architecture
    path(
        'writing/hub/<int:unit_id>/',
        writing.WritingStageContentViewSet.as_view({'get': 'hub'}),
        name='writing-hub',
    ),
    path(
        'writing/submit/',
        writing.WritingAttemptViewSet.as_view({'post': 'submit'}),
        name='writing-submit',
    ),
    path(
        'writing/interventions/<int:pk>/fix/',
        writing.WritingInterventionViewSet.as_view({'post': 'fix'}),
        name='writing-intervention-fix',
    ),

    # Testing
    path(
        'testing/active-session/',
        testing.UnitTestSessionViewSet.as_view({'get': 'active'}),
        name='test-active-session',
    ),
    path(
        'testing/history/',
        testing.UnitTestSessionViewSet.as_view({'get': 'history'}),
        name='test-history',
    ),
    path(
        'testing/domain-breakdown/',
        testing.UnitTestProgressViewSet.as_view({'get': 'domain_breakdown'}),
        name='test-domain-breakdown',
    ),

    # Progress
    path(
        'dashboard/overview/',
        progress.DashboardViewSet.as_view({'get': 'overview'}),
        name='dashboard-overview',
    ),
    path(
        'dashboard/summary/',
        progress.DashboardViewSet.as_view({'get': 'summary'}),
        name='dashboard-summary',
    ),
    path(
        'progress/unit-detail/',
        progress.UnitProgressViewSet.as_view({'get': 'detail'}),
        name='progress-unit-detail',
    ),
    path(
        'progress/lesson-detail/',
        progress.LessonProgressViewSet.as_view({'get': 'detail'}),
        name='progress-lesson-detail',
    ),

    # Mobile
    path(
        'mobile/dashboard/summary/',
        mobile.MobileDashboardViewSet.as_view({'get': 'summary'}),
        name='mobile-dashboard-summary',
    ),
    path(
        'mobile/dashboard/recent/',
        mobile.MobileDashboardViewSet.as_view({'get': 'recent_activity'}),
        name='mobile-dashboard-recent',
    ),
    path(
        'mobile/dashboard/recommendations/',
        mobile.MobileDashboardViewSet.as_view({'get': 'recommendations'}),
        name='mobile-dashboard-recommendations',
    ),
    path(
        'mobile/dashboard/streak/',
        mobile.MobileDashboardViewSet.as_view({'get': 'streak'}),
        name='mobile-dashboard-streak',
    ),
    path(
        'mobile/submit/practice/',
        mobile.MobileSubmissionViewSet.as_view({'post': 'submit_practice'}),
        name='mobile-submit-practice',
    ),
    path(
        'mobile/submit/test/',
        mobile.MobileSubmissionViewSet.as_view({'post': 'submit_test'}),
        name='mobile-submit-test',
    ),
    path(
        'mobile/sync/status/',
        mobile.MobileSyncViewSet.as_view({'get': 'status'}),
        name='mobile-sync-status',
    ),
    path(
        'mobile/notifications/preferences/',
        mobile.MobileNotificationViewSet.as_view({
            'get': 'preferences',
            'post': 'update_preferences',
        }),
        name='mobile-notification-preferences',
    ),
]


# ============================================================
# API INFO ENDPOINT
# ============================================================

@api_view(['GET'])
def get_api_info(request):
    api_info = {
        'version':         '1.0.0',
        'title':           'LMS API',
        'description':     'Complete REST API for Learning Management System',
        'domains': [
            'core', 'grammar', 'punctuation', 'vocabulary',
            'comprehension', 'writing', 'pronunciation',
            'testing', 'progress', 'mobile',
        ],
        'total_endpoints': len(router.urls) + len(custom_urlpatterns),
    }
    return Response(api_info)


custom_urlpatterns.append(
    path('info/', get_api_info, name='api-info')
)


# ============================================================
# VERSIONED API URLS
# ============================================================

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/', include(custom_urlpatterns)),
    path('',    include(router.urls)),
    path('',    include(custom_urlpatterns)),
]