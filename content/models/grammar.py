# content/models/grammar.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings

from .core import LessonChunk


# ============================================================
# KNOWLEDGE LAYER (Global Grammar Curriculum)
# ============================================================

class GrammarConcept(models.Model):
    """
    A global grammar concept independent of textbooks.
    Examples: Noun, Proper Noun, Present Simple, Relative Clause.
    """
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=100,
        help_text="e.g. Parts of Speech, Tense, Clause, Sentence Structure"
    )

    order_index = models.PositiveIntegerField(
        help_text="Controls global progression order across the curriculum"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order_index", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category"]),
            models.Index(fields=["order_index"]),
        ]

    def __str__(self):
        return self.name


class GrammarRule(models.Model):
    """
    A specific rule under a grammar concept.
    """
    concept = models.ForeignKey(
        GrammarConcept,
        on_delete=models.CASCADE,
        related_name="rules"
    )

    rule_text = models.TextField()
    order = models.PositiveSmallIntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["concept", "order"],
                name="unique_rule_order_per_concept"
            )
        ]
        indexes = [
            models.Index(fields=["concept"]),
        ]

    def __str__(self):
        return f"{self.concept.name}: {self.rule_text[:60]}"


class GrammarExample(models.Model):
    """
    Example sentence illustrating a grammar rule.
    """
    rule = models.ForeignKey(
        GrammarRule,
        on_delete=models.CASCADE,
        related_name="examples"
    )

    sentence = models.TextField()
    order = models.PositiveSmallIntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["rule", "order"],
                name="unique_example_order_per_rule"
            )
        ]
        indexes = [
            models.Index(fields=["rule"]),
        ]

    def __str__(self):
        return self.sentence[:80]


# ============================================================
# TEACHING LAYER (Chunk-level Pedagogical Focus)
# ============================================================

class ChunkGrammarFocus(models.Model):
    """
    Represents how a grammar concept is taught in a specific chunk.
    """

    chunk = models.ForeignKey(
        LessonChunk,
        on_delete=models.CASCADE,
        related_name="grammar_focuses"
    )

    concept = models.ForeignKey(
        GrammarConcept,
        on_delete=models.CASCADE,
        related_name="teaching_instances"
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
                name="unique_grammar_focus_order_per_chunk"
            )
        ]
        indexes = [
            models.Index(fields=["chunk"]),
            models.Index(fields=["concept"]),
            models.Index(fields=["depth_level"]),
        ]

    def __str__(self):
        return f"{self.chunk} → {self.focus_title}"


# ============================================================
# QUESTIONS
# ============================================================

class GrammarQuestion(models.Model):
    """
    Grammar questions tied to a specific ChunkGrammarFocus.
    """

    TYPE_MCQ = "mcq"
    TYPE_FILL = "fill"
    TYPE_REWRITE = "rewrite"
    TYPE_IDENTIFY = "identify"

    QUESTION_TYPES = [
        (TYPE_MCQ, "Multiple Choice"),
        (TYPE_FILL, "Fill in the Blank"),
        (TYPE_REWRITE, "Rewrite Sentence"),
        (TYPE_IDENTIFY, "Identify Part / Function"),
    ]
    
    DIFFICULTY_CHOICES = [(i, str(i)) for i in range(1, 6)]

    focus = models.ForeignKey(
        ChunkGrammarFocus,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField()
    options = models.TextField(
        blank=True, 
        null=True,
        help_text="For MCQ: One option per line"
    )
    correct_answer = models.CharField(max_length=255)

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
        else:
            if not self.correct_answer.strip():
                raise ValidationError(
                    "Non-MCQ questions must define a correct answer."
                )

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

class GrammarPracticeAttempt(models.Model):
    """
    Tracks practice attempts for grammar.
    3 attempts max per cycle, 100% required to pass.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grammar_practice_attempts"
    )

    focus = models.ForeignKey(
        ChunkGrammarFocus,
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
                name="unique_grammar_practice_per_cycle"
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
        return f"{self.user.username} — {self.focus} — Practice {self.attempt_number} ({self.score_percent}%)"


# ============================================================
# TEST LAYER (Summative Assessment)
# ============================================================

class GrammarTestAttempt(models.Model):
    """
    Aggregate assessment result for a test session.
    3 attempts max per cycle, 100% required to pass.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grammar_test_attempts"
    )

    focus = models.ForeignKey(
        ChunkGrammarFocus,
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

    correct_answers = models.PositiveSmallIntegerField()
    total_questions = models.PositiveSmallIntegerField()

    questions_snapshot = models.JSONField(
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
                name="unique_grammar_test_per_cycle"
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
        return f"{self.user.username} — {self.focus.focus_title} — Attempt {self.attempt_number} ({self.score_percent}%) {status}"


# ============================================================
# PER-QUESTION ATTEMPTS (Detailed Analytics)
# ============================================================

class GrammarQuestionAttempt(models.Model):
    """
    Per-question logging for analytics and diagnostics.
    Tracks individual question responses within practice/test sessions.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grammar_question_attempts"
    )

    question = models.ForeignKey(
        GrammarQuestion,
        on_delete=models.CASCADE,
        related_name="question_attempts"
    )
    
    # Link to practice or test attempt
    practice_attempt = models.ForeignKey(
        GrammarPracticeAttempt,
        on_delete=models.CASCADE,
        related_name="question_attempts",
        null=True,
        blank=True
    )
    
    test_attempt = models.ForeignKey(
        GrammarTestAttempt,
        on_delete=models.CASCADE,
        related_name="question_attempts",
        null=True,
        blank=True
    )

    selected_answer = models.CharField(max_length=255, blank=True)
    is_correct = models.BooleanField(default=False)
    
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Timestamps
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(fields=["user", "question"]),
            models.Index(fields=["user", "is_correct"]),
            models.Index(fields=["practice_attempt"]),
            models.Index(fields=["test_attempt"]),
            models.Index(fields=["attempted_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} — Q{self.question_id} — {'✓' if self.is_correct else '✗'}"