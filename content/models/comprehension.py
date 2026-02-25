from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings

from .core import LessonChunk


# ============================================================
# KNOWLEDGE LAYER (Bloom's Taxonomy)
# ============================================================

class BloomLevel(models.TextChoices):
    LITERAL = "literal", "Literal"
    INFERENTIAL = "inferential", "Inferential"
    EVALUATIVE = "evaluative", "Evaluative"


# ============================================================
# TEACHING LAYER (Chunk-level Reading Focus)
# ============================================================

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

    depth_level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        help_text="Difficulty level within this Bloom stage"
    )

    sequence_order = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Order of focus within the chunk (Literal → Inferential → Evaluative)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
            models.Index(fields=["depth_level"]),
        ]

    # 🔒 PEDAGOGICAL INTEGRITY GUARD
    def clean(self):
        expected_order = {
            BloomLevel.LITERAL: 1,
            BloomLevel.INFERENTIAL: 2,
            BloomLevel.EVALUATIVE: 3,
        }

        if self.sequence_order != expected_order.get(self.level):
            raise ValidationError(
                f"{self.level.capitalize()} focus must have "
                f"sequence_order {expected_order[self.level]}."
            )

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
    
    DIFFICULTY_CHOICES = [(i, str(i)) for i in range(1, 6)]

    focus = models.ForeignKey(
        ChunkComprehensionFocus,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField()
    options = models.TextField(
        blank=True, 
        null=True,
        help_text="For MCQ: One option per line"
    )
    correct_answer = models.CharField(max_length=255, blank=True, null=True)

    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPES,
        default=TYPE_MCQ
    )

    difficulty = models.PositiveSmallIntegerField(
        choices=DIFFICULTY_CHOICES,
        default=3
    )

    explanation = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["focus_id", "id"]
        indexes = [
            models.Index(fields=["focus"]),
            models.Index(fields=["question_type"]),
            models.Index(fields=["difficulty"]),
        ]

    # 🔒 DOMAIN VALIDATION
    def clean(self):
        if self.question_type == self.TYPE_MCQ:
            if not self.options:
                raise ValidationError("MCQ questions must have options.")

            option_list = self.get_options_list()

            if len(option_list) < 2:
                raise ValidationError("MCQ questions must have at least two options.")

            normalized_options = [o.strip().lower() for o in option_list]

            if not self.correct_answer or self.correct_answer.strip().lower() not in normalized_options:
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
# PRACTICE LAYER (Formative Assessment)
# ============================================================

class ComprehensionPracticeAttempt(models.Model):
    """
    Tracks practice attempts for comprehension.
    3 attempts max per cycle, 100% required to pass.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comprehension_practice_attempts"
    )

    focus = models.ForeignKey(
        ChunkComprehensionFocus,
        on_delete=models.CASCADE,
        related_name="practice_attempts"
    )

    # Attempt tracking (3 attempts max per cycle)
    attempt_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="1, 2, or 3"
    )
    cycle_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text="Increments when restarting after 3 failures"
    )

    # Performance
    score_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_passed = models.BooleanField(default=False)  # True if score = 100

    correct_answers = models.PositiveSmallIntegerField()
    total_questions = models.PositiveSmallIntegerField()

    # Questions snapshot
    questions_data = models.JSONField(
        default=dict,
        help_text="Stores questions and answers for this attempt"
    )

    # Timestamps
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "focus", "cycle_number", "attempt_number"],
                name="unique_comprehension_practice_per_cycle"
            )
        ]
        indexes = [
            models.Index(fields=["user", "focus"]),
            models.Index(fields=["user", "cycle_number"]),
            models.Index(fields=["is_passed"]),
            models.Index(fields=["attempted_at"]),
        ]

    def save(self, *args, **kwargs):
        """Auto-calculate pass status."""
        self.is_passed = (self.score_percent == 100)
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.user.username} — {self.focus.focus_title} — "
            f"Practice {self.attempt_number} ({self.score_percent}%)"
        )


# ============================================================
# TEST LAYER (Summative Assessment)
# ============================================================

class ComprehensionTestAttempt(models.Model):
    """
    Stores mastery test submissions for comprehension.
    3 attempts max per cycle, 100% required to pass.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comprehension_test_attempts"
    )

    focus = models.ForeignKey(
        ChunkComprehensionFocus,
        on_delete=models.CASCADE,
        related_name="test_attempts"
    )

    # Attempt tracking (3 attempts max per cycle)
    attempt_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="1, 2, or 3"
    )
    cycle_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text="Increments when restarting after 3 failures"
    )

    score_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_mastered = models.BooleanField(
        default=False,
        help_text="Automatically True when score_percent == 100."
    )

    total_questions = models.PositiveSmallIntegerField()
    correct_answers = models.PositiveSmallIntegerField()

    # Questions snapshot
    questions_data = models.JSONField(
        default=dict,
        help_text="Stores questions and answers for this attempt"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Comprehension Test Attempt"
        verbose_name_plural = "Comprehension Test Attempts"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "focus", "cycle_number", "attempt_number"],
                name="unique_comprehension_test_per_cycle"
            )
        ]
        indexes = [
            models.Index(fields=["user", "focus"]),
            models.Index(fields=["user", "focus", "is_mastered"]),
            models.Index(fields=["user", "cycle_number"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        """Auto-calculate mastery."""
        self.is_mastered = (self.score_percent == 100)
        super().save(*args, **kwargs)

    def __str__(self):
        status = "✓" if self.is_mastered else "✗"
        return (
            f"{self.user.username} — {self.focus.focus_title} — "
            f"Test {self.attempt_number} ({self.score_percent}%) {status}"
        )


# ============================================================
# PER-QUESTION ATTEMPTS (Detailed Analytics)
# ============================================================

class ComprehensionQuestionAttempt(models.Model):
    """
    Per-question logging with retry cycles for mastery learning.
    Tracks individual question responses within practice/test sessions.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comprehension_question_attempts"
    )

    question = models.ForeignKey(
        ComprehensionQuestion,
        on_delete=models.CASCADE,
        related_name="question_attempts"
    )

    # Link to practice or test attempt
    practice_attempt = models.ForeignKey(
        ComprehensionPracticeAttempt,
        on_delete=models.CASCADE,
        related_name="question_attempts",
        null=True,
        blank=True
    )

    test_attempt = models.ForeignKey(
        ComprehensionTestAttempt,
        on_delete=models.CASCADE,
        related_name="question_attempts",
        null=True,
        blank=True
    )

    # Cycle tracking
    cycle_number = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    attempt_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )

    # Answer data
    selected_answer = models.CharField(max_length=255, blank=True)
    open_ended_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)

    # Timestamps
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "question", "cycle_number", "attempt_number"],
                name="unique_comprehension_question_attempt_per_cycle"
            )
        ]
        indexes = [
            models.Index(fields=["user", "question"]),
            models.Index(fields=["user", "cycle_number"]),
            models.Index(fields=["practice_attempt"]),
            models.Index(fields=["test_attempt"]),
            models.Index(fields=["is_correct"]),
            models.Index(fields=["attempted_at"]),
        ]

    def __str__(self):
        return (
            f"{self.user.username} — Q{self.question_id} — "
            f"(cycle {self.cycle_number}, attempt {self.attempt_number}) — "
            f"{'✓' if self.is_correct else '✗'}"
        )