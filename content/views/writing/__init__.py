# content/views/writing/__init__.py

from .core import _chunk_context, get_writing_objects
from .hub import chunk_writing_view
from .teach import writing_teach
from .practice import writing_practice
from .test import writing_test

__all__ = [
    "_chunk_context",
    "get_writing_objects",
    "chunk_writing_view",
    "writing_teach",
    "writing_practice",
    "writing_test",
]