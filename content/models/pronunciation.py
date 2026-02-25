from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from .core import LessonChunk


# ============================================================
# 9. PRONUNCIATION
# ============================================================

class PronunciationFocus(models.Model):
    """
    Teaching layer for pronunciation.
    Links phonemes and stress patterns to chunks.
    """
    chunk = models.ForeignKey(
        LessonChunk,
        on_delete=models.CASCADE,
        related_name="pronunciation_focuses"
    )

    focus_title = models.CharField(max_length=200)
    focus_description = models.TextField()

    sequence_order = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Order of focus within the chunk (1, 2, or 3)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["chunk_id", "sequence_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["chunk", "sequence_order"],
                name="unique_pronunciation_focus_order_per_chunk"
            )
        ]
        indexes = [
            models.Index(fields=["chunk"]),
        ]

    def __str__(self):
        return f"{self.chunk} → {self.focus_title}"


class PronunciationAttempt(models.Model):
    """
    Tracks student pronunciation attempts with AI feedback.
    3 attempts maximum per focus, with reshuffled content each time.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pronunciation_attempts"
    )

    focus = models.ForeignKey(
        PronunciationFocus,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    # Attempt tracking (3 attempts max per cycle)
    attempt_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        default=1,
        help_text="1, 2, or 3"
    )
    cycle_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text="Increments when restarting after 3 failures"
    )

    # Core data
    recording = models.FileField(
        upload_to="student_audio/",
        blank=True,
        null=True
    )
    ai_feedback = models.TextField(blank=True)
    ai_score = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Practice vs Test distinction
    attempt_type = models.CharField(
        max_length=10,
        choices=[
            ('practice', 'Practice'),
            ('test', 'Test'),
        ],
        default='practice'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "focus", "cycle_number", "attempt_number"],
                name="unique_pronunciation_attempt_per_cycle"
            )
        ]
        indexes = [
            models.Index(fields=["user", "focus"]),
            models.Index(fields=["user", "cycle_number"]),
            models.Index(fields=["attempt_type"]),
        ]

    @property
    def is_passed(self):
        """Pass if score >= 90"""
        if self.ai_score is None:
            return False
        return self.ai_score >= 90

    def __str__(self):
        return f"{self.user.username} — {self.focus} — Attempt {self.attempt_number}"


class PronunciationMastery(models.Model):
    """
    Tracks current mastery state for pronunciation focuses.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pronunciation_mastery"
    )

    focus = models.ForeignKey(
        PronunciationFocus,
        on_delete=models.CASCADE,
        related_name="mastery_records"
    )

    # Statistics
    total_attempts = models.PositiveIntegerField(default=0)
    best_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Mastery flag (True if any attempt scored >= 90)
    is_mastered = models.BooleanField(default=False)

    # Timestamps
    last_attempted = models.DateTimeField(null=True, blank=True)
    mastered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "focus"],
                name="unique_user_pronunciation_mastery"
            )
        ]
        indexes = [
            models.Index(fields=["user", "is_mastered"]),
        ]

    def __str__(self):
        status = "Mastered" if self.is_mastered else "Learning"
        return f"{self.user.username} — {self.focus} — {status}"