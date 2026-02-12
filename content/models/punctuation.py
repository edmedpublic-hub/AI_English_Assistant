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
    last_updated = models.DateTimeField(auto_now=True)

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

    class Meta:
        verbose_name = "2. Global Punctuation Rule"

    def __str__(self):
        return f"{self.mark.symbol}: {self.rule_text[:60]}"


class PunctuationExample(models.Model):
    """Sentence illustrating a rule for the 'Study Theory' section."""
    rule = models.ForeignKey(PunctuationRule, on_delete=models.CASCADE, related_name="examples")
    sentence = models.TextField()

    def __str__(self):
        return self.sentence[:80]


# ============================================================
# TEACHING LAYER (Chunk-level Focus)
# ============================================================

class ChunkPunctuationFocus(models.Model):
    """Defines what punctuation is taught in a specific Lesson Chunk."""
    chunk = models.ForeignKey(LessonChunk, on_delete=models.CASCADE, related_name="punctuation_focuses")
    mark = models.ForeignKey(PunctuationMark, on_delete=models.PROTECT)
    focus_title = models.CharField(max_length=200, help_text="e.g., Using Commas in a List")
    focus_description = models.TextField()
    
    depth_level = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Difficulty Level (1: Beginner, 5: Advanced)"
    )
    sequence_order = models.PositiveSmallIntegerField(
        default=1, help_text="Order within the chunk (1, 2, or 3)."
    )

    class Meta:
        ordering = ["chunk", "sequence_order"]
        verbose_name = "3. Chunk Punctuation Focus"
        verbose_name_plural = "3. Chunk Punctuation Focuses"
        constraints = [
            models.UniqueConstraint(fields=["chunk", "mark"], name="unique_punc_mark_per_chunk")
        ]

    def __str__(self):
        return f"Chunk {self.chunk.id} - {self.focus_title}"


class ChunkPunctuationFocusRule(models.Model):
    """Links specific global rules to a lesson focus."""
    focus = models.ForeignKey(ChunkPunctuationFocus, on_delete=models.CASCADE, related_name="focus_rules")
    rule = models.ForeignKey(PunctuationRule, on_delete=models.PROTECT) # Prevents curriculum deletion errors
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        verbose_name = "4. Focus-Rule Mapping"
        constraints = [
            models.UniqueConstraint(fields=["focus", "rule"], name="unique_rule_per_focus_mapping")
        ]


# ============================================================
# PRACTICE & ANALYTICS
# ============================================================

class PunctuationQuestion(models.Model):
    """Questions for practice/tests."""
    TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'), 
        ('insert', 'Insert Mark'), 
        ('fix', 'Correct Sentence')
    ]

    focus = models.ForeignKey(ChunkPunctuationFocus, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    
    # Staff-friendly pipe separator '|'
    options = models.TextField(
        blank=True, 
        help_text="For MCQ: Separate options with '|'. Example: Option A | Option B"
    )
    
    correct_answer = models.CharField(max_length=255)
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='mcq')
    explanation = models.TextField(blank=True, help_text="Shown to help the student learn from mistakes.")

    class Meta:
        verbose_name = "5. Punctuation Question"

    def __str__(self):
        return f"{self.question_type.upper()} - {self.question_text[:40]}"

    @property
    def options_list(self):
        if self.options:
        # This looks for the '|' and splits the text into a list
            return [opt.strip() for opt in self.options.split('|') if opt.strip()]
        return []


class PunctuationTestAttempt(models.Model):
    """
    Stores EVERY mastery test submission.
    True LMS design: one row per attempt.
    """

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    focus = models.ForeignKey(ChunkPunctuationFocus, on_delete=models.CASCADE)

    score_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    is_mastered = models.BooleanField(
        default=False,
        help_text="Automatically True when score_percent == 100."
    )

    total_questions = models.PositiveSmallIntegerField()
    correct_answers = models.PositiveSmallIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Punctuation Test Attempt"
        verbose_name_plural = "Punctuation Test Attempts"
        indexes = [
            models.Index(fields=["student", "focus"]),
            models.Index(fields=["student", "focus", "is_mastered"]),
        ]

    def save(self, *args, **kwargs):
        """
        Auto-calculate mastery.
        """
        self.is_mastered = (self.score_percent == 100)
        super().save(*args, **kwargs)
