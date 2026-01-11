# Ensure these imports exist so urls can resolve attributes on content.views
from .index import index
from .textbooks import textbook_list, textbook_detail
from .units import unit_list, unit_detail
from .lessons import lesson_list, lesson_detail

# Core chunk views
from .chunks_core import (
    chunk_detail,
    chunk_vocabulary,
    chunk_grammar,
    chunk_comprehension,
    chunk_punctuation,
    chunk_writing,
    chunk_progress,
)

# Practice chunk views
from .chunks_practice import (
    chunk_vocabulary_practice,
    chunk_vocab_fill,
    chunk_vocab_synonyms,
    chunk_vocab_antonyms,
    chunk_vocabulary_test,
)