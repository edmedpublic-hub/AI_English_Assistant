# api_views/__init__.py

"""
LMS API Views
============
This module exports all viewsets for the LMS API, organized by domain.
All viewsets are importable directly from the api_views package.
"""

# ============================================================
# CORE VIEWS
# ============================================================
from .core import (
    # Textbook views
    TextbookViewSet,
    
    # Unit views
    UnitViewSet,
    
    # Lesson views
    LessonViewSet,
    
    # Lesson chunk views
    LessonChunkViewSet,
    
    # Search views
    SearchViewSet,
)

# ============================================================
# GRAMMAR VIEWS
# ============================================================
from .grammar import (
    # Knowledge layer
    GrammarConceptViewSet,
    GrammarRuleViewSet,
    GrammarExampleViewSet,
    
    # Teaching layer
    ChunkGrammarFocusViewSet,
    GrammarQuestionViewSet,
    
    # Practice and test
    GrammarPracticeViewSet,
    GrammarTestViewSet,
    GrammarQuestionAttemptViewSet,
    
    # Progress
    GrammarProgressViewSet,
    
    # Bulk operations
    GrammarBulkOperationViewSet,
)

# ============================================================
# PUNCTUATION VIEWS
# ============================================================
from .punctuation import (
    # Knowledge layer
    PunctuationMarkViewSet,
    PunctuationRuleViewSet,
    PunctuationExampleViewSet,
    
    # Teaching layer
    ChunkPunctuationFocusViewSet,
    ChunkPunctuationFocusRuleViewSet,
    PunctuationQuestionViewSet,
    
    # Practice and test
    PunctuationPracticeViewSet,
    PunctuationTestViewSet,
    
    # Progress
    PunctuationProgressViewSet,
    
    # Bulk operations
    PunctuationBulkOperationViewSet,
)

# ============================================================
# VOCABULARY VIEWS
# ============================================================
from .vocabulary import (
    # Vocabulary items
    VocabularyItemViewSet,
    
    # Practice and mastery
    VocabularyPracticeViewSet,
    StudentVocabMasteryViewSet,
    
    # Progress
    VocabularyProgressViewSet,
    
    # Flashcard mode
    FlashcardViewSet,
)

# ============================================================
# COMPREHENSION VIEWS
# ============================================================
from .comprehension import (
    # Teaching layer
    ChunkComprehensionFocusViewSet,
    ComprehensionQuestionViewSet,
    
    # Practice and test
    ComprehensionPracticeViewSet,
    ComprehensionTestViewSet,
    ComprehensionQuestionAttemptViewSet,
    
    # Progress
    ComprehensionProgressViewSet,
    
    # Bulk operations
    ComprehensionBulkOperationViewSet,
)

# ============================================================
# WRITING VIEWS
# Temporarily silenced — API layer being rebuilt
# to match new three-tier writing architecture.
# Restore after content/api_views/writing.py is rebuilt.
# ============================================================
# from .writing import (
#     ChunkWritingFocusViewSet,
#     UnitWritingTaskViewSet,
#     WritingPromptViewSet,
#     WritingPracticeViewSet,
#     WritingTestViewSet,
#     WritingProgressViewSet,
#     WritingBulkOperationViewSet,
# )

# ============================================================
# PRONUNCIATION VIEWS
# ============================================================
from .pronunciation import (
    # Teaching layer
    PronunciationFocusViewSet,
    
    # Practice and mastery
    PronunciationAttemptViewSet,
    PronunciationMasteryViewSet,
    
    # Audio processing
    PronunciationAudioViewSet,
    
    # Progress
    PronunciationProgressViewSet,
    
    # Bulk operations
    PronunciationBulkOperationViewSet,
)

# ============================================================
# TESTING VIEWS
# ============================================================
from .testing import (
    # Test sessions
    UnitTestSessionViewSet,
    UnitTestQuestionViewSet,
    UnitTestAnswerViewSet,
    
    # Progress
    UnitTestProgressViewSet,
    
    # Test generation
    TestGenerationViewSet,
    
    # Legacy migration
    LegacyMigrationViewSet,
)

# ============================================================
# PROGRESS & DASHBOARD VIEWS
# ============================================================
from .progress import (
    # Dashboard
    DashboardViewSet,
    
    # Unit and lesson progress
    UnitProgressViewSet,
    LessonProgressViewSet,
    
    # Analytics
    AnalyticsViewSet,
)

# ============================================================
# MOBILE VIEWS
# ============================================================
from .mobile import (
    # Mobile content
    MobileContentViewSet,
    
    # Mobile domain-specific
    MobileGrammarViewSet,
    MobilePunctuationViewSet,
    MobileVocabularyViewSet,
    MobileComprehensionViewSet,
    MobileWritingViewSet,
    MobilePronunciationViewSet,
    MobileTestingViewSet,
    
    # Mobile dashboard
    MobileDashboardViewSet,
    
    # Mobile submissions
    MobileSubmissionViewSet,
    
    # Mobile sync and batch
    MobileSyncViewSet,
    MobileBatchViewSet,
    
    # Mobile notifications
    MobileNotificationViewSet,
)

