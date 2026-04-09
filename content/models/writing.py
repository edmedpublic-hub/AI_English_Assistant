# content/models/writing.py
#
# Complete replacement of the previous writing models.
# Architecture: Three-tier writing module — Sentence → Paragraph → Genre
# Each tier has Teach → Practice → Test phases.
# 16 stages across the three tiers, each with Dissect / Imitate / Produce phases.
# Class level derived from unit.textbook.class_level — no user profile needed.
# Academic year scoped via WritingAcademicYear system settings model.

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .core import Unit


# ============================================================
# TIER CONSTANTS
# ============================================================

TIER_SENTENCE  = 'sentence'
TIER_PARAGRAPH = 'paragraph'
TIER_GENRE     = 'genre'

TIER_CHOICES = [
    (TIER_SENTENCE,  'Sentence'),
    (TIER_PARAGRAPH, 'Paragraph'),
    (TIER_GENRE,     'Genre'),
]

# ============================================================
# EVALUATION METHOD CONSTANTS
# ============================================================

EVAL_AUTOMATIC  = 'automatic'
EVAL_KEYWORD    = 'keyword'
EVAL_TEACHER    = 'teacher'
EVAL_AI_TEACHER = 'ai_teacher'

EVAL_CHOICES = [
    (EVAL_AUTOMATIC,  'Automatic'),
    (EVAL_KEYWORD,    'Keyword'),
    (EVAL_TEACHER,    'Teacher'),
    (EVAL_AI_TEACHER, 'AI + Teacher'),
]

# ============================================================
# PHASE CONSTANTS
# ============================================================

PHASE_DISSECT = 'dissect'
PHASE_IMITATE = 'imitate'
PHASE_PRODUCE = 'produce'

PHASE_CHOICES = [
    (PHASE_DISSECT, 'Dissect'),
    (PHASE_IMITATE, 'Imitate'),
    (PHASE_PRODUCE, 'Produce'),
]

# ============================================================
# SUBMISSION STATUS CONSTANTS
# ============================================================

STATUS_PENDING   = 'pending'
STATUS_PASSED    = 'passed'
STATUS_FAILED    = 'failed'
STATUS_COOLDOWN  = 'cooldown'
STATUS_APPROVED  = 'approved'
STATUS_REVISION  = 'needs_revision'

STATUS_CHOICES = [
    (STATUS_PENDING,  'Pending Review'),
    (STATUS_PASSED,   'Passed'),
    (STATUS_FAILED,   'Failed'),
    (STATUS_COOLDOWN, 'In Cooldown'),
    (STATUS_APPROVED, 'Approved by Teacher'),
    (STATUS_REVISION, 'Needs Revision'),
]


# ============================================================
# 1. ACADEMIC YEAR  — system-wide setting, admin sets once
# ============================================================

