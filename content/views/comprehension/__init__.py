# content/views/comprehension/__init__.py
"""
Comprehension views package.
Implements the Teach → Practice → Test → Result loop for comprehension,
mirroring the grammar and punctuation modules.
"""

from .core import ComprehensionFocusListView, ComprehensionQuestionListView
from .hub import ComprehensionHubView
from .teach import ComprehensionTeachView
from .practice import ComprehensionPracticeView
from .test import ComprehensionTestResultsView

__all__ = [
    "ComprehensionFocusListView",
    "ComprehensionQuestionListView",
    "ComprehensionHubView",
    "ComprehensionTeachView",
    "ComprehensionPracticeView",
    "ComprehensionTestResultsView",
]