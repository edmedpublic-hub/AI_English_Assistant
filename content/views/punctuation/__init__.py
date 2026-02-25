# content/views/punctuation/__init__.py

from .hub import chunk_punctuation_view
from .teach import teach_punctuation_view
from .practice import punctuation_practice
from .test import punctuation_test
from .result import punctuation_test_result, punctuation_attempt_detail

__all__ = [
    "chunk_punctuation_view",
    "teach_punctuation_view",
    "punctuation_practice",
    "punctuation_test",
    "punctuation_test_result",
    "punctuation_attempt_detail",
]