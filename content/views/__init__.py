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
)

# --- VOCABULARY VIEWS ---
# Ensure these folders (vocabulary/practice.py and vocabulary/test.py) exist
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
from .grammar.practice import grammar_practice
from .grammar.test import grammar_test

# NOTE: Punctuation, Writing, and Comprehension imports have been purged.
# Add them back only after the respective folders and functions are created.