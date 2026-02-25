# content/views/pronunciation/__init__.py

from .hub import chunk_pronunciation_view
from .teach import pronunciation_teach
from .practice import pronunciation_practice
from .result import pronunciation_result

__all__ = [
    "chunk_pronunciation_view",
    "pronunciation_teach",
    "pronunciation_practice",
    "pronunciation_result",
]