# ============================================================
# BASE VIEWS
# ============================================================
from .base import (
    # Base classes
    BaseViewSet,
    ReadOnlyViewSet,
    PracticeViewSet,
    TestViewSet,
    ProgressViewSet,
    
    # Mixins
    UserFilterMixin,
    MultipleFieldLookupMixin,
    CachedQuerysetMixin,
    
    # Permissions
    IsOwnerOrReadOnly,
    IsEnrolledOrReadOnly,
    
    # Pagination
    StandardResultsSetPagination,
    MobileOptimizedPagination,
    
    # Utilities
    log_user_activity,
    get_client_ip,
)


# ============================================================
# VERSION AND METADATA
# ============================================================

__version__ = "1.0.0"
__author__ = "LMS Team"
__description__ = "Complete set of viewsets for LMS API with mobile optimization"


# ============================================================
# EXPORT ALL VIEWSETS
# ============================================================

__all__ = [
    # Core
    "TextbookViewSet",
    "UnitViewSet",
    "LessonViewSet",
    "LessonChunkViewSet",
    "SearchViewSet",
    
    # Grammar
    "GrammarConceptViewSet",
    "GrammarRuleViewSet",
    "GrammarExampleViewSet",
    "ChunkGrammarFocusViewSet",
    "GrammarQuestionViewSet",
    "GrammarPracticeViewSet",
    "GrammarTestViewSet",
    "GrammarQuestionAttemptViewSet",
    "GrammarProgressViewSet",
    "GrammarBulkOperationViewSet",
    
    # Punctuation
    "PunctuationMarkViewSet",
    "PunctuationRuleViewSet",
    "PunctuationExampleViewSet",
    "ChunkPunctuationFocusViewSet",
    "ChunkPunctuationFocusRuleViewSet",
    "PunctuationQuestionViewSet",
    "PunctuationPracticeViewSet",
    "PunctuationTestViewSet",
    "PunctuationProgressViewSet",
    "PunctuationBulkOperationViewSet",
    
    # Vocabulary
    "VocabularyItemViewSet",
    "VocabularyPracticeViewSet",
    "StudentVocabMasteryViewSet",
    "VocabularyProgressViewSet",
    "FlashcardViewSet",
    
    # Comprehension
    "ChunkComprehensionFocusViewSet",
    "ComprehensionQuestionViewSet",
    "ComprehensionPracticeViewSet",
    "ComprehensionTestViewSet",
    "ComprehensionQuestionAttemptViewSet",
    "ComprehensionProgressViewSet",
    "ComprehensionBulkOperationViewSet",
    
    # Writing — temporarily silenced
    # "ChunkWritingFocusViewSet",
    # "UnitWritingTaskViewSet",
    # "WritingPromptViewSet",
    # "WritingPracticeViewSet",
    # "WritingTestViewSet",
    # "WritingProgressViewSet",
    # "WritingBulkOperationViewSet",
    
    # Pronunciation
    "PronunciationFocusViewSet",
    "PronunciationAttemptViewSet",
    "PronunciationMasteryViewSet",
    "PronunciationAudioViewSet",
    "PronunciationProgressViewSet",
    "PronunciationBulkOperationViewSet",
    
    # Testing
    "UnitTestSessionViewSet",
    "UnitTestQuestionViewSet",
    "UnitTestAnswerViewSet",
    "UnitTestProgressViewSet",
    "TestGenerationViewSet",
    "LegacyMigrationViewSet",
    
    # Progress & Dashboard
    "DashboardViewSet",
    "UnitProgressViewSet",
    "LessonProgressViewSet",
    "AnalyticsViewSet",
    
    # Mobile
    "MobileContentViewSet",
    "MobileGrammarViewSet",
    "MobilePunctuationViewSet",
    "MobileVocabularyViewSet",
    "MobileComprehensionViewSet",
    "MobileWritingViewSet",
    "MobilePronunciationViewSet",
    "MobileTestingViewSet",
    "MobileDashboardViewSet",
    "MobileSubmissionViewSet",
    "MobileSyncViewSet",
    "MobileBatchViewSet",
    "MobileNotificationViewSet",
    
    # Base
    "BaseViewSet",
    "ReadOnlyViewSet",
    "PracticeViewSet",
    "TestViewSet",
    "ProgressViewSet",
    "UserFilterMixin",
    "MultipleFieldLookupMixin",
    "CachedQuerysetMixin",
    "IsOwnerOrReadOnly",
    "IsEnrolledOrReadOnly",
    "StandardResultsSetPagination",
    "MobileOptimizedPagination",
    "log_user_activity",
    "get_client_ip",
]