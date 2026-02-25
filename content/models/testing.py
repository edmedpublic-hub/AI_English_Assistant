from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from .core import LessonChunk, Lesson, Unit
from .vocabulary import VocabularyItem
from .grammar import GrammarConcept
from .punctuation import PunctuationMark
from .comprehension import BloomLevel


# ============================================================
# UNIT TEST SYSTEM (Comprehensive Assessment)
# Covers all domains taught in a unit: Vocabulary, Grammar,
# Punctuation, Comprehension, Writing, Pronunciation
# ============================================================

class UnitTestSession(models.Model):
    """
    Represents one complete unit test attempt.
    3 attempts maximum, 70% required to pass.
    """
    
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
    
    # Attempt tracking (3 attempts max)
    attempt_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="1, 2, or 3"
    )
    
    # Session timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Overall scores
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    score_percentage = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0
    )
    
    # Pass/fail (70% threshold)
    passed = models.BooleanField(default=False)
    
    # Domain-wise breakdown
    domain_scores = models.JSONField(
        default=dict,
        help_text="Breakdown by domain: {'vocabulary': 80, 'grammar': 70, ...}"
    )
    
    # Complete snapshot of the test
    test_data = models.JSONField(
        default=dict,
        help_text="Complete test structure with questions and correct answers"
    )
    
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
        """Auto-calculate pass/fail based on 70% threshold."""
        if self.total_questions > 0:
            self.score_percentage = (self.correct_answers / self.total_questions) * 100
            self.passed = self.score_percentage >= 70
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "✓" if self.passed else "✗"
        return f"{self.user.username} — Unit {self.unit.id} — Attempt {self.attempt_number} — {self.score_percentage:.1f}% {status}"


class UnitTestQuestion(models.Model):
    """
    Individual question within a unit test.
    Can come from any domain.
    """
    
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
    
    # Domain identification
    domain = models.CharField(
        max_length=20,
        choices=DOMAIN_CHOICES,
        db_index=True
    )
    
    # Source reference (optional, for analytics)
    vocabulary_item = models.ForeignKey(
        VocabularyItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If vocabulary question, which item?"
    )
    grammar_concept = models.ForeignKey(
        GrammarConcept,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If grammar question, which concept?"
    )
    punctuation_mark = models.ForeignKey(
        PunctuationMark,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If punctuation question, which mark?"
    )
    bloom_level = models.CharField(
        max_length=20,
        choices=BloomLevel.choices,
        null=True,
        blank=True,
        help_text="If comprehension question, which Bloom's level?"
    )
    
    # Question content
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='mcq'
    )
    question_text = models.TextField()
    
    # For MCQ: options stored as JSON array
    options = models.JSONField(
        default=list,
        blank=True,
        help_text="For MCQ: ['Option A', 'Option B', 'Option C', 'Option D']"
    )
    
    correct_answer = models.TextField(
        help_text="The correct answer for grading"
    )
    
    # Metadata
    difficulty = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    order = models.PositiveIntegerField(
        help_text="Question order within the test"
    )
    points = models.PositiveSmallIntegerField(
        default=1,
        help_text="Points awarded for correct answer"
    )
    
    class Meta:
        ordering = ["session", "order"]
        indexes = [
            models.Index(fields=["session", "domain"]),
            models.Index(fields=["session", "difficulty"]),
        ]
    
    def __str__(self):
        return f"{self.session} — Q{self.order} ({self.domain})"


class UnitTestAnswer(models.Model):
    """
    Stores student's answer for each test question.
    """
    
    question = models.ForeignKey(
        UnitTestQuestion,
        on_delete=models.CASCADE,
        related_name="answers"
    )
    
    student_answer = models.TextField(
        help_text="The answer provided by the student"
    )
    is_correct = models.BooleanField(default=False)
    
    answered_at = models.DateTimeField(auto_now_add=True)
    time_taken_seconds = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    
    class Meta:
        indexes = [
            models.Index(fields=["question", "is_correct"]),
        ]
    
    def __str__(self):
        return f"Answer to Q{self.question.order} — {'✓' if self.is_correct else '✗'}"


# ============================================================
# DOMAIN-SPECIFIC TEST ATTEMPTS (For backward compatibility)
# These mirror the patterns in other modules but feed into unit tests
# ============================================================

class VocabularyUnitTestAttempt(models.Model):
    """
    Tracks vocabulary portion of unit tests.
    Maintained for analytics and detailed tracking.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vocab_unit_test_attempts"
    )
    
    unit_test_session = models.ForeignKey(
        UnitTestSession,
        on_delete=models.CASCADE,
        related_name="vocabulary_attempts"
    )
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    chunk = models.ForeignKey(
        LessonChunk,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    score_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    correct_answers = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    
    questions_data = models.JSONField(
        default=dict,
        help_text="Snapshot of vocabulary questions and answers"
    )
    answers_data = models.JSONField(
        default=list,
        help_text="Snapshot of student's answers for this attempt"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "unit_test_session"]),
            models.Index(fields=["user", "lesson"]),
            models.Index(fields=["user", "chunk"]),
        ]
    
    def __str__(self):
        return f"{self.user} – Unit Test Vocab – {self.score_percent}%"