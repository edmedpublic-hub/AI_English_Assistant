# content/models/__init__.py

# Core hierarchy
from .core import Textbook, Unit, Lesson, LessonChunk

# Grammar domain
from .grammar import (
    GrammarConcept, GrammarRule, GrammarExample,
    ChunkGrammarFocus, GrammarQuestion,
    GrammarPracticeAttempt, GrammarTestAttempt, GrammarQuestionAttempt
)

# Punctuation domain
from .punctuation import (
    PunctuationMark, PunctuationRule, PunctuationExample,
    ChunkPunctuationFocus, ChunkPunctuationFocusRule,
    PunctuationQuestion, PunctuationPracticeAttempt, PunctuationTestAttempt
)

# Vocabulary domain
from .vocabulary import (
    VocabularyItem, VocabularyAttempt, StudentVocabMastery
)

# Comprehension domain
from .comprehension import (
    ChunkComprehensionFocus, ComprehensionQuestion,
    ComprehensionPracticeAttempt, ComprehensionTestAttempt,
    ComprehensionQuestionAttempt
)

# Writing domain — new three-tier architecture
from .writing import (
    WritingAcademicYear,
    WritingStage,
    WritingStageContent,
    WritingAttempt,
    WritingStageMastery,
    WritingIntervention,
)

# Pronunciation domain
from .pronunciation import (
    PronunciationFocus, PronunciationAttempt, PronunciationMastery
)

# Testing domain (Unit Tests)
from .testing import (
    UnitTestSession, UnitTestQuestion, UnitTestAnswer,
    VocabularyUnitTestAttempt
)


__all__ = [
    # Core
    'Textbook', 'Unit', 'Lesson', 'LessonChunk',

    # Grammar
    'GrammarConcept', 'GrammarRule', 'GrammarExample',
    'ChunkGrammarFocus', 'GrammarQuestion',
    'GrammarPracticeAttempt', 'GrammarTestAttempt', 'GrammarQuestionAttempt',

    # Punctuation
    'PunctuationMark', 'PunctuationRule', 'PunctuationExample',
    'ChunkPunctuationFocus', 'ChunkPunctuationFocusRule',
    'PunctuationQuestion', 'PunctuationPracticeAttempt',
    'PunctuationTestAttempt',

    # Vocabulary
    'VocabularyItem', 'VocabularyAttempt', 'StudentVocabMastery',

    # Comprehension
    'ChunkComprehensionFocus', 'ComprehensionQuestion',
    'ComprehensionPracticeAttempt', 'ComprehensionTestAttempt',
    'ComprehensionQuestionAttempt',

    # Writing
    'WritingAcademicYear',
    'WritingStage',
    'WritingStageContent',
    'WritingAttempt',
    'WritingStageMastery',
    'WritingIntervention',

    # Pronunciation
    'PronunciationFocus', 'PronunciationAttempt', 'PronunciationMastery',

    # Unit Testing
    'UnitTestSession', 'UnitTestQuestion', 'UnitTestAnswer',
    'VocabularyUnitTestAttempt',
]