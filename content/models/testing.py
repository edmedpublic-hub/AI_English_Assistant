from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from .core import LessonChunk, Lesson, Unit
from .vocabulary import VocabularyItem
from .grammar import GrammarConcept
from .punctuation import PunctuationMark
from .comprehension import BloomLevel


class UnitTestSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="unit_test_sessions"
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="test_sessions"
    )
    attempt_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="1, 2, or 3"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    score_percentage = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0
    )
    passed = models.BooleanField(default=False)
    domain_scores = models.JSONField(default=dict)
    test_data = models.JSONField(default=dict)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "unit", "attempt_number"],
                name="unique_unit_test_attempt_per_user"
            )
        ]
        indexes = [
            models.Index(fields=["user", "unit"]),
            models.Index(fields=["user", "passed"]),
            models.Index(fields=["user", "attempt_number"]),
            models.Index(fields=["started_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.total_questions > 0:
            self.score_percentage = (self.correct_answers / self.total_questions) * 100
            self.passed = self.score_percentage >= 70
        super().save(*args, **kwargs)

    def __str__(self):
        status = "✓" if self.passed else "✗"
        return f"{self.user.username} — Unit {self.unit.id} — Attempt {self.attempt_number} — {self.score_percentage:.1f}% {status}"


class UnitTestQuestion(models.Model):
    DOMAIN_CHOICES = [
        ('vocabulary', 'Vocabulary'),
        ('grammar', 'Grammar'),
        ('punctuation', 'Punctuation'),
        ('comprehension', 'Comprehension'),
        ('writing', 'Writing'),
        ('pronunciation', 'Pronunciation'),
    ]
    QUESTION_TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('short_answer', 'Short Answer'),
        ('matching', 'Matching'),
    ]

    session = models.ForeignKey(
        UnitTestSession,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    domain = models.CharField(max_length=20, choices=DOMAIN_CHOICES, db_index=True)
    vocabulary_item = models.ForeignKey(
        VocabularyItem, on_delete=models.SET_NULL, null=True, blank=True)
    grammar_concept = models.ForeignKey(
        GrammarConcept, on_delete=models.SET_NULL, null=True, blank=True)
    punctuation_mark = models.ForeignKey(
        PunctuationMark, on_delete=models.SET_NULL, null=True, blank=True)
    bloom_level = models.CharField(
        max_length=20, choices=BloomLevel.choices, null=True, blank=True)
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPE_CHOICES, default='mcq')
    question_text = models.TextField()
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField()
    difficulty = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    order = models.PositiveIntegerField()
    points = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["session", "order"]
        indexes = [
            models.Index(fields=["session", "domain"]),
            models.Index(fields=["session", "difficulty"]),
        ]

    def __str__(self):
        return f"{self.session} — Q{self.order} ({self.domain})"


class UnitTestAnswer(models.Model):
    question = models.ForeignKey(
        UnitTestQuestion, on_delete=models.CASCADE, related_name="answers")
    student_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["question", "is_correct"]),
        ]

    def __str__(self):
        return f"Answer to Q{self.question.order} — {'✓' if self.is_correct else '✗'}"


class VocabularyUnitTestAttempt(models.Model):
    """
    Tracks vocabulary chunk-level test attempts.
    unit_test_session is optional — chunk tests run independently
    of full unit tests.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vocab_unit_test_attempts"
    )
    # FIXED: nullable — chunk vocab tests run without a full UnitTestSession
    unit_test_session = models.ForeignKey(
        UnitTestSession,
        on_delete=models.CASCADE,
        related_name="vocabulary_attempts",
        null=True,
        blank=True
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, null=True, blank=True)
    chunk = models.ForeignKey(
        LessonChunk, on_delete=models.CASCADE, null=True, blank=True)
    score_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)])
    correct_answers = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    questions_data = models.JSONField(default=dict)
    answers_data = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "unit_test_session"]),
            models.Index(fields=["user", "lesson"]),
            models.Index(fields=["user", "chunk"]),
        ]

    def __str__(self):
        return f"{self.user} – Vocab Test – {self.score_percent}%"