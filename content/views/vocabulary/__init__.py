# content/views/vocabulary/__init__.py
from .core import (
    get_vocab_context,
    _vocab_base_context,
)

from .practice import (
    chunk_vocabulary_practice,
    chunk_vocab_fill,
    chunk_vocab_synonyms,
    chunk_vocab_antonyms,
)

from .test import (
    chunk_vocabulary_test,
    test_history,
    attempt_detail,
)