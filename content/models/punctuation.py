from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from .core import LessonChunk


# ============================================================
# KNOWLEDGE LAYER (Global Punctuation Curriculum)
# ============================================================

class PunctuationMark(models.Model):
    """A global punctuation symbol (e.g., Period, Comma)."""
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(
        help_text="Global learning sequence. Lower numbers appear first."
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order_index"]
        verbose_name = "1. Global Punctuation Mark"
        indexes = [models.Index(fields=['order_index'])]

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class PunctuationRule(models.Model):
    """Specific grammar rule for a punctuation mark (e.g., 'Use comma before FANBOYS')."""
    mark = models.ForeignKey(PunctuationMark, on_delete=models.CASCADE, related_name="rules")
    rule_text = models.TextField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "2. Global Punctuation Rule"
        indexes = [
            models.Index(fields=["mark"]),
        ]

    def __str__(self):
        return f"{self.mark.symbol}: {self.rule_text[:60]}"


class PunctuationExample(models.Model):
    """Sentence illustrating a rule for the 'Study Theory' section."""
    rule = models.ForeignKey(PunctuationRule, on_delete=models.CASCADE, related_name="examples")
    sentence = models.TextField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["rule"]),
        ]

    def __str__(self):
        return self.sentence[:80]


# ============================================================
# TEACHING LAYER (Chunk-level Focus)
# ============================================================

class ChunkPunctuationFocus(models.Model):
    """Defines what punctuation is taught in a specific Lesson Chunk."""
    chunk = models.ForeignKey(
        LessonChunk, 
        on_delete=models.CASCADE, 
        related_name="punctuation_focuses"
    )
    mark = models.ForeignKey(PunctuationMark, on_delete=models.PROTECT)
    focus_title = models.CharField(max_length=200, help_text="e.g., Using Commas in a List")
    focus_description = models.TextField()
    
    depth_level = models.PositiveSmallIntegerField(
        default=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Difficulty Level (1: Beginner, 5: Advanced)"
    )
    sequence_order = models.PositiveSmallIntegerField(
        default=1, 
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Order within the chunk (1, 2, or 3)."
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["chunk", "sequence_order"]
        verbose_name = "3. Chunk Punctuation Focus"
        verbose_name_plural = "3. Chunk Punctuation Focuses"
        constraints = [
            models.UniqueConstraint(
                fields=["chunk", "sequence_order"], 
                name="unique_punctuation_focus_order_per_chunk"
            ),
            # Keep existing mark constraint if useful
            models.UniqueConstraint(
                fields=["chunk", "mark"], 
                name="unique_punc_mark_per_chunk"
            ),
        ]
        indexes = [
            models.Index(fields=["chunk", "depth_level"]),
            models.Index(fields=["mark"]),
        ]

    def __str__(self):
        return f"Chunk {self.chunk.id} - {self.focus_title}"


class ChunkPunctuationFocusRule(models.Model):
    """Links specific global rules to a lesson focus."""
    focus = models.ForeignKey(
        ChunkPunctuationFocus, 
        on_delete=models.CASCADE, 
        related_name="focus_rules"
    )
    rule = models.ForeignKey(
        PunctuationRule, 
        on_delete=models.PROTECT
    )  # Prevents curriculum deletion errors
    order = models.PositiveSmallIntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "4. Focus-Rule Mapping"
        constraints = [
            models.UniqueConstraint(
                fields=["focus", "rule"], 
                name="unique_rule_per_focus_mapping"
            )
        ]
        indexes = [
            models.Index(fields=["focus", "order"]),
        ]


# ============================================================
# PRACTICE LAYER (Formative Assessment)
# ============================================================

class PunctuationPracticeAttempt(models.Model):
    """
    Tracks practice attempts (not tests).
    3 attempts max, reshuffled, 100% required.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="punctuation_practice_attempts"
    )
    
    focus = models.ForeignKey(
        ChunkPunctuationFocus,
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
    
    # Questions snapshot
    questions_data = models.JSONField(
        default=dict,
        help_text="Stores questions and answers for this attempt"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "focus", "cycle_number", "attempt_number"],
                name="unique_punctuation_practice_per_cycle"
            )
        ]
        indexes = [
            models.Index(fields=["user", "focus"]),
            models.Index(fields=["user", "cycle_number"]),
            models.Index(fields=["is_passed"]),
        ]
    
    def save(self, *args, **kwargs):
        """Auto-calculate pass status."""
        self.is_passed = (self.score_percent == 100)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} — {self.focus} — Practice {self.attempt_number}"


# ============================================================
# TEST LAYER (Summative Assessment)
# ============================================================

class PunctuationTestAttempt(models.Model):
    """
    Stores mastery test submissions.
    3 attempts max, reshuffled, 100% required.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="punctuation_test_attempts"
    )
    
    focus = models.ForeignKey(
        ChunkPunctuationFocus,
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
    
    # Performance
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
        verbose_name = "Punctuation Test Attempt"
        verbose_name_plural = "Punctuation Test Attempts"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "focus", "cycle_number", "attempt_number"],
                name="unique_punctuation_test_per_cycle"
            )
        ]
        indexes = [
            models.Index(fields=["user", "focus"]),
            models.Index(fields=["user", "focus", "is_mastered"]),
            models.Index(fields=["user", "cycle_number"]),
        ]

    def save(self, *args, **kwargs):
        """Auto-calculate mastery."""
        self.is_mastered = (self.score_percent == 100)
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "✓" if self.is_mastered else "✗"
        return f"{self.user.username} — {self.focus} — {self.score_percent}% {status}"


# ============================================================
# QUESTIONS (Reusable across Practice & Test)
# ============================================================

class PunctuationQuestion(models.Model):
    """Questions for practice/tests."""
    
    TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'), 
        ('insert', 'Insert Mark'), 
        ('fix', 'Correct Sentence')
    ]
    
    DIFFICULTY_CHOICES = [(i, str(i)) for i in range(1, 6)]

    focus = models.ForeignKey(
        ChunkPunctuationFocus, 
        on_delete=models.CASCADE, 
        related_name="questions"
    )
    
    question_text = models.TextField()
    
    # Staff-friendly pipe separator '|'
    options = models.TextField(
        blank=True, 
        help_text="For MCQ: Separate options with '|'. Example: Option A | Option B"
    )
    
    correct_answer = models.CharField(max_length=255)
    question_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='mcq'
    )
    
    difficulty = models.PositiveSmallIntegerField(
        choices=DIFFICULTY_CHOICES,
        default=3
    )
    
    explanation = models.TextField(
        blank=True, 
        help_text="Shown to help the student learn from mistakes."
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["focus", "id"]
        verbose_name = "5. Punctuation Question"
        indexes = [
            models.Index(fields=["focus", "difficulty"]),
            models.Index(fields=["question_type"]),
        ]

    def __str__(self):
        return f"{self.question_type.upper()} - {self.question_text[:40]}"

    @property
    def options_list(self):
        if self.options:
            return [opt.strip() for opt in self.options.split('|') if opt.strip()]
        return []
    
    def clean(self):
        """Validate MCQ questions have correct answer in options."""
        from django.core.exceptions import ValidationError
        
        if self.question_type == 'mcq':
            if not self.options:
                raise ValidationError("MCQ questions must have options.")
            
            options = self.options_list
            if len(options) < 2:
                raise ValidationError("MCQ questions must have at least two options.")
            
            if self.correct_answer not in options:
                raise ValidationError("Correct answer must match one of the options.")