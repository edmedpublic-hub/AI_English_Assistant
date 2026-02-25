# serializers/__init__.py

"""
LMS API Serializers
==================
This module exports all serializers for the LMS API, organized by domain.
All serializers are importable directly from the serializers package.
"""

# ============================================================
# CORE SERIALIZERS
# ============================================================
from .core import (
    # Main serializers
    LessonChunkSerializer,
    LessonSerializer,
    UnitSerializer,
    TextbookSerializer,
    
    # List serializers
    LessonListMobileSerializer,
    UnitListMobileSerializer,
    TextbookListMobileSerializer,
    
    # Mastery serializers
    ChunkMasteryDetailsSerializer,
    LessonChunkMasterySerializer,
)

# ============================================================
# GRAMMAR SERIALIZERS
# ============================================================
from .grammar import (
    # Knowledge layer
    GrammarConceptSerializer,
    GrammarConceptListSerializer,
    GrammarRuleSerializer,
    GrammarExampleSerializer,
    
    # Teaching layer
    ChunkGrammarFocusSerializer,
    ChunkGrammarFocusListSerializer,
    GrammarQuestionSerializer,
    
    # Practice layer
    GrammarPracticeAttemptSerializer,
    GrammarPracticeAttemptSubmitSerializer,
    
    # Test layer
    GrammarTestAttemptSerializer,
    GrammarTestAttemptSubmitSerializer,
    
    # Question attempts
    GrammarQuestionAttemptSerializer,
    GrammarQuestionAttemptDetailSerializer,
    
    # Progress tracking
    GrammarConceptProgressSerializer,
    GrammarFocusProgressSerializer,
    
    # Bulk operations
    GrammarBulkQuestionCreateSerializer,
)

# ============================================================
# PUNCTUATION SERIALIZERS
# ============================================================
from .punctuation import (
    # Knowledge layer
    PunctuationMarkSerializer,
    PunctuationMarkDetailSerializer,
    PunctuationRuleSerializer,
    PunctuationRuleDetailSerializer,
    PunctuationExampleSerializer,
    
    # Teaching layer
    ChunkPunctuationFocusSerializer,
    ChunkPunctuationFocusListSerializer,
    ChunkPunctuationFocusRuleSerializer,
    PunctuationQuestionSerializer,
    
    # Practice layer
    PunctuationPracticeAttemptSerializer,
    PunctuationPracticeAttemptSubmitSerializer,
    
    # Test layer
    PunctuationTestAttemptSerializer,
    PunctuationTestAttemptSubmitSerializer,
    
    # Progress tracking
    PunctuationMarkProgressSerializer,
    PunctuationFocusProgressSerializer,
    
    # Bulk operations
    PunctuationBulkQuestionCreateSerializer,
    PunctuationBulkFocusRuleCreateSerializer,
)

# ============================================================
# VOCABULARY SERIALIZERS
# ============================================================
from .vocabulary import (
    # Vocabulary items
    VocabularyItemSerializer,
    VocabularyItemListSerializer,
    VocabularyItemDetailSerializer,
    VocabularyItemMobileSerializer,
    
    # Attempts
    VocabularyAttemptSerializer,
    VocabularyAttemptSubmitSerializer,
    VocabularyBatchAttemptSubmitSerializer,
    
    # Mastery
    StudentVocabMasterySerializer,
    StudentVocabMasteryUpdateSerializer,
    StudentVocabMasteryMobileSerializer,
    
    # Progress tracking
    VocabularyProgressSummarySerializer,
    VocabularyItemProgressSerializer,
    VocabularySessionSummarySerializer,
    
    # Bulk operations
    VocabularyBulkCreateSerializer,
    VocabularyBulkMasteryUpdateSerializer,
)

