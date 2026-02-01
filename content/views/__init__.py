# content/views/__init__.py

from .core import (
    content_index,
    textbook_list,
    textbook_detail,
    unit_detail,
    lesson_detail,
)

from .chunk_core import (
    chunk_hub,
    chunk_vocabulary,
    chunk_comprehension,
    chunk_punctuation,
    chunk_writing,
    chunk_progress,
)

from .vocabulary.practice import (
    chunk_vocabulary_practice,
    chunk_vocab_fill,
    chunk_vocab_synonyms,
    chunk_vocab_antonyms,
)
from .vocabulary.test import (
    chunk_vocabulary_test,
    test_history,
    attempt_detail,
)

# --- REFACTORED GRAMMAR IMPORTS ---
from .grammar.hub import chunk_grammar_view
from .grammar.teach import grammar_teach
from .grammar.exercise import grammar_exercise
from .grammar.test import grammar_test
# ----------------------------------

from .punctuation_views import (
    PunctuationMarkViewSet,
    ChunkPunctuationFocusViewSet,
    PunctuationQuestionViewSet,
)