# content/views/__init__.py
# Centralised View Exports (Clean + Explicit)

from .lessons import (
    LessonViewSet,
    content_lesson_list,
    content_lesson_detail,
)

from .vocab import (
    VocabularyItemViewSet,
    content_vocab_list,
    content_vocab_item_detail,
)

from .grammar import (
    GrammarPointViewSet,
    ExtractGrammar,
    content_grammar_point_detail,
)

from .comprehension import (
    ComprehensionQuestionViewSet,
    content_comprehension_question_detail,
)

from .writing import (
    WritingTaskViewSet,
    SentenceAttemptViewSet,
    content_writing_task_detail,
)

from .student import (
    content_student_dashboard,
    content_student_attempts,
    content_student_comprehension_progress,
    content_student_writing_progress,
    content_student_vocab_progress,
    content_student_grammar_progress,
)

from .home import content_home


__all__ = [
    "LessonViewSet",
    "VocabularyItemViewSet",
    "GrammarPointViewSet",
    "ComprehensionQuestionViewSet",
    "WritingTaskViewSet",
    "SentenceAttemptViewSet",

    "ExtractGrammar",

    "content_lesson_list",
    "content_lesson_detail",
    "content_vocab_list",
    "content_vocab_item_detail",
    "content_comprehension_question_detail",
    "content_writing_task_detail",
    "content_grammar_point_detail",

    "content_student_dashboard",
    "content_student_attempts",
    "content_student_comprehension_progress",
    "content_student_writing_progress",
    "content_student_vocab_progress",
    "content_student_grammar_progress",

    "content_home",
]
