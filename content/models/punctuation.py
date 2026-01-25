# content/models/punctuation.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .core import LessonChunk


# ============================================================
# KNOWLEDGE LAYER (Global Punctuation Curriculum)
# ============================================================

class PunctuationMark(models.Model):
    """
    A global punctuation symbol.
    Examples: Period, Comma, Apostrophe, Semicolon, Quotation Marks.
    """
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=10, unique=True)  # e.g. ".", ",", "?"
    description = models.TextField(blank=True)

    order_index = models.PositiveIntegerField(
        help_text="Controls global learning progression"
    )

    class Meta:
        ordering = ["order_index", "name"]
        indexes = [
            models.Index(fields=["symbol"]),
            models.Index(fields=["order_index"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class PunctuationRule(models.Model):
    """
    Rule describing correct use of a punctuation mark.
    Example: 'Use a comma after introductory phrases.'
    """
    mark = models.ForeignKey(
        PunctuationMark,
        on_delete=models.CASCADE,
        related_name="rules"
    )

    rule_text = models.TextField()

    def __str__(self):
        return f"{self.mark.symbol}: {self.rule_text[:60]}"


class PunctuationExample(models.Model):
    """
    Example sentence illustrating punctuation usage.
    """
    rule = models.ForeignKey(
        PunctuationRule,
        on_delete=models.CASCADE,
        related_name="examples"
    )

    sentence = models.TextField()

    def __str__(self):
        return self.sentence[:80]


# ============================================================
# TEACHING LAYER (Chunk-level Focus)
# ============================================================

class ChunkPunctuationFocus(models.Model):
    """
    How punctuation is taught inside a specific lesson chunk.
    Enables spiral learning and controlled progression.
    """

    chunk = models.ForeignKey(
        LessonChunk,
        on_delete=models.CASCADE,
        related_name="punctuation_focuses"
    )

    mark = models.ForeignKey(
        PunctuationMark,
        on_delete=models.CASCADE,
        related_name="teaching_instances"
    )

    focus_title = models.CharField(
        max_length=200,
        help_text="e.g. 'Comma in Lists', 'Apostrophe for Possession'"
    )

    focus_description = models.TextField()

    depth_level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 = Introductory, 5 = Advanced"
    )

    sequence_order = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Max 3 punctuation focuses per chunk"
    )

    class Meta:
        ordering = ["chunk_id", "sequence_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["chunk", "sequence_order"],
                name="unique_punctuation_order_per_chunk"
            )
        ]
        indexes = [
            models.Index(fields=["chunk"]),
            models.Index(fields=["mark"]),
            models.Index(fields=["depth_level"]),
        ]

    def __str__(self):
        return f"{self.chunk} → {self.focus_title}"


# ============================================================
# PRACTICE QUESTIONS
# ============================================================

class PunctuationQuestion(models.Model):
    """
    Practice questions tied to a specific chunk-level focus.
    """

    TYPE_MCQ = "mcq"
    TYPE_INSERT = "insert"
    TYPE_FIX = "fix"
    TYPE_IDENTIFY = "identify"

    QUESTION_TYPES = [
        (TYPE_MCQ, "Multiple Choice"),
        (TYPE_INSERT, "Insert Correct Punctuation"),
        (TYPE_FIX, "Correct the Sentence"),
        (TYPE_IDENTIFY, "Identify Error"),
    ]

    focus = models.ForeignKey(
        ChunkPunctuationFocus,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField()
    options = models.JSONField(null=True, blank=True)
    correct_answer = models.CharField(max_length=255)

    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPES,
        default=TYPE_MCQ
    )

    difficulty = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ["focus_id", "id"]
        indexes = [
            models.Index(fields=["focus"]),
            models.Index(fields=["question_type"]),
            models.Index(fields=["difficulty"]),
        ]

    def __str__(self):
        return f"{self.focus.focus_title}: {self.question_text[:60]}"


# ============================================================
# ATTEMPTS & ANALYTICS
# ============================================================

class PunctuationAttempt(models.Model):
    """
    Logs individual student responses for diagnostics.
    """

    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="punctuation_attempts"
    )

    question = models.ForeignKey(
        PunctuationQuestion,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    selected_answer = models.CharField(max_length=255, blank=True)
    is_correct = models.BooleanField(default=False)

    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["question"]),
            models.Index(fields=["is_correct"]),
        ]

    def __str__(self):
        return f"{self.student.username} — Q{self.question_id}"


class PunctuationTestAttempt(models.Model):
    """
    Aggregate test result for a punctuation session.
    """

    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="punctuation_test_attempts"
    )

    focus = models.ForeignKey(
        ChunkPunctuationFocus,
        on_delete=models.CASCADE,
        related_name="test_attempts"
    )

    score_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    correct_answers = models.PositiveSmallIntegerField()
    total_questions = models.PositiveSmallIntegerField()

    questions_snapshot = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["focus"]),
        ]

    def __str__(self):
        return f"{self.student.username} — {self.focus.focus_title} ({self.score_percent}%)"