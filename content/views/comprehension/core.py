# content/views/comprehension/core.py

"""
Temporary compatibility layer.

This file now delegates comprehension resolution and context
building to the service layer while preserving existing imports
across the codebase.

This allows safe, reversible architectural migration toward a
proper service-driven production structure.
"""

from content.services.comprehension.comprehension_resolution import (
    get_comprehension_objects,
    build_chunk_context,
)

__all__ = [
    "get_comprehension_objects",
    "build_chunk_context",
]
