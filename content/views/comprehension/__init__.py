# PATH: content/views/comprehension/__init__.py
# ACTION: Replace the entire existing file with this content.
#
# CHANGES FROM ORIGINAL:
#   - Removed ComprehensionTestResultsView (deleted from test.py)
#   - All other exports unchanged

from .hub      import chunk_comprehension_view
from .teach    import comprehension_teach_view
from .practice import ComprehensionPracticeView
from .test     import ComprehensionTestSubmitView
from .result   import (
    comprehension_result_view,
    comprehension_attempt_detail_view,
    comprehension_practice_result_view,
)
from .core import get_comprehension_objects, build_chunk_context