# content/models/grammar.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

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

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["concept", "order"],
                name="unique_rule_order_per_concept"
            )
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

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["rule", "order"],
                name="unique_example_order_per_rule"
            )
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

    class Meta:
        ordering = ["chunk_id", "sequence_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["chunk", "sequence_order"],
                name="unique_focus_order_per_chunk"
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
# PRACTICE & TEST QUESTIONS
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

    focus = models.ForeignKey(
        ChunkGrammarFocus,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField()
    options = models.TextField(blank=True, null=True)
    correct_answer = models.CharField(max_length=255)

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
# ATTEMPTS & ANALYTICS
# ============================================================

class GrammarAttempt(models.Model):
    """
    Per-question logging for analytics and diagnostics.
    """

    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="grammar_attempts"
    )

    question = models.ForeignKey(
        GrammarQuestion,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    selected_answer = models.CharField(max_length=255, blank=True)
    is_correct = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "question"],
                name="unique_attempt_per_question"
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


class GrammarTestAttempt(models.Model):
    """
    Aggregate assessment result for a test session.
    """

    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="grammar_test_attempts"
    )

    focus = models.ForeignKey(
        ChunkGrammarFocus,
        on_delete=models.CASCADE,
        related_name="test_attempts"
    )

    score_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    correct_answers = models.PositiveSmallIntegerField()
    total_questions = models.PositiveSmallIntegerField()

    questions_snapshot = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["focus"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.student.username} — {self.focus.focus_title} ({self.score_percent}%)"


# ============================================================
# PRACTICE TRACKING
# ============================================================

class GrammarPracticeAttempt(models.Model):
    """
    Records whether a student has attempted practice for a grammar focus.
    """

    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="grammar_practice_attempts"
    )

    focus = models.ForeignKey(
        ChunkGrammarFocus,
        on_delete=models.CASCADE,
        related_name="practice_attempts"
    )

    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "focus")
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["focus"]),
            models.Index(fields=["attempted_at"]),
        ]

    def __str__(self):
        return f"{self.student.username} — Practice attempted ({self.focus.focus_title})"