class WritingAcademicYear(models.Model):
    """
    Stores the current academic year start date.
    Admin sets this once per year.
    All writing mastery records are scoped to academic_year.
    Only one record should be marked is_current=True at a time.
    """
    label      = models.CharField(
        max_length=20,
        help_text="Example: 2025-2026"
    )
    start_date = models.DateField(
        help_text="Academic year start date. "
                  "Class advancement happens automatically after this date."
    )
    is_current = models.BooleanField(
        default=False,
        help_text="Mark exactly one academic year as current."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "Academic Year"
        verbose_name_plural = "Academic Years"

    def save(self, *args, **kwargs):
        # Enforce only one current academic year at a time
        if self.is_current:
            WritingAcademicYear.objects.exclude(pk=self.pk).update(
                is_current=False
            )
        super().save(*args, **kwargs)

    @classmethod
    def get_current(cls):
        """Return the current academic year or None."""
        return cls.objects.filter(is_current=True).first()

    def __str__(self):
        return f"{self.label} {'(current)' if self.is_current else ''}"


# ============================================================
# 2. WRITING STAGE  — the 16 stages, seeded once
# ============================================================

class WritingStage(models.Model):
    """
    The 16 writing stages. Seeded via data migration — not entered by admin.
    Stages are global — they apply across all class levels and units.
    Content per stage per unit is stored in WritingStageContent.

    Tier 1 — Sentence  (stages 1–5)
    Tier 2 — Paragraph (stages 6–13)
    Tier 3 — Genre     (stages 14–16)
    """
    number      = models.PositiveSmallIntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(16)],
        help_text="Stage number 1–16."
    )
    name        = models.CharField(max_length=100)
    tier        = models.CharField(max_length=20, choices=TIER_CHOICES)
    eval_method = models.CharField(
        max_length=20,
        choices=EVAL_CHOICES,
        help_text="How student work is evaluated at this stage."
    )
    description = models.TextField(
        blank=True,
        help_text="Plain English description shown to the student."
    )

    # Minimum word counts per class level
    # These are defaults — WritingStageContent can override per unit
    min_words_class_9  = models.PositiveSmallIntegerField(default=5)
    min_words_class_10 = models.PositiveSmallIntegerField(default=6)
    min_words_class_11 = models.PositiveSmallIntegerField(default=7)
    min_words_class_12 = models.PositiveSmallIntegerField(default=8)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]
        verbose_name = "Writing Stage"
        verbose_name_plural = "Writing Stages"

    def get_min_words_for_class(self, class_level: str) -> int:
        """
        Return minimum word count for a given class level string.
        class_level matches Textbook.class_level values.
        """
        mapping = {
            '9th':  self.min_words_class_9,
            '10th': self.min_words_class_10,
            'Inter': self.min_words_class_11,
            'inter': self.min_words_class_11,
            '11th': self.min_words_class_11,
            '12th': self.min_words_class_12,
            'BA':   self.min_words_class_12,
        }
        return mapping.get(class_level, self.min_words_class_11)

    def unlocks_after(self):
        """Return the stage that must be mastered before this one."""
        if self.number == 1:
            return None
        try:
            return WritingStage.objects.get(number=self.number - 1)
        except WritingStage.DoesNotExist:
            return None

    def __str__(self):
        return f"Stage {self.number}: {self.name} ({self.get_tier_display()})"


# ============================================================
# 3. WRITING STAGE CONTENT  — admin enters per stage per unit
# ============================================================

