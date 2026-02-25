from django.db.models import Exists, OuterRef

from content.models.comprehension import ComprehensionTestAttempt


def is_focus_mastered(student, focus):
    """
    Returns True if the student has ANY mastered test attempt
    for this comprehension focus.

    Query-efficient:
    Uses EXISTS instead of COUNT.
    """

    mastered_attempts = ComprehensionTestAttempt.objects.filter(
        user=student,
        focus=focus,
        is_mastered=True,
    )

    return mastered_attempts.exists()


def get_latest_test_attempt(student, focus):
    """
    Returns the most recent test attempt for display on result screens.
    """

    return (
        ComprehensionTestAttempt.objects
        .filter(user=student, focus=focus)
        .order_by("-created_at")
        .first()
    )
