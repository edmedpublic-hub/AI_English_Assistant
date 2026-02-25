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
    #GrammarQuestionAttemptAdmin
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

# Writing admin
from .writing import (
    ChunkWritingFocusAdmin, UnitWritingTaskAdmin, WritingPromptAdmin,
    WritingPracticeAttemptAdmin, WritingTestAttemptAdmin
)

# Pronunciation admin
from .pronunciation import (
    PronunciationFocusAdmin, PronunciationAttemptAdmin, PronunciationMasteryAdmin
)

# Testing admin (Unit Tests) - Commented out until vocabulary testing models are implemented
# from .testing import (
#     UnitTestSessionAdmin, UnitTestQuestionAdmin, UnitTestAnswerAdmin,
#     VocabularyUnitTestAttemptAdmin
# )


__all__ = [
    # Core
    'TextbookAdmin', 'UnitAdmin', 'LessonAdmin', 'LessonChunkAdmin',
    
    # Grammar
    'GrammarConceptAdmin', 'GrammarRuleAdmin', 'GrammarExampleAdmin',
    'ChunkGrammarFocusAdmin', 'GrammarQuestionAdmin',
    'GrammarPracticeAttemptAdmin', 'GrammarTestAttemptAdmin',
    'GrammarQuestionAttemptAdmin',
    
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
    'ChunkWritingFocusAdmin', 'UnitWritingTaskAdmin', 'WritingPromptAdmin',
    'WritingPracticeAttemptAdmin', 'WritingTestAttemptAdmin',
    
    # Pronunciation
    'PronunciationFocusAdmin', 'PronunciationAttemptAdmin', 'PronunciationMasteryAdmin',
    
    # Testing - Commented out until models exist
    # 'UnitTestSessionAdmin', 'UnitTestQuestionAdmin', 'UnitTestAnswerAdmin',
    # 'VocabularyUnitTestAttemptAdmin',
]