# ============================================================
# COMPREHENSION SERIALIZERS
# ============================================================
from .comprehension import (
    # Teaching layer
    ChunkComprehensionFocusSerializer,
    ChunkComprehensionFocusListSerializer,
    ComprehensionQuestionSerializer,
    
    # Practice layer
    ComprehensionPracticeAttemptSerializer,
    ComprehensionPracticeAttemptSubmitSerializer,
    
    # Test layer
    ComprehensionTestAttemptSerializer,
    ComprehensionTestAttemptSubmitSerializer,
    
    # Question attempts
    ComprehensionQuestionAttemptSerializer,
    ComprehensionQuestionAttemptDetailSerializer,
    
    # Progress tracking
    ComprehensionBloomLevelProgressSerializer,
    ComprehensionFocusProgressSerializer,
    
    # Bulk operations
    ComprehensionBulkQuestionCreateSerializer,
)

# ============================================================
# WRITING SERIALIZERS
# ============================================================
from .writing import (
    # Chunk-level
    ChunkWritingFocusSerializer,
    ChunkWritingFocusListSerializer,
    
    # Unit-level
    UnitWritingTaskSerializer,
    UnitWritingTaskListSerializer,
    
    # Prompts
    WritingPromptSerializer,
    WritingPromptListSerializer,
    WritingPromptMobileSerializer,
    
    # Practice layer
    WritingPracticeAttemptSerializer,
    WritingPracticeAttemptSubmitSerializer,
    WritingPracticeAttemptMobileSerializer,
    
    # Test layer
    WritingTestAttemptSerializer,
    WritingTestAttemptSubmitSerializer,
    WritingTestAttemptMobileSerializer,
    
    # Progress tracking
    WritingProgressSummarySerializer,
    WritingFocusProgressSerializer,
    WritingTaskProgressSerializer,
    
    # Bulk operations
    WritingBulkPromptCreateSerializer,
)

# ============================================================
# PRONUNCIATION SERIALIZERS
# ============================================================
from .pronunciation import (
    # Teaching layer
    PronunciationFocusSerializer,
    PronunciationFocusListSerializer,
    
    # Attempts
    PronunciationAttemptSerializer,
    PronunciationAttemptSubmitSerializer,
    PronunciationAttemptMobileSerializer,
    
    # Mastery
    PronunciationMasterySerializer,
    PronunciationMasteryUpdateSerializer,
    PronunciationMasteryMobileSerializer,
    
    # Progress tracking
    PronunciationProgressSummarySerializer,
    PronunciationFocusProgressSerializer,
    
    # Bulk operations
    PronunciationBulkFocusCreateSerializer,
    
    # Audio processing
    PronunciationAudioAnalysisSerializer,
    PronunciationFeedbackSerializer,
)

# ============================================================
# TESTING SERIALIZERS
# ============================================================
from .testing import (
    # Test questions
    UnitTestQuestionSerializer,
    UnitTestQuestionListSerializer,
    UnitTestQuestionMobileSerializer,
    
    # Test answers
    UnitTestAnswerSerializer,
    UnitTestAnswerSubmitSerializer,
    UnitTestAnswerMobileSerializer,
    
    # Test sessions
    UnitTestSessionSerializer,
    UnitTestSessionListSerializer,
    UnitTestSessionCreateSerializer,
    UnitTestSessionSubmitSerializer,
    UnitTestSessionMobileSerializer,
    UnitTestSessionActiveMobileSerializer,
    
    # Domain-specific test attempts
    VocabularyUnitTestAttemptSerializer,
    
    # Progress tracking
    UnitTestDomainBreakdownSerializer,
    UnitTestHistorySerializer,
    UnitTestHistoryMobileSerializer,
    UnitTestPerformanceSerializer,
    
    # Bulk operations
    UnitTestBulkQuestionCreateSerializer,
    
    # Test generation
    TestGenerationConfigSerializer,
    
    # Legacy migration
    LegacyVocabularyTestSessionSerializer,
    LegacyVocabularyTestQuestionSerializer,
    LegacyVocabularyTestAnswerSerializer,
    LegacyVocabularyTestAttemptSerializer,
    LegacyToUnitTestMigrationSerializer,
)

