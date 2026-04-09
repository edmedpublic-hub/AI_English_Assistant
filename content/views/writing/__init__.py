# content/views/writing/__init__.py
#
# Exports all writing views for use in URL configuration.
#
# Import pattern in urls.py:
#
#   from content.views.writing import (
#       WritingHubView,
#       WritingTeachView,
#       WritingTeachSubmitView,
#       WritingPracticeView,
#       WritingPracticeSubmitView,
#       WritingInterventionFixView,
#       WritingTestView,
#       WritingTestSubmitView,
#       WritingTestResultView,
#   )

from .hub import WritingHubView

from .teach import (
    WritingTeachView,
    WritingTeachSubmitView,
)

from .practice import (
    WritingPracticeView,
    WritingPracticeSubmitView,
    WritingInterventionFixView,
)

from .test import (
    WritingTestView,
    WritingTestSubmitView,
    WritingTestResultView,
)

__all__ = [
    # Hub
    "WritingHubView",

    # Teach — Dissect phase
    "WritingTeachView",
    "WritingTeachSubmitView",

    # Practice — Imitate phase
    "WritingPracticeView",
    "WritingPracticeSubmitView",
    "WritingInterventionFixView",

    # Test — Produce phase
    "WritingTestView",
    "WritingTestSubmitView",
    "WritingTestResultView",
]