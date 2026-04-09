# content/serializers/__init__.py

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
    LessonChunkSerializer,
    LessonSerializer,
    UnitSerializer,
    TextbookSerializer,
    LessonListMobileSerializer,
    UnitListMobileSerializer,
    TextbookListMobileSerializer,
    ChunkMasteryDetailsSerializer,
    LessonChunkMasterySerializer,
)

# ============================================================
# GRAMMAR SERIALIZERS
# ============================================================
from .grammar import (
    GrammarConceptSerializer,
    GrammarConceptListSerializer,
    GrammarRuleSerializer,
    GrammarExampleSerializer,
    ChunkGrammarFocusSerializer,
    ChunkGrammarFocusListSerializer,
    GrammarQuestionSerializer,
    GrammarPracticeAttemptSerializer,
    GrammarPracticeAttemptSubmitSerializer,
    GrammarTestAttemptSerializer,
    GrammarTestAttemptSubmitSerializer,
    GrammarQuestionAttemptSerializer,
    GrammarQuestionAttemptDetailSerializer,
    GrammarConceptProgressSerializer,
    GrammarFocusProgressSerializer,
    GrammarBulkQuestionCreateSerializer,
)

# ============================================================
# PUNCTUATION SERIALIZERS
# ============================================================
from .punctuation import (
    PunctuationMarkSerializer,
    PunctuationMarkDetailSerializer,
    PunctuationRuleSerializer,
    PunctuationRuleDetailSerializer,
    PunctuationExampleSerializer,
    ChunkPunctuationFocusSerializer,
    ChunkPunctuationFocusListSerializer,
    ChunkPunctuationFocusRuleSerializer,
    PunctuationQuestionSerializer,
    PunctuationPracticeAttemptSerializer,
    PunctuationPracticeAttemptSubmitSerializer,
    PunctuationTestAttemptSerializer,
    PunctuationTestAttemptSubmitSerializer,
    PunctuationMarkProgressSerializer,
    PunctuationFocusProgressSerializer,
    PunctuationBulkQuestionCreateSerializer,
    PunctuationBulkFocusRuleCreateSerializer,
)

# ============================================================
# VOCABULARY SERIALIZERS
# ============================================================
from .vocabulary import (
    VocabularyItemSerializer,
    VocabularyItemListSerializer,
    VocabularyItemDetailSerializer,
    VocabularyItemMobileSerializer,
    VocabularyAttemptSerializer,
    VocabularyAttemptSubmitSerializer,
    VocabularyBatchAttemptSubmitSerializer,
    StudentVocabMasterySerializer,
    StudentVocabMasteryUpdateSerializer,
    StudentVocabMasteryMobileSerializer,
    VocabularyProgressSummarySerializer,
    VocabularyItemProgressSerializer,
    VocabularySessionSummarySerializer,
    VocabularyBulkCreateSerializer,
    VocabularyBulkMasteryUpdateSerializer,
)

# ============================================================
# COMPREHENSION SERIALIZERS
# ============================================================
from .comprehension import (
    ChunkComprehensionFocusSerializer,
    ChunkComprehensionFocusListSerializer,
    ComprehensionQuestionSerializer,
    ComprehensionPracticeAttemptSerializer,
    ComprehensionPracticeAttemptSubmitSerializer,
    ComprehensionTestAttemptSerializer,
    ComprehensionTestAttemptSubmitSerializer,
    ComprehensionQuestionAttemptSerializer,
    ComprehensionQuestionAttemptDetailSerializer,
    ComprehensionBloomLevelProgressSerializer,
    ComprehensionFocusProgressSerializer,
    ComprehensionBulkQuestionCreateSerializer,
)

# ============================================================
# WRITING SERIALIZERS
# New three-tier architecture.
# ============================================================
from .writing import (
    # Academic year
    WritingAcademicYearSerializer,
    WritingAcademicYearListSerializer,

    # Stages
    WritingStageSerializer,
    WritingStageListSerializer,

    # Stage content
    WritingStageContentSerializer,
    WritingStageContentListSerializer,
    WritingStageContentStudentSerializer,

    # Attempts
    WritingAttemptSerializer,
    WritingAttemptStudentSerializer,
    WritingAttemptSubmitSerializer,
    WritingAttemptListSerializer,

    # Mastery
    WritingStageMasterySerializer,
    WritingStageMasteryListSerializer,

    # Interventions
    WritingInterventionSerializer,
    WritingInterventionFixSerializer,

    # Progress
    WritingStageProgressSerializer,
    WritingTierProgressSerializer,
    WritingJourneySerializer,
    WritingProgressSummarySerializer,

    # Mobile
    WritingStageContentMobileSerializer,
    WritingAttemptMobileSerializer,
    WritingStageMasteryMobileSerializer,
)

