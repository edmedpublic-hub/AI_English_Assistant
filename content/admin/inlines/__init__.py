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

# Writing inlines
from .writing import (
    WritingPromptInline,
    WritingPracticeAttemptInline,
    WritingTestAttemptInline,
    WritingTestAttemptDetailInline,
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
    'GrammarQuestionStackedInline',
    
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
    'WritingPromptInline',
    'WritingPracticeAttemptInline',
    'WritingTestAttemptInline',
    'WritingTestAttemptDetailInline',
    
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