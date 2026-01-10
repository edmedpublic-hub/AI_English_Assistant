# Ensure these imports exist so urls can resolve attributes on content.views
from .index import index
from .textbooks import textbook_list, textbook_detail
from .units import unit_list, unit_detail
from .lessons import lesson_list, lesson_detail
from .chunks import (
    chunk_detail,
    chunk_vocabulary,
    chunk_grammar,
    chunk_comprehension,
    chunk_punctuation,
    chunk_writing,
    chunk_progress,
    chunk_vocabulary_practice,
    chunk_vocabulary_test,
)