# content/views/comprehension/__init__.py

# Hub view
from .hub import chunk_comprehension_view

# Teach / Practice / Test views
from .teach import comprehension_teach_view
from .practice import ComprehensionPracticeView
from .test import ComprehensionTestSubmitView, ComprehensionTestResultsView

# Result views
from .result import (
    comprehension_result_view,
    comprehension_attempt_detail_view,
    comprehension_practice_result_view,
)

# Core helpers (functions, not views)
from .core import get_comprehension_objects, build_chunk_context