# ============================================================
# PROGRESS SERIALIZERS (Dashboard)
# ============================================================
from .progress import (
    # Domain-specific progress
    GrammarProgressSerializer,
    PunctuationProgressSerializer,
    VocabularyProgressSerializer,
    ComprehensionProgressSerializer,
    WritingProgressSerializer,
    PronunciationProgressSerializer,
    UnitTestProgressSerializer,
    
    # Overall dashboard
    OverallProgressSerializer,
    DomainProgressMobileSerializer,
    DashboardMobileSerializer,
    
    # Unit/Lesson progress
    UnitProgressDetailSerializer,
    LessonProgressSerializer,
)

# ============================================================
# MOBILE SERIALIZERS
# ============================================================
from .mobile import (
    # Core mobile
    LessonChunkMobileSerializer,
    LessonMobileSerializer,
    UnitMobileSerializer,
    TextbookMobileSerializer,
    UnitWithLessonsMobileSerializer,
    LessonWithChunksMobileSerializer,
    
    # Grammar mobile
    GrammarQuestionMobileSerializer,
    ChunkGrammarFocusMobileSerializer,
    GrammarPracticeAttemptMobileSerializer,
    GrammarTestAttemptMobileSerializer,
    
    # Punctuation mobile
    PunctuationQuestionMobileSerializer,
    ChunkPunctuationFocusMobileSerializer,
    PunctuationPracticeAttemptMobileSerializer,
    PunctuationTestAttemptMobileSerializer,
    
    # Vocabulary mobile
    VocabularyItemMobileSerializer,
    VocabularyAttemptMobileSerializer,
    StudentVocabMasteryMobileSerializer,
    
    # Comprehension mobile
    ComprehensionQuestionMobileSerializer,
    ChunkComprehensionFocusMobileSerializer,
    ComprehensionPracticeAttemptMobileSerializer,
    ComprehensionTestAttemptMobileSerializer,
    
    # Writing mobile
    WritingPromptMobileSerializer,
    ChunkWritingFocusMobileSerializer,
    UnitWritingTaskMobileSerializer,
    WritingPracticeAttemptMobileSerializer,
    WritingTestAttemptMobileSerializer,
    
    # Pronunciation mobile
    PronunciationFocusMobileSerializer,
    PronunciationAttemptMobileSerializer,
    PronunciationMasteryMobileSerializer,
    
    # Testing mobile
    UnitTestQuestionMobileSerializer,
    UnitTestSessionMobileSerializer,
    UnitTestSessionActiveMobileSerializer,
    UnitTestAnswerMobileSerializer,
    UnitTestHistoryMobileSerializer,
    
    # Mobile dashboard
    DomainProgressMobileSerializer,
    DashboardMobileSerializer,
    
    # Mobile submissions
    MobilePracticeSubmitSerializer,
    MobileTestSubmitSerializer,
    
    # Offline sync
    SyncPayloadSerializer,
    SyncResponseSerializer,
    
    # Batch operations
    MobileBatchContentSerializer,
    MobileBatchContentResponseSerializer,
    
    # Push notifications
    MobileNotificationSerializer,
)


# ============================================================
# VERSION AND METADATA
# ============================================================

__version__ = "1.0.0"
__author__ = "LMS Team"
__description__ = "Complete set of serializers for LMS API with mobile optimization"


# ============================================================
# EXPORT ALL SERIALIZERS
# ============================================================

