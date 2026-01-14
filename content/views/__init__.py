# Ensure these imports exist so urls can resolve attributes on content.views
from .index import index
from .textbooks import textbook_list, textbook_detail
from .units import unit_list, unit_detail
from .lessons import lesson_list, lesson_detail
from .practice_page import *
from .practice_views import *
from .test_views import *
from .history_views import *



# Core chunk views
from .chunks_core import (
    chunk_detail,
    chunk_vocabulary,
    chunk_grammar,
    chunk_comprehension,
    chunk_punctuation,
    chunk_writing,
    chunk_progress,
)

