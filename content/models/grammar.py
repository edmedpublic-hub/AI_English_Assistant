# content/models/grammar.py

from django.db import models
from .core import Lesson, LessonChunk


# ============================================================
# Grammar: future-proof, scalable, and pedagogy-aligned models
# Teach → Exercise → Test, with granular logging and summaries
# ============================================================

class GrammarPoint(models.Model):
    """
    A single grammar concept taught within a lesson/chunk.
    Example: "Nouns", "Present Simple", "Relative Clauses".
    """
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="grammar_points"
    )
    chunk = models.ForeignKey(
        LessonChunk,
        on_delete=models.CASCADE,
        related_name="grammar_points",
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    explanation = models.TextField()   # Teaching content
    examples = models.TextField()      # Example sentences

    class Meta:
        indexes = [
            models.Index(fields=["lesson"]),
            models.Index(fields=["chunk"]),
            models.Index(fields=["title"]),
        ]
        ordering = ["lesson_id", "chunk_id", "title"]

    def __str__(self):
        return f"{self.lesson} — {self.title}"


class GrammarQuestion(models.Model):
    """
    A reusable exercise/test item linked to a GrammarPoint.
    Supports multiple question types and flexible options via JSON.
    """
    TYPE_MCQ = "mcq"
    TYPE_FILL = "fill"
    TYPE_REWRITE = "rewrite"

    QUESTION_TYPES = [
        (TYPE_MCQ, "Multiple Choice"),
        (TYPE_FILL, "Fill in the Blank"),
        (TYPE_REWRITE, "Rewrite"),
    ]

    grammar_point = models.ForeignKey(
        GrammarPoint,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    question_text = models.TextField()
    options = models.JSONField(null=True, blank=True)  # For MCQs or structured choices
    correct_answer = models.CharField(max_length=200)
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES, default=TYPE_MCQ)
    difficulty = models.PositiveSmallIntegerField(default=1)  # 1–5 scale (optional)

    class Meta:
        indexes = [
            models.Index(fields=["grammar_point"]),
            models.Index(fields=["question_type"]),
            models.Index(fields=["difficulty"]),
        ]
        ordering = ["grammar_point_id", "id"]

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.question_text[:60]}..."


class GrammarAttempt(models.Model):
    """
    Per-question attempt logging for analytics and review.
    Stores the selected answer and correctness for each question.
    """
    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="grammar_attempts",
        null=True, blank=True   # ✅ allow nulls for existing rows
    )
    grammar_question = models.ForeignKey(
        GrammarQuestion,
        on_delete=models.CASCADE,
        related_name="attempts",
        null=True, blank=True   # ✅ allow nulls for existing rows
    )
    selected_answer = models.CharField(max_length=200, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["grammar_question"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["is_correct"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        student_name = self.student.username if self.student else "Unknown Student"
        gp_title = self.grammar_question.grammar_point.title if self.grammar_question else "Unknown Grammar Point"
        return f"{student_name} — {gp_title} ({'✓' if self.is_correct else '✗'})"


class GrammarTestAttempt(models.Model):
    """
    Per-test summary for a GrammarPoint.
    Stores aggregate score and the full question set used in the test.
    """
    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="grammar_test_attempts",
        null=True, blank=True   # ✅ allow nulls for existing rows
    )
    grammar_point = models.ForeignKey(
        GrammarPoint,
        on_delete=models.CASCADE,
        related_name="test_attempts",
        null=True, blank=True   # ✅ allow nulls for existing rows
    )
    score_percent = models.IntegerField(null=True, blank=True)
    correct_answers = models.IntegerField(null=True, blank=True)
    total_questions = models.IntegerField(null=True, blank=True)
    questions_data = models.JSONField(null=True, blank=True)  # Entire test set for review
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["grammar_point"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["score_percent"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        student_name = self.student.username if self.student else "Unknown Student"
        gp_title = self.grammar_point.title if self.grammar_point else "Unknown Grammar Point"
        return f"{student_name} — {gp_title} ({self.score_percent or 0}%)"