# content/admin/inlines/__init__.py

# Core inlines
from .core import LessonChunkInline

# Grammar inlines
from .grammar import (
    ChunkGrammarFocusInline,
    GrammarQuestionInline,
)

# Punctuation inlines
from .punctuation import (
    PunctuationRuleInline,
    PunctuationExampleInline,
    PunctuationQuestionInline,
    FocusRuleInline,
    PunctuationPracticeAttemptInline,
    PunctuationTestAttemptInline,
)

# Vocabulary inlines
from .vocabulary import (
    VocabularyItemInline,
    VocabularyItemQuickInline,
)

# Comprehension inlines
from .comprehension import (
    ComprehensionQuestionInline,
    ComprehensionQuestionStackedInline,
)

# Writing inlines — new three-tier architecture
from .writing import (
    WritingStageContentInline,
    WritingAttemptInline,
    WritingInterventionInline,
    WritingStageMasteryInline,
)

# Pronunciation inlines
from .pronunciation import (
    PronunciationFocusInline,
    PronunciationAttemptInline,
    PronunciationMasteryInline,
)

# Testing inlines
from .testing import (
    UnitTestQuestionInline,
    UnitTestQuestionStackedInline,
    UnitTestAnswerInline,
    VocabularyUnitTestAttemptInline,
    VocabularyUnitTestAttemptDetailInline,
)


__all__ = [
    # Core
    'LessonChunkInline',

    # Grammar
    'ChunkGrammarFocusInline',
    'GrammarQuestionInline',

    # Punctuation
    'PunctuationRuleInline',
    'PunctuationExampleInline',
    'PunctuationQuestionInline',
    'FocusRuleInline',
    'PunctuationPracticeAttemptInline',
    'PunctuationTestAttemptInline',

    # Vocabulary
    'VocabularyItemInline',
    'VocabularyItemQuickInline',

    # Comprehension
    'ComprehensionQuestionInline',
    'ComprehensionQuestionStackedInline',

    # Writing
    'WritingStageContentInline',
    'WritingAttemptInline',
    'WritingInterventionInline',
    'WritingStageMasteryInline',

    # Pronunciation
    'PronunciationFocusInline',
    'PronunciationAttemptInline',
    'PronunciationMasteryInline',

    # Testing
    'UnitTestQuestionInline',
    'UnitTestQuestionStackedInline',
    'UnitTestAnswerInline',
    'VocabularyUnitTestAttemptInline',
    'VocabularyUnitTestAttemptDetailInline',
]