class WritingStageContent(models.Model):
    """
    The content admin prepares for each stage within each unit.
    This is what the student sees when they work through a stage.

    One record = one stage + one unit combination.
    The class level is derived from unit.textbook.class_level.

    Admin enters:
    - Model sentence (original from textbook)
    - Converted/simplified version
    - Conversion note explaining what changed and why
    - Imitate frame (sentence/paragraph frame for Imitate phase)
    - Produce prompt (the writing task for Produce phase)
    - Required keywords (for keyword-evaluated stages)
    - Word count override (optional — overrides WritingStage default)
    """
    stage = models.ForeignKey(
        WritingStage,
        on_delete=models.CASCADE,
        related_name="stage_contents"
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="writing_stage_contents"
    )

    # ── Dissect phase content ─────────────────────────────
    model_sentence_original = models.TextField(
        help_text="Original sentence or passage taken directly from the unit text."
    )
    model_sentence_converted = models.TextField(
        help_text="Simplified or converted version for comparison. "
                  "Example: complex sentence broken into simple sentences."
    )
    conversion_note = models.TextField(
        help_text="Plain English explanation of what changed and why. "
                  "Example: 'The relative clause was removed and the subject repeated.'"
    )

    # Dissect question — what the student identifies
    dissect_question = models.TextField(
        help_text="The identification question shown to the student. "
                  "Example: 'Which part is the subject? Which part is the verb?'"
    )
    dissect_answer = models.TextField(
        help_text="The correct answer used for automatic checking of Dissect phase."
    )

    # ── Imitate phase content ─────────────────────────────
    imitate_frame = models.TextField(
        help_text="The sentence or paragraph frame for the Imitate phase. "
                  "Use ___ for blanks. "
                  "Example: ___ [subject] ___ [verb] ___ [object]."
    )
    imitate_instruction = models.TextField(
        help_text="Clear instruction for what the student should do with this frame.",
        default="Fill in the frame using your own words to make a correct sentence."
    )

    # ── Produce phase content ─────────────────────────────
    produce_prompt = models.TextField(
        help_text="The writing task for the Produce phase. "
                  "No frame is given. Student writes independently. "
                  "Should relate to unit content."
    )
    produce_instruction = models.TextField(
        help_text="Clear instruction for the Produce phase.",
        default="Write on your own. No frame is given. "
                "Use what you have learned in this unit."
    )

    # ── Evaluation content ────────────────────────────────
    required_keywords = models.TextField(
        blank=True,
        help_text="Comma-separated keywords the student must use. "
                  "Used for keyword-evaluated stages only."
    )
    min_word_count = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Override the stage default minimum word count for this unit. "
                  "Leave blank to use the stage default."
    )

    # ── AI evaluation prompt ──────────────────────────────
    ai_rubric = models.JSONField(
        default=dict,
        blank=True,
        help_text="Rubric for AI evaluation. "
                  "Format: {'criterion': {'max_score': 5, 'description': '...'}}. "
                  "Used for AI+Teacher evaluated stages only."
    )

    # ── Status ────────────────────────────────────────────
    is_complete = models.BooleanField(
        default=False,
        help_text="Mark as complete when all content fields are filled "
                  "and ready for students."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering  = ["unit", "stage__number"]
        constraints = [
            models.UniqueConstraint(
                fields=["stage", "unit"],
                name="unique_writing_content_per_stage_per_unit"
            )
        ]
        indexes = [
            models.Index(fields=["stage", "unit"]),
            models.Index(fields=["is_complete"]),
        ]

    def get_min_words(self) -> int:
        """
        Return effective minimum word count.
        Unit-level override takes priority over stage default.
        """
        if self.min_word_count:
            return self.min_word_count
        class_level = self.unit.textbook.class_level
        return self.stage.get_min_words_for_class(class_level)

    def get_required_keywords_list(self) -> list:
        """Return required keywords as a clean list."""
        if not self.required_keywords:
            return []
        return [
            kw.strip()
            for kw in self.required_keywords.split(',')
            if kw.strip()
        ]

    def __str__(self):
        return (
            f"Stage {self.stage.number} · "
            f"{self.unit.textbook.class_level} · "
            f"Unit {self.unit.number}: {self.stage.name}"
        )


# ============================================================
# 4. WRITING ATTEMPT  — every student submission
# ============================================================

class WritingAttempt(models.Model):
    """
    Records every student submission across all phases and stages.

    Phase logic:
    - Student may attempt Produce directly (confident path)
    - If Produce fails → system routes to Dissect → Imitate → Produce
    - Cooldown of 24 hours enforced between failed Produce attempts

    Evaluation routing:
    - Automatic:  evaluated immediately by the system
    - Keyword:    evaluated immediately — checks structure + keywords
    - Teacher:    status stays PENDING until teacher reviews in admin
    - AI+Teacher: AI evaluates first → teacher can approve or override

    Academic year scoping:
    - academic_year links to WritingAcademicYear
    - Mastery from one academic year does NOT carry to the next
    """
    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="writing_attempts"
    )
    content = models.ForeignKey(
        WritingStageContent,
        on_delete=models.CASCADE,
        related_name="attempts"
    )
    academic_year = models.ForeignKey(
        WritingAcademicYear,
        on_delete=models.PROTECT,
        related_name="attempts",
        help_text="Academic year this attempt belongs to."
    )

    phase           = models.CharField(
        max_length=10,
        choices=PHASE_CHOICES,
        help_text="Which phase the student is submitting."
    )
    attempt_number  = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Attempt number within this phase for this academic year. "
                  "No hard cap — but cooldown enforced between Produce failures."
    )

    # ── Student's work ────────────────────────────────────
    response_text   = models.TextField(
        help_text="The student's written response."
    )

    # ── Evaluation results ────────────────────────────────
    status          = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text="Current status of this attempt."
    )

    # Automatic/keyword evaluation results
    auto_checks     = models.JSONField(
        default=dict,
        blank=True,
        help_text="Results of automatic checks. "
                  "Format: {'capital_start': True, 'full_stop_end': True, "
                  "'min_word_count': True, 'verb_present': True, "
                  "'keywords_found': ['word1', 'word2'], "
                  "'keywords_missing': ['word3']}"
    )

    # Sentence-level intervention flags (paragraph stages onward)
    intervention_flags = models.JSONField(
        default=list,
        blank=True,
        help_text="Sentence-level issues detected. "
                  "Format: [{'sentence': '...', 'issue': '...', "
                  "'fix_exercise': '...'}]"
    )

    # Scores
    auto_score      = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score from automatic/keyword evaluation (0–100)."
    )
    ai_score        = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score from AI evaluation (0–100)."
    )
    ai_feedback     = models.TextField(
        blank=True,
        help_text="AI-generated feedback shown to the student."
    )
    ai_rubric_scores = models.JSONField(
        default=dict,
        blank=True,
        help_text="AI scores per rubric criterion."
    )

    # Teacher evaluation
    teacher_score    = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score assigned by teacher (overrides AI score if set)."
    )
    teacher_feedback = models.TextField(
        blank=True,
        help_text="Teacher's written feedback shown to the student."
    )
    reviewed_by      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="writing_reviews",
        help_text="Teacher who reviewed this attempt."
    )
    reviewed_at      = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the teacher reviewed this attempt."
    )

    # Cooldown tracking
    cooldown_task    = models.TextField(
        blank=True,
        help_text="Directed focus task shown to student during cooldown. "
                  "Generated on fail and shown immediately on the fail screen."
    )
    next_attempt_allowed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student may attempt Produce again after a failure. "
                  "Set to 24 hours after a failed Produce attempt."
    )

    # Metadata
    time_spent_seconds = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "content", "academic_year"]),
            models.Index(fields=["user", "phase"]),
            models.Index(fields=["status"]),
            models.Index(fields=["reviewed_at"]),
            models.Index(fields=["next_attempt_allowed_at"]),
        ]

    # ── Cooldown helpers ──────────────────────────────────

    def set_cooldown(self, hours: int = 24):
        """Set the cooldown period after a failed Produce attempt."""
        self.next_attempt_allowed_at = timezone.now() + timedelta(hours=hours)
        self.status = STATUS_COOLDOWN

    def is_in_cooldown(self) -> bool:
        """Return True if the student must wait before attempting again."""
        if not self.next_attempt_allowed_at:
            return False
        return timezone.now() < self.next_attempt_allowed_at

    def cooldown_remaining(self):
        """Return remaining cooldown as a timedelta, or None if not in cooldown."""
        if not self.is_in_cooldown():
            return None
        return self.next_attempt_allowed_at - timezone.now()

    # ── Score helpers ─────────────────────────────────────

    def effective_score(self) -> int:
        """
        Return the score that counts for mastery determination.
        Teacher score overrides AI score overrides auto score.
        """
        if self.teacher_score is not None:
            return self.teacher_score
        if self.ai_score is not None:
            return self.ai_score
        if self.auto_score is not None:
            return self.auto_score
        return 0

    def is_passed(self) -> bool:
        """Return True if this attempt constitutes a pass."""
        return self.status in (STATUS_PASSED, STATUS_APPROVED)

    def __str__(self):
        return (
            f"{self.user.username} · "
            f"{self.content.stage.name} · "
            f"{self.get_phase_display()} · "
            f"Attempt {self.attempt_number} · "
            f"{self.get_status_display()}"
        )


