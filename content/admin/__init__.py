# content/admin/__init__.py

# Core admin
from .core import (
    TextbookAdmin, UnitAdmin, LessonAdmin, LessonChunkAdmin
)

# Grammar admin
from .grammar import (
    GrammarConceptAdmin, GrammarRuleAdmin, GrammarExampleAdmin,
    ChunkGrammarFocusAdmin, GrammarQuestionAdmin,
    GrammarPracticeAttemptAdmin, GrammarTestAttemptAdmin,
)

# Punctuation admin
from .punctuation import (
    PunctuationMarkAdmin, PunctuationRuleAdmin, PunctuationExampleAdmin,
    ChunkPunctuationFocusAdmin, ChunkPunctuationFocusRuleAdmin,
    PunctuationQuestionAdmin, PunctuationPracticeAttemptAdmin,
    PunctuationTestAttemptAdmin
)

# Vocabulary admin
from .vocabulary import (
    VocabularyItemAdmin, VocabularyAttemptAdmin, StudentVocabMasteryAdmin
)

# Comprehension admin
from .comprehension import (
    ChunkComprehensionFocusAdmin, ComprehensionQuestionAdmin,
    ComprehensionPracticeAttemptAdmin, ComprehensionTestAttemptAdmin,
    ComprehensionQuestionAttemptAdmin
)

# Writing admin — new three-tier architecture
from .writing import (
    WritingAcademicYearAdmin,
    WritingStageAdmin,
    WritingStageContentAdmin,
    WritingAttemptAdmin,
    WritingStageMasteryAdmin,
    WritingInterventionAdmin,
)

# Pronunciation admin
from .pronunciation import (
    PronunciationFocusAdmin, PronunciationAttemptAdmin,
    PronunciationMasteryAdmin
)

# Testing admin
from .testing import (
    UnitTestSessionAdmin, UnitTestQuestionAdmin, UnitTestAnswerAdmin,
    VocabularyUnitTestAttemptAdmin
)


__all__ = [
    # Core
    'TextbookAdmin', 'UnitAdmin', 'LessonAdmin', 'LessonChunkAdmin',

    # Grammar
    'GrammarConceptAdmin', 'GrammarRuleAdmin', 'GrammarExampleAdmin',
    'ChunkGrammarFocusAdmin', 'GrammarQuestionAdmin',
    'GrammarPracticeAttemptAdmin', 'GrammarTestAttemptAdmin',

    # Punctuation
    'PunctuationMarkAdmin', 'PunctuationRuleAdmin', 'PunctuationExampleAdmin',
    'ChunkPunctuationFocusAdmin', 'ChunkPunctuationFocusRuleAdmin',
    'PunctuationQuestionAdmin', 'PunctuationPracticeAttemptAdmin',
    'PunctuationTestAttemptAdmin',

    # Vocabulary
    'VocabularyItemAdmin', 'VocabularyAttemptAdmin', 'StudentVocabMasteryAdmin',

    # Comprehension
    'ChunkComprehensionFocusAdmin', 'ComprehensionQuestionAdmin',
    'ComprehensionPracticeAttemptAdmin', 'ComprehensionTestAttemptAdmin',
    'ComprehensionQuestionAttemptAdmin',

    # Writing
    'WritingAcademicYearAdmin',
    'WritingStageAdmin',
    'WritingStageContentAdmin',
    'WritingAttemptAdmin',
    'WritingStageMasteryAdmin',
    'WritingInterventionAdmin',

    # Pronunciation
    'PronunciationFocusAdmin', 'PronunciationAttemptAdmin',
    'PronunciationMasteryAdmin',

    # Testing
    'UnitTestSessionAdmin', 'UnitTestQuestionAdmin', 'UnitTestAnswerAdmin',
    'VocabularyUnitTestAttemptAdmin',
]