# ============================================================
# PRONUNCIATION SERIALIZERS
# ============================================================
from .pronunciation import (
    PronunciationFocusSerializer,
    PronunciationFocusListSerializer,
    PronunciationAttemptSerializer,
    PronunciationAttemptSubmitSerializer,
    PronunciationAttemptMobileSerializer,
    PronunciationMasterySerializer,
    PronunciationMasteryUpdateSerializer,
    PronunciationMasteryMobileSerializer,
    PronunciationProgressSummarySerializer,
    PronunciationFocusProgressSerializer,
    PronunciationBulkFocusCreateSerializer,
    PronunciationAudioAnalysisSerializer,
    PronunciationFeedbackSerializer,
)

# ============================================================
# TESTING SERIALIZERS
# ============================================================
from .testing import (
    UnitTestQuestionSerializer,
    UnitTestQuestionListSerializer,
    UnitTestQuestionMobileSerializer,
    UnitTestAnswerSerializer,
    UnitTestAnswerSubmitSerializer,
    UnitTestAnswerMobileSerializer,
    UnitTestSessionSerializer,
    UnitTestSessionListSerializer,
    UnitTestSessionCreateSerializer,
    UnitTestSessionSubmitSerializer,
    UnitTestSessionMobileSerializer,
    UnitTestSessionActiveMobileSerializer,
    VocabularyUnitTestAttemptSerializer,
    UnitTestDomainBreakdownSerializer,
    UnitTestHistorySerializer,
    UnitTestHistoryMobileSerializer,
    UnitTestPerformanceSerializer,
    UnitTestBulkQuestionCreateSerializer,
    TestGenerationConfigSerializer,
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
    GrammarProgressSerializer,
    PunctuationProgressSerializer,
    VocabularyProgressSerializer,
    ComprehensionProgressSerializer,
    WritingProgressSerializer,
    PronunciationProgressSerializer,
    UnitTestProgressSerializer,
    OverallProgressSerializer,
    DomainProgressMobileSerializer,
    DashboardMobileSerializer,
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

    # Writing mobile — imported from writing.py via mobile.py
    WritingStageContentMobileSerializer,
    WritingAttemptMobileSerializer,
    WritingStageMasteryMobileSerializer,

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
    MobilePracticeSubmitSerializer,
    MobileTestSubmitSerializer,
    SyncPayloadSerializer,
    SyncResponseSerializer,
    MobileBatchContentSerializer,
    MobileBatchContentResponseSerializer,
    MobileNotificationSerializer,
)


# ============================================================
# VERSION AND METADATA
# ============================================================

__version__ = "1.0.0"
__author__  = "LMS Team"
__description__ = (
    "Complete set of serializers for LMS API with mobile optimization"
)


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

    # Writing — new three-tier architecture
    "WritingAcademicYearSerializer",
    "WritingAcademicYearListSerializer",
    "WritingStageSerializer",
    "WritingStageListSerializer",
    "WritingStageContentSerializer",
    "WritingStageContentListSerializer",
    "WritingStageContentStudentSerializer",
    "WritingAttemptSerializer",
    "WritingAttemptStudentSerializer",
    "WritingAttemptSubmitSerializer",
    "WritingAttemptListSerializer",
    "WritingStageMasterySerializer",
    "WritingStageMasteryListSerializer",
    "WritingInterventionSerializer",
    "WritingInterventionFixSerializer",
    "WritingStageProgressSerializer",
    "WritingTierProgressSerializer",
    "WritingJourneySerializer",
    "WritingProgressSummarySerializer",
    "WritingStageContentMobileSerializer",
    "WritingAttemptMobileSerializer",
    "WritingStageMasteryMobileSerializer",

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
    "VocabularyItemMobileSerializer",
    "VocabularyAttemptMobileSerializer",
    "StudentVocabMasteryMobileSerializer",
    "ComprehensionQuestionMobileSerializer",
    "ChunkComprehensionFocusMobileSerializer",
    "ComprehensionPracticeAttemptMobileSerializer",
    "ComprehensionTestAttemptMobileSerializer",
    "WritingStageContentMobileSerializer",
    "WritingAttemptMobileSerializer",
    "WritingStageMasteryMobileSerializer",
    "PronunciationFocusMobileSerializer",
    "PronunciationAttemptMobileSerializer",
    "PronunciationMasteryMobileSerializer",
    "UnitTestQuestionMobileSerializer",
    "UnitTestSessionMobileSerializer",
    "UnitTestSessionActiveMobileSerializer",
    "UnitTestAnswerMobileSerializer",
    "UnitTestHistoryMobileSerializer",
    "MobilePracticeSubmitSerializer",
    "MobileTestSubmitSerializer",
    "SyncPayloadSerializer",
    "SyncResponseSerializer",
    "MobileBatchContentSerializer",
    "MobileBatchContentResponseSerializer",
    "MobileNotificationSerializer",
]