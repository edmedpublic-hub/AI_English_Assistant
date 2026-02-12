from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from .core import LessonChunk


# ============================================================
# COMPREHENSION LAYER (Chunk-level Reading Focus)
# ============================================================

class BloomLevel(models.TextChoices):
    LITERAL = "literal", "Literal"
    INFERENTIAL = "inferential", "Inferential"
    EVALUATIVE = "evaluative", "Evaluative"


class ChunkComprehensionFocus(models.Model):
    """
    Represents how comprehension is taught in a specific chunk.
    Each focus aligns with Bloom's taxonomy levels.
    """

    chunk = models.ForeignKey(
        LessonChunk,
        on_delete=models.CASCADE,
        related_name="comprehension_focuses"
    )

    focus_title = models.CharField(max_length=200)
    focus_description = models.TextField()

    level = models.CharField(
        max_length=20,
        choices=BloomLevel.choices,
        default=BloomLevel.LITERAL
    )

    sequence_order = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Order of focus within the chunk (Literal → Inferential → Evaluative)"
    )

    class Meta:
        ordering = ["chunk_id", "sequence_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["chunk", "sequence_order"],
                name="unique_comprehension_focus_order_per_chunk"
            )
        ]
        indexes = [
            models.Index(fields=["chunk"]),
            models.Index(fields=["level"]),
        ]

    def __str__(self):
        return f"{self.chunk} → {self.focus_title} ({self.level})"


# ============================================================
# QUESTIONS
# ============================================================

class ComprehensionQuestion(models.Model):
    """
    Comprehension questions tied to a specific ChunkComprehensionFocus.
    """

    TYPE_MCQ = "mcq"
    TYPE_TRUE_FALSE = "true_false"
    TYPE_SHORT_ANSWER = "short_answer"
    TYPE_OPEN_ENDED = "open_ended"

    QUESTION_TYPES = [
        (TYPE_MCQ, "Multiple Choice"),
        (TYPE_TRUE_FALSE, "True/False"),
        (TYPE_SHORT_ANSWER, "Short Answer"),
        (TYPE_OPEN_ENDED, "Open Ended"),
    ]

    focus = models.ForeignKey(
        ChunkComprehensionFocus,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField()
    options = models.TextField(blank=True, null=True)
    correct_answer = models.CharField(max_length=255, blank=True, null=True)

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

    def clean(self):
        if self.question_type == self.TYPE_MCQ:
            if not self.options:
                raise ValidationError("MCQ questions must have options.")

            option_list = self.get_options_list()

            if len(option_list) < 2:
                raise ValidationError("MCQ questions must have at least two options.")

            if self.correct_answer not in option_list:
                raise ValidationError(
                    "Correct answer must exactly match one of the options."
                )
        elif self.question_type in [self.TYPE_TRUE_FALSE, self.TYPE_SHORT_ANSWER]:
            if not self.correct_answer or not self.correct_answer.strip():
                raise ValidationError("This question type must define a correct answer.")
        else:
            # Open-ended questions may not have a predefined correct answer
            self.correct_answer = None

    def get_options_list(self):
        if not self.options:
            return []
        return [opt.strip() for opt in self.options.splitlines() if opt.strip()]

    @property
    def parsed_options(self):
        return self.get_options_list()

    def __str__(self):
        return f"{self.focus.focus_title}: {self.question_text[:60]}"


# ============================================================
# ATTEMPTS & ANALYTICS
# ============================================================

class ComprehensionAttempt(models.Model):
    """
    Per-question logging for comprehension analytics.
    """

    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="comprehension_attempts"
    )

    question = models.ForeignKey(
        ComprehensionQuestion,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    selected_answer = models.CharField(max_length=255, blank=True)
    open_ended_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "question"],
                name="unique_comprehension_attempt_per_question"
            )
        ]
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["question"]),
            models.Index(fields=["is_correct"]),
            models.Index(fields=["attempted_at"]),
        ]

    def __str__(self):
        return f"{self.student.username} — Q{self.question_id}"