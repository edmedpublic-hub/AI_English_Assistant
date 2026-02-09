# content/views/punctuation/__init__.py
"""
Punctuation Views Package

This module exposes the main views for the punctuation curriculum:
- Hub (overview of focuses)
- Teach (rules + examples)
- Practice (interactive exercises)
- Test (final mastery evaluation)

Importing from this package ensures consistent namespacing.
"""

from .hub import chunk_punctuation_view
from .teach import teach_punctuation_view
from .practice import punctuation_practice
from .test import punctuation_test
from .test import punctuation_test_result

__all__ = [
    "chunk_punctuation_view",
    "teach_punctuation_view",
    "punctuation_practice",
    "punctuation_test",
    punctuation_test_result
    
]