__all__ = [
    # Core
    "LessonChunkSerializer",
    "LessonSerializer",
    "UnitSerializer",
    "TextbookSerializer",
    "LessonListMobileSerializer",
    "UnitListMobileSerializer",
    "TextbookListMobileSerializer",
    "ChunkMasteryDetailsSerializer",
    "LessonChunkMasterySerializer",
    
    # Grammar
    "GrammarConceptSerializer",
    "GrammarConceptListSerializer",
    "GrammarRuleSerializer",
    "GrammarExampleSerializer",
    "ChunkGrammarFocusSerializer",
    "ChunkGrammarFocusListSerializer",
    "GrammarQuestionSerializer",
    "GrammarPracticeAttemptSerializer",
    "GrammarPracticeAttemptSubmitSerializer",
    "GrammarTestAttemptSerializer",
    "GrammarTestAttemptSubmitSerializer",
    "GrammarQuestionAttemptSerializer",
    "GrammarQuestionAttemptDetailSerializer",
    "GrammarConceptProgressSerializer",
    "GrammarFocusProgressSerializer",
    "GrammarBulkQuestionCreateSerializer",
    
    # Punctuation
    "PunctuationMarkSerializer",
    "PunctuationMarkDetailSerializer",
    "PunctuationRuleSerializer",
    "PunctuationRuleDetailSerializer",
    "PunctuationExampleSerializer",
    "ChunkPunctuationFocusSerializer",
    "ChunkPunctuationFocusListSerializer",
    "ChunkPunctuationFocusRuleSerializer",
    "PunctuationQuestionSerializer",
    "PunctuationPracticeAttemptSerializer",
    "PunctuationPracticeAttemptSubmitSerializer",
    "PunctuationTestAttemptSerializer",
    "PunctuationTestAttemptSubmitSerializer",
    "PunctuationMarkProgressSerializer",
    "PunctuationFocusProgressSerializer",
    "PunctuationBulkQuestionCreateSerializer",
    "PunctuationBulkFocusRuleCreateSerializer",
    
    # Vocabulary
    "VocabularyItemSerializer",
    "VocabularyItemListSerializer",
    "VocabularyItemDetailSerializer",
    "VocabularyItemMobileSerializer",
    "VocabularyAttemptSerializer",
    "VocabularyAttemptSubmitSerializer",
    "VocabularyBatchAttemptSubmitSerializer",
    "StudentVocabMasterySerializer",
    "StudentVocabMasteryUpdateSerializer",
    "StudentVocabMasteryMobileSerializer",
    "VocabularyProgressSummarySerializer",
    "VocabularyItemProgressSerializer",
    "VocabularySessionSummarySerializer",
    "VocabularyBulkCreateSerializer",
    "VocabularyBulkMasteryUpdateSerializer",
    
    # Comprehension
    "ChunkComprehensionFocusSerializer",
    "ChunkComprehensionFocusListSerializer",
    "ComprehensionQuestionSerializer",
    "ComprehensionPracticeAttemptSerializer",
    "ComprehensionPracticeAttemptSubmitSerializer",
    "ComprehensionTestAttemptSerializer",
    "ComprehensionTestAttemptSubmitSerializer",
    "ComprehensionQuestionAttemptSerializer",
    "ComprehensionQuestionAttemptDetailSerializer",
    "ComprehensionBloomLevelProgressSerializer",
    "ComprehensionFocusProgressSerializer",
    "ComprehensionBulkQuestionCreateSerializer",
    
    # Writing
    "ChunkWritingFocusSerializer",
    "ChunkWritingFocusListSerializer",
    "UnitWritingTaskSerializer",
    "UnitWritingTaskListSerializer",
    "WritingPromptSerializer",
    "WritingPromptListSerializer",
    "WritingPromptMobileSerializer",
    "WritingPracticeAttemptSerializer",
    "WritingPracticeAttemptSubmitSerializer",
    "WritingPracticeAttemptMobileSerializer",
    "WritingTestAttemptSerializer",
    "WritingTestAttemptSubmitSerializer",
    "WritingTestAttemptMobileSerializer",
    "WritingProgressSummarySerializer",
    "WritingFocusProgressSerializer",
    "WritingTaskProgressSerializer",
    "WritingBulkPromptCreateSerializer",
    
    # Pronunciation
    "PronunciationFocusSerializer",
    "PronunciationFocusListSerializer",
    "PronunciationAttemptSerializer",
    "PronunciationAttemptSubmitSerializer",
    "PronunciationAttemptMobileSerializer",
    "PronunciationMasterySerializer",
    "PronunciationMasteryUpdateSerializer",
    "PronunciationMasteryMobileSerializer",
    "PronunciationProgressSummarySerializer",
    "PronunciationFocusProgressSerializer",
    "PronunciationBulkFocusCreateSerializer",
    "PronunciationAudioAnalysisSerializer",
    "PronunciationFeedbackSerializer",
    
    # Testing
    "UnitTestQuestionSerializer",
    "UnitTestQuestionListSerializer",
    "UnitTestQuestionMobileSerializer",
    "UnitTestAnswerSerializer",
    "UnitTestAnswerSubmitSerializer",
    "UnitTestAnswerMobileSerializer",
    "UnitTestSessionSerializer",
    "UnitTestSessionListSerializer",
    "UnitTestSessionCreateSerializer",
    "UnitTestSessionSubmitSerializer",
    "UnitTestSessionMobileSerializer",
    "UnitTestSessionActiveMobileSerializer",
    "VocabularyUnitTestAttemptSerializer",
    "UnitTestDomainBreakdownSerializer",
    "UnitTestHistorySerializer",
    "UnitTestHistoryMobileSerializer",
    "UnitTestPerformanceSerializer",
    "UnitTestBulkQuestionCreateSerializer",
    "TestGenerationConfigSerializer",
    "LegacyVocabularyTestSessionSerializer",
    "LegacyVocabularyTestQuestionSerializer",
    "LegacyVocabularyTestAnswerSerializer",
    "LegacyVocabularyTestAttemptSerializer",
    "LegacyToUnitTestMigrationSerializer",
    
    # Progress
    "GrammarProgressSerializer",
    "PunctuationProgressSerializer",
    "VocabularyProgressSerializer",
    "ComprehensionProgressSerializer",
    "WritingProgressSerializer",
    "PronunciationProgressSerializer",
    "UnitTestProgressSerializer",
    "OverallProgressSerializer",
    "DomainProgressMobileSerializer",
    "DashboardMobileSerializer",
    "UnitProgressDetailSerializer",
    "LessonProgressSerializer",
    
    # Mobile
    "LessonChunkMobileSerializer",
    "LessonMobileSerializer",
    "UnitMobileSerializer",
    "TextbookMobileSerializer",
    "UnitWithLessonsMobileSerializer",
    "LessonWithChunksMobileSerializer",
    "GrammarQuestionMobileSerializer",
    "ChunkGrammarFocusMobileSerializer",
    "GrammarPracticeAttemptMobileSerializer",
    "GrammarTestAttemptMobileSerializer",
    "PunctuationQuestionMobileSerializer",
    "ChunkPunctuationFocusMobileSerializer",
    "PunctuationPracticeAttemptMobileSerializer",
    "PunctuationTestAttemptMobileSerializer",
    "VocabularyAttemptMobileSerializer",
    "ComprehensionQuestionMobileSerializer",
    "ChunkComprehensionFocusMobileSerializer",
    "ComprehensionPracticeAttemptMobileSerializer",
    "ComprehensionTestAttemptMobileSerializer",
    "WritingPromptMobileSerializer",
    "ChunkWritingFocusMobileSerializer",
    "UnitWritingTaskMobileSerializer",
    "WritingPracticeAttemptMobileSerializer",
    "WritingTestAttemptMobileSerializer",
    "PronunciationFocusMobileSerializer",
    "PronunciationAttemptMobileSerializer",
    "PronunciationMasteryMobileSerializer",
    "UnitTestSessionActiveMobileSerializer",
    "MobilePracticeSubmitSerializer",
    "MobileTestSubmitSerializer",
    "SyncPayloadSerializer",
    "SyncResponseSerializer",
    "MobileBatchContentSerializer",
    "MobileBatchContentResponseSerializer",
    "MobileNotificationSerializer",
]