# ============================================================
# 5. WRITING STAGE MASTERY  — per student per stage per year
# ============================================================

class WritingStageMastery(models.Model):
    """
    Records whether a student has mastered a stage in a given academic year.
    Scoped to: user + content (stage+unit) + academic_year.

    This is the gate model — mastery here unlocks the next stage.

    For automatic/keyword stages: set when auto evaluation passes.
    For teacher stages: set when teacher marks as Approved.
    For AI+Teacher stages: set when teacher Approves (AI verdict alone is not enough).
    """
    user          = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="writing_masteries"
    )
    content       = models.ForeignKey(
        WritingStageContent,
        on_delete=models.CASCADE,
        related_name="masteries"
    )
    academic_year = models.ForeignKey(
        WritingAcademicYear,
        on_delete=models.PROTECT,
        related_name="masteries"
    )

    mastered_at   = models.DateTimeField(
        help_text="When mastery was first achieved."
    )
    mastered_via  = models.CharField(
        max_length=20,
        choices=EVAL_CHOICES,
        help_text="Which evaluation method granted mastery."
    )

    # The specific attempt that earned mastery
    mastery_attempt = models.ForeignKey(
        WritingAttempt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mastery_grants",
        help_text="The attempt that earned this mastery."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["mastered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "content", "academic_year"],
                name="unique_mastery_per_student_stage_year"
            )
        ]
        indexes = [
            models.Index(fields=["user", "academic_year"]),
            models.Index(fields=["content", "academic_year"]),
        ]

    def __str__(self):
        return (
            f"{self.user.username} · "
            f"Stage {self.content.stage.number} mastered · "
            f"{self.academic_year.label}"
        )


