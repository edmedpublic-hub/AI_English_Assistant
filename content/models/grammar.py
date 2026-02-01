# content/models/grammar.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError
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
    Example: 'Proper nouns begin with capital letters.'
    """
    concept = models.ForeignKey(
        GrammarConcept,
        on_delete=models.CASCADE,
        related_name="rules"
    )

    rule_text = models.TextField()

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

    def __str__(self):
        return self.sentence[:80]


# ============================================================
# TEACHING LAYER (Chunk-level Pedagogical Focus)
# ============================================================

class ChunkGrammarFocus(models.Model):
    """
    Represents how a grammar concept is taught in a specific chunk.
    Enables spiral learning and progressive depth.
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

    focus_title = models.CharField(
        max_length=200,
        help_text="e.g. 'Kinds of Nouns', 'Present Simple vs Present Continuous'"
    )

    focus_description = models.TextField()

    depth_level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 = Introductory, 5 = Expert-level treatment"
    )

    sequence_order = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="1–3 (maximum three grammar focuses per chunk)"
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
    Concrete grammar questions tied to a specific ChunkGrammarFocus.
    Designed for teacher-friendly content entry.
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
        "ChunkGrammarFocus",
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField()

    # ⬇️ CHANGED: JSONField → TextField (teacher-friendly)
    options = models.TextField(
        null=True,
        blank=True,
        help_text="For MCQs: enter one option per line"
    )

    correct_answer = models.CharField(
        max_length=255,
        help_text="Must exactly match one of the options (for MCQs)"
    )

    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPES,
        default=TYPE_MCQ
    )

    difficulty = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    explanation = models.TextField(
        blank=True,
        help_text="Explanation shown after answering (why this is correct)"
    )

    class Meta:
        ordering = ["focus_id", "id"]
        indexes = [
            models.Index(fields=["focus"]),
            models.Index(fields=["question_type"]),
            models.Index(fields=["difficulty"]),
        ]

    def clean(self):
        """
        Model-level validation to protect data integrity
        without burdening teachers.
        """
        if self.question_type == self.TYPE_MCQ:
            if not self.options:
                raise ValidationError("MCQ questions must have options.")

            option_list = [
                opt.strip()
                for opt in self.options.splitlines()
                if opt.strip()
            ]

            if len(option_list) < 2:
                raise ValidationError("MCQ questions must have at least two options.")

            if self.correct_answer not in option_list:
                raise ValidationError(
                    "Correct answer must exactly match one of the options."
                )

    def get_options_list(self):
        """
        Utility method for views/templates.
        """
        if not self.options:
            return []
        return [
            opt.strip()
            for opt in self.options.splitlines()
            if opt.strip()
        ]

    def __str__(self):
        return f"{self.focus.focus_title}: {self.question_text[:60]}"


# ============================================================
# ATTEMPTS & ANALYTICS
# ============================================================

class GrammarAttempt(models.Model):
    """
    Per-question logging for analytics and learner diagnostics.
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
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["question"]),
            models.Index(fields=["is_correct"]),
            models.Index(fields=["attempted_at"]),
        ]

    def __str__(self):
        return f"{self.student.username} — Q{self.question_id} ({'✓' if self.is_correct else '✗'})"


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

    questions_snapshot = models.JSONField(
        help_text="Snapshot of questions used in this test for review consistency"
    )

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
