"""
Public service interface for the comprehension domain.

This module exposes stable, high-level service functions that
views and other application layers are allowed to import.

Never import from internal service modules directly.
Always import from this package root instead.
"""

# Mastery
from .comprehension_mastery import is_focus_mastered

# Resolution / object loading
from .comprehension_resolution import (
    get_comprehension_objects,
    build_chunk_context,
)

__all__ = [
    "is_focus_mastered",
    "get_comprehension_objects",
    "build_chunk_context",
]
