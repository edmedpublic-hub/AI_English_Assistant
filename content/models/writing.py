# content/models/writing.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    
    PROMPT_TYPE_CHOICES = [
        ('sentence', 'Sentence'),
        ('paragraph', 'Paragraph'),
        ('essay', 'Essay'),
    ]

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

    prompt_type = models.CharField(
        max_length=20,
        choices=PROMPT_TYPE_CHOICES,
        default='sentence'
    )
    
    prompt_text = models.TextField()
    
    # For automated checking (optional)
    expected_keywords = models.TextField(
        help_text="Comma-separated keywords expected in student responses",
        blank=True
    )
    
    # Rubric for scoring
    rubric = models.JSONField(
        help_text="Rubric criteria stored as JSON: {'criterion': {'max_score': 5, 'description': '...'}}",
        default=dict,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["focus"]),
            models.Index(fields=["task"]),
            models.Index(fields=["prompt_type"]),
        ]

    def clean(self):
        # Enforce exclusive linkage: must be linked to exactly one of focus or task
        if bool(self.focus) == bool(self.task):
            raise ValidationError("WritingPrompt must be linked to either a focus OR a task, not both.")

    def __str__(self):
        return f"Prompt {self.id}: {self.prompt_text[:60]}"


# ============================================================
# PRACTICE LAYER (Formative Assessment)
# ============================================================

class WritingPracticeAttempt(models.Model):
    """
    Tracks practice attempts for writing.
    3 attempts max per cycle.
    For chunk-level focuses (sentence-level writing).
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="writing_practice_attempts"
    )

    focus = models.ForeignKey(
        ChunkWritingFocus,
        on_delete=models.CASCADE,
        related_name="practice_attempts",
        null=True,
        blank=True
    )
    
    prompt = models.ForeignKey(
        WritingPrompt,
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
    
    # Student's response
    response_text = models.TextField()
    
    # Scoring (for automated/keyword-based scoring)
    keyword_match_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        help_text="Automated score based on keyword matching"
    )
    
    is_passed = models.BooleanField(
        default=False,
        help_text="True if score meets passing threshold (typically 100% for practice)"
    )
    
    # Metadata
    time_spent_seconds = models.PositiveIntegerField(null=True, blank=True)
    hints_used = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "prompt", "cycle_number", "attempt_number"],
                name="unique_writing_practice_per_cycle"
            )
        ]
        indexes = [
            models.Index(fields=["user", "focus"]),
            models.Index(fields=["user", "prompt"]),
            models.Index(fields=["user", "cycle_number"]),
            models.Index(fields=["is_passed"]),
        ]

    def save(self, *args, **kwargs):
        """Auto-calculate pass status (100% for keyword-based)."""
        if self.keyword_match_score is not None:
            self.is_passed = (self.keyword_match_score == 100)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} — {self.prompt} — Practice {self.attempt_number}"


# ============================================================
# TEST LAYER (Summative Assessment)
# ============================================================

class WritingTestAttempt(models.Model):
    """
    Aggregate assessment result for a writing test session.
    3 attempts max per cycle.
    For both chunk-level and unit-level tasks.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="writing_test_attempts"
    )

    # Can be linked to either a focus (chunk-level) or a task (unit-level)
    focus = models.ForeignKey(
        ChunkWritingFocus,
        on_delete=models.CASCADE,
        related_name="test_attempts",
        null=True,
        blank=True
    )
    
    task = models.ForeignKey(
        UnitWritingTask,
        on_delete=models.CASCADE,
        related_name="test_attempts",
        null=True,
        blank=True
    )
    
    prompt = models.ForeignKey(
        WritingPrompt,
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
    
    # Student's response
    response_text = models.TextField()
    
    # Scoring
    rubric_scores = models.JSONField(
        help_text="Stores rubric evaluation scores per criterion",
        default=dict
    )
    
    overall_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Aggregate score percentage"
    )
    
    is_mastered = models.BooleanField(
        default=False,
        help_text="True if overall_score == 100 (for chunk-level) or >=70 (for unit-level)"
    )
    
    feedback = models.TextField(
        blank=True,
        help_text="Teacher or AI feedback"
    )
    
    # Metadata
    time_spent_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "prompt", "cycle_number", "attempt_number"],
                name="unique_writing_test_per_cycle"
            ),
            # Ensure linked to either focus or task, not both
            models.CheckConstraint(
                check=(
                    models.Q(focus__isnull=False, task__isnull=True) |
                    models.Q(focus__isnull=True, task__isnull=False)
                ),
                name="either_focus_or_task"
            )
        ]
        indexes = [
            models.Index(fields=["user", "focus"]),
            models.Index(fields=["user", "task"]),
            models.Index(fields=["user", "prompt"]),
            models.Index(fields=["user", "cycle_number"]),
            models.Index(fields=["is_mastered"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        """Auto-calculate mastery based on context."""
        if self.focus is not None:
            # Chunk-level: 100% required
            self.is_mastered = (self.overall_score == 100)
        else:
            # Unit-level: 70% required
            self.is_mastered = (self.overall_score >= 70)
        super().save(*args, **kwargs)

    def __str__(self):
        context = self.focus if self.focus else self.task
        status = "✓" if self.is_mastered else "✗"
        return f"{self.user.username} — {context} — Test {self.attempt_number} ({self.overall_score}%) {status}"


# ============================================================
# LEGACY MODELS (Consolidated)
# ============================================================

# The following models are replaced by the above:
# - WritingResponse (now part of WritingPracticeAttempt/WritingTestAttempt)
# - WritingAttempt (now integrated with attempt_number/cycle_number)
# - WritingPracticeAttempt (enhanced version above)
# - WritingTestAttempt (enhanced version above)