# ============================================================
# 6. WRITING INTERVENTION  — point-of-need sentence flags
# ============================================================

class WritingIntervention(models.Model):
    """
    Stores a single sentence-level intervention generated during evaluation.
    Created when a paragraph or higher-level submission contains
    a sentence with a detectable structural problem.

    The student sees:
    1. The problematic sentence highlighted
    2. The exact issue named in plain English
    3. A single targeted fix exercise on that sentence
    4. Only after attempting the fix can they resubmit

    One WritingAttempt may generate multiple WritingIntervention records
    (one per problematic sentence).
    """
    attempt       = models.ForeignKey(
        WritingAttempt,
        on_delete=models.CASCADE,
        related_name="interventions"
    )

    sentence_text = models.TextField(
        help_text="The exact sentence that triggered this intervention."
    )
    issue_label   = models.CharField(
        max_length=200,
        help_text="Plain English description of the problem. "
                  "Example: 'This sentence has no verb.'"
    )
    fix_exercise  = models.TextField(
        help_text="The single targeted exercise shown to the student. "
                  "Example: 'Rewrite this sentence with a verb: The old man slowly.'"
    )
    student_fix   = models.TextField(
        blank=True,
        help_text="The student's response to the fix exercise."
    )
    is_resolved   = models.BooleanField(
        default=False,
        help_text="True when the student has attempted the fix exercise. "
                  "Does not need to be perfect — attempting is enough to proceed."
    )

    created_at    = models.DateTimeField(auto_now_add=True)
    resolved_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["attempt", "id"]
        indexes = [
            models.Index(fields=["attempt"]),
            models.Index(fields=["is_resolved"]),
        ]

    def resolve(self, student_fix_text: str):
        """Mark this intervention as resolved with the student's fix attempt."""
        self.student_fix = student_fix_text
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()

    def __str__(self):
        return (
            f"Intervention · "
            f"{self.attempt.user.username} · "
            f"Attempt {self.attempt.id} · "
            f"'{self.sentence_text[:40]}'"
        )


# ============================================================
# PATCH NOTES FOR core.py
# ============================================================
#
# After applying this file, update these two methods in
# content/models/core.py → LessonChunk:
#
# 1. _writing_mastered(self, user):
#    Replace entirely with:
#
#    def _writing_mastered(self, user):
#        from .writing import WritingStageMastery, WritingAcademicYear
#        year = WritingAcademicYear.get_current()
#        if not year:
#            return False
#        contents = WritingStageContent.objects.filter(unit=self.lesson.unit)
#        if not contents.exists():
#            return True
#        for content in contents:
#            mastered = WritingStageMastery.objects.filter(
#                user=user,
#                content=content,
#                academic_year=year
#            ).exists()
#            if not mastered:
#                return False
#        return True
#
# 2. _writing_details(self, user):
#    Replace entirely with:
#
#    def _writing_details(self, user):
#        from .writing import (
#            WritingStageMastery, WritingAcademicYear,
#            WritingStageContent, WritingAttempt
#        )
#        year = WritingAcademicYear.get_current()
#        contents = WritingStageContent.objects.filter(
#            unit=self.lesson.unit
#        ).select_related('stage')
#        details = []
#        for content in contents:
#            latest = WritingAttempt.objects.filter(
#                user=user,
#                content=content
#            ).order_by('-created_at').first()
#            mastered = WritingStageMastery.objects.filter(
#                user=user,
#                content=content,
#                academic_year=year
#            ).exists() if year else False
#            details.append({
#                'stage': content.stage.name,
#                'stage_number': content.stage.number,
#                'mastered': mastered,
#                'latest_score': latest.effective_score() if latest else 0,
#                'latest_phase': latest.phase if latest else None,
#                'latest_status': latest.status if latest else None,
#            })
#        return details
#
# ============================================================