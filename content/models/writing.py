# content/models/writing.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .core import LessonChunk, Unit

# ============================================================
# CHUNK-LEVEL FOCUS (Sentence / Short Writing Tasks)
# ============================================================

class ChunkWritingFocus(models.Model):
    """
    Represents how a writing stage is taught in a specific chunk.
    Example: Simple sentence practice in LessonChunk 3.
    """
    chunk = models.ForeignKey(
        LessonChunk,
        on_delete=models.CASCADE,
        related_name="writing_focuses"
    )

    focus_title = models.CharField(max_length=200)
    focus_description = models.TextField()

    depth_level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    sequence_order = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )

    class Meta:
        ordering = ["chunk_id", "sequence_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["chunk", "sequence_order"],
                name="unique_writing_focus_order_per_chunk"
            )
        ]
        indexes = [
            models.Index(fields=["chunk"]),
            models.Index(fields=["depth_level"]),
            models.Index(fields=["sequence_order"]),
        ]

    def __str__(self):
        return f"{self.chunk} → {self.focus_title}"


# ============================================================
# UNIT-LEVEL TASKS (Extended Writing: Paragraphs, Essays, Genres)
# ============================================================

class UnitWritingTask(models.Model):
    """
    Extended writing task tied to a Unit.
    Example: Essay writing in Unit 2.
    """
    STAGE_CHOICES = [
        ("paragraph", "Paragraph"),
        ("essay", "Essay"),
        ("academic_genre", "Academic/Professional Genre"),
    ]

    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="writing_tasks"
    )

    task_title = models.CharField(max_length=200)
    task_description = models.TextField()
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES)
    difficulty_level = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["unit_id", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["unit", "order"],
                name="unique_task_order_per_unit"
            )
        ]
        indexes = [
            models.Index(fields=["unit"]),
            models.Index(fields=["stage"]),
            models.Index(fields=["difficulty_level"]),
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"{self.unit} → {self.task_title} ({self.get_stage_display()})"


# ============================================================
# PROMPTS (Practice/Test Items)
# ============================================================

class WritingPrompt(models.Model):
    """
    WritingPrompt represents a specific exercise.
    Must be tied to either a ChunkWritingFocus OR a UnitWritingTask.
    """
    focus = models.ForeignKey(
        ChunkWritingFocus,
        on_delete=models.CASCADE,
        related_name="prompts",
        null=True,
        blank=True
    )
    task = models.ForeignKey(
        UnitWritingTask,
        on_delete=models.CASCADE,
        related_name="prompts",
        null=True,
        blank=True
    )

    prompt_text = models.TextField()
    expected_keywords = models.TextField(
        help_text="Comma-separated keywords expected in student responses",
        blank=True
    )
    rubric = models.JSONField(
        help_text="Rubric criteria stored as JSON (criterion: max_score)",
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["focus"]),
            models.Index(fields=["task"]),
        ]

    def clean(self):
        # Enforce exclusive linkage: must be linked to exactly one of focus or task
        if bool(self.focus) == bool(self.task):
            raise ValidationError("WritingPrompt must be linked to either a focus OR a task, not both.")

    def __str__(self):
        return f"Prompt {self.id}: {self.prompt_text[:60]}"


# ============================================================
# STUDENT RESPONSES
# ============================================================

class WritingResponse(models.Model):
    """
    Stores learner submissions for writing prompts.
    """
    prompt = models.ForeignKey(
        WritingPrompt,
        on_delete=models.CASCADE,
        related_name="responses"
    )
    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="writing_responses"
    )
    response_text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["prompt"]),
            models.Index(fields=["submitted_at"]),
        ]

    def __str__(self):
        return f"{self.student.username} → Prompt {self.prompt_id}"


# ============================================================
# ATTEMPTS & ANALYTICS
# ============================================================

class WritingAttempt(models.Model):
    """
    Per-response logging for analytics and diagnostics.
    """
    response = models.ForeignKey(
        WritingResponse,
        on_delete=models.CASCADE,
        related_name="attempts"
    )
    attempt_number = models.PositiveIntegerField(default=1)
    time_spent = models.DurationField(null=True, blank=True)
    hints_used = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["attempt_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["response", "attempt_number"],
                name="unique_attempt_per_response"
            )
        ]
        indexes = [
            models.Index(fields=["response"]),
            models.Index(fields=["attempt_number"]),
        ]

    def __str__(self):
        return f"Attempt {self.attempt_number} → Response {self.response_id}"


class WritingTestAttempt(models.Model):
    """
    Aggregate assessment result for a writing session.
    Mirrors GrammarTestAttempt.
    """
    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="writing_test_attempts"
    )
    prompt = models.ForeignKey(
        WritingPrompt,
        on_delete=models.CASCADE,
        related_name="test_attempts"
    )
    rubric_scores = models.JSONField(
        help_text="Stores rubric evaluation scores per criterion"
    )
    overall_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Aggregate score percentage for quick reporting"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "prompt"],
                name="unique_test_attempt_per_prompt"
            )
        ]
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["prompt"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.student.username} → Prompt {self.prompt_id} ({self.overall_score}%)"
    
    
# content/models/writing.py

from django.db import models
from django.conf import settings

class WritingPracticeAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    focus = models.ForeignKey("ChunkWritingFocus", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "focus")

    def __str__(self):
        return f"{self.student.username} → {self.focus.focus_title}"