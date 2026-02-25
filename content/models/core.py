from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.functional import cached_property


# ============================================================
# 1. TEXTBOOK
# ============================================================
class Textbook(models.Model):
    title = models.CharField(max_length=200)
    class_level = models.CharField(max_length=50, help_text="Example: 9th, 10th, Inter, BA")
    description = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["class_level", "title"]
        indexes = [
            models.Index(fields=["class_level"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.class_level})"


# ============================================================
# 2. UNIT
# ============================================================
class Unit(models.Model):
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        related_name="units"
    )
    title = models.CharField(max_length=200)
    number = models.PositiveIntegerField()
    description = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["textbook", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["textbook", "number"],
                name="unique_unit_number_per_textbook"
            ),
        ]
        indexes = [
            models.Index(fields=["textbook", "number"]),
        ]

    @cached_property
    def total_chunks(self):
        """Get total number of chunks in this unit."""
        return LessonChunk.objects.filter(lesson__unit=self).count()

    def __str__(self):
        return f"{self.textbook.title} • Unit {self.number}: {self.title}"


# ============================================================
# 3. LESSON
# ============================================================
class Lesson(models.Model):
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="lessons"
    )
    title = models.CharField(max_length=200)
    number = models.PositiveIntegerField()

    english_text = models.TextField(blank=True)
    translated_text = models.TextField(blank=True)

    audio_file = models.FileField(
        upload_to="lesson_audio/",
        blank=True,
        null=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["unit", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["unit", "number"],
                name="unique_lesson_number_per_unit"
            ),
        ]
        indexes = [
            models.Index(fields=["unit", "number"]),
        ]

    @cached_property
    def total_chunks(self):
        """Get total number of chunks in this lesson."""
        return self.chunks.count()

    def __str__(self):
        return f"{self.unit} • Lesson {self.number}: {self.title}"


# ============================================================
# 4. LESSON CHUNKS (The Atomic Learning Unit)
# ============================================================
class LessonChunk(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="chunks"
    )
    order = models.PositiveIntegerField(
        help_text="Display order within the lesson"
    )

    english_text = models.TextField()
    translated_text = models.TextField(blank=True)

    audio_file = models.FileField(
        upload_to="chunk_audio/",
        blank=True,
        null=True
    )
    translated_audio_file = models.FileField(
        upload_to="chunk_audio_urdu/",
        blank=True,
        null=True
    )

    # Metadata
    estimated_time_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Estimated time to complete this chunk"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "order"],
                name="unique_chunk_order_per_lesson"
            ),
        ]
        indexes = [
            models.Index(fields=["lesson", "order"]),
        ]

    # -----------------------------------------------------------------
    # MASTERY METHODS (Integrated across all six domains)
    # -----------------------------------------------------------------

    def is_mastered_by(self, user):
        """
        Comprehensive mastery check across ALL domains:
        - Grammar: 100% on all GrammarTestAttempts
        - Punctuation: 100% on all PunctuationTestAttempts
        - Comprehension: 100% on all ComprehensionTestAttempts
        - Vocabulary: All items at "mastered" level
        - Writing: 100% on all WritingTestAttempts (chunk + unit level)
        - Pronunciation: Average AI score >= 90
        """
        if not user.is_authenticated:
            return False

        results = {
            'grammar': self._grammar_mastered(user),
            'punctuation': self._punctuation_mastered(user),
            'comprehension': self._comprehension_mastered(user),
            'vocabulary': self._vocabulary_mastered(user),
            'writing': self._writing_mastered(user),
            'pronunciation': self._pronunciation_mastered(user),
        }

        return all(results.values())

    def get_mastery_status(self, user):
        """
        Returns detailed mastery status for all domains.
        Used by dashboards and progress tracking.
        """
        if not user.is_authenticated:
            return None

        by_domain = {
            'grammar': {
                'mastered': self._grammar_mastered(user),
                'details': self._grammar_details(user),
            },
            'punctuation': {
                'mastered': self._punctuation_mastered(user),
                'details': self._punctuation_details(user),
            },
            'comprehension': {
                'mastered': self._comprehension_mastered(user),
                'details': self._comprehension_details(user),
            },
            'vocabulary': {
                'mastered': self._vocabulary_mastered(user),
                'details': self._vocabulary_details(user),
            },
            'writing': {
                'mastered': self._writing_mastered(user),
                'details': self._writing_details(user),
            },
            'pronunciation': {
                'mastered': self._pronunciation_mastered(user),
                'details': self._pronunciation_details(user),
            },
        }

        return {
            'overall': all(d['mastered'] for d in by_domain.values()),
            'by_domain': by_domain,
            'next_domain_to_work': self._next_priority_domain(by_domain),
        }

    # -----------------------------------------------------------------
    # Domain-specific mastery checks
    # -----------------------------------------------------------------

    def _grammar_mastered(self, user):
        """Check if all grammar focuses are mastered."""
        from .grammar import GrammarTestAttempt

        focuses = self.grammar_focuses.all()
        if not focuses.exists():
            return True

        for focus in focuses:
            mastered = GrammarTestAttempt.objects.filter(
                user=user,
                focus=focus,
                is_mastered=True
            ).exists()
            if not mastered:
                return False

        return True

    def _grammar_details(self, user):
        """Get detailed grammar progress."""
        from .grammar import GrammarTestAttempt

        focuses = self.grammar_focuses.all()
        details = []

        for focus in focuses:
            latest = GrammarTestAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-created_at').first()

            details.append({
                'focus': focus.focus_title,
                'mastered': latest.is_mastered if latest else False,
                'latest_score': latest.score_percent if latest else 0,
                'attempts_used': latest.attempt_number if latest else 0,
            })

        return details

    def _punctuation_mastered(self, user):
        """Check if all punctuation focuses are mastered."""
        from .punctuation import PunctuationTestAttempt

        focuses = self.punctuation_focuses.all()
        if not focuses.exists():
            return True

        for focus in focuses:
            mastered = PunctuationTestAttempt.objects.filter(
                user=user,
                focus=focus,
                is_mastered=True
            ).exists()
            if not mastered:
                return False

        return True

    def _punctuation_details(self, user):
        """Get detailed punctuation progress."""
        from .punctuation import PunctuationTestAttempt

        focuses = self.punctuation_focuses.all()
        details = []

        for focus in focuses:
            latest = PunctuationTestAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-created_at').first()

            details.append({
                'focus': focus.focus_title,
                'mastered': latest.is_mastered if latest else False,
                'latest_score': latest.score_percent if latest else 0,
                'attempts_used': latest.attempt_number if latest else 0,
            })

        return details

    def _comprehension_mastered(self, user):
        """Check if all comprehension focuses are mastered."""
        from .comprehension import ComprehensionTestAttempt

        focuses = self.comprehension_focuses.all()
        if not focuses.exists():
            return True

        for focus in focuses:
            mastered = ComprehensionTestAttempt.objects.filter(
                user=user,
                focus=focus,
                is_mastered=True
            ).exists()
            if not mastered:
                return False

        return True

    def _comprehension_details(self, user):
        """Get detailed comprehension progress."""
        from .comprehension import ComprehensionTestAttempt

        focuses = self.comprehension_focuses.all()
        details = []

        for focus in focuses:
            latest = ComprehensionTestAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-created_at').first()

            details.append({
                'focus': focus.focus_title,
                'level': focus.level,
                'mastered': latest.is_mastered if latest else False,
                'latest_score': latest.score_percent if latest else 0,
                'attempts_used': latest.attempt_number if latest else 0,
            })

        return details

    def _vocabulary_mastered(self, user):
        """Check if all vocabulary items are at 'mastered' level."""
        from .vocabulary import StudentVocabMastery

        vocab_items = self.vocab_items.all()
        if not vocab_items.exists():
            return True

        for item in vocab_items:
            try:
                mastery = StudentVocabMastery.objects.get(
                    user=user,
                    vocab_item=item
                )
                if mastery.mastery_level != 'mastered':
                    return False
            except StudentVocabMastery.DoesNotExist:
                return False

        return True

    def _vocabulary_details(self, user):
        """Get detailed vocabulary progress."""
        from .vocabulary import StudentVocabMastery, VocabularyAttempt

        vocab_items = self.vocab_items.all()
        details = []

        for item in vocab_items:
            try:
                mastery = StudentVocabMastery.objects.get(
                    user=user,
                    vocab_item=item
                )
                details.append({
                    'word': item.word,
                    'mastery_level': mastery.mastery_level,
                    'accuracy': mastery.accuracy_percentage,
                    'total_attempts': mastery.total_attempts,
                    'last_practiced': mastery.last_practiced,
                })
            except StudentVocabMastery.DoesNotExist:
                details.append({
                    'word': item.word,
                    'mastery_level': 'new',
                    'accuracy': 0,
                    'total_attempts': 0,
                    'last_practiced': None,
                })

        return details

    def _writing_mastered(self, user):
        """Check if all writing focuses (chunk and unit level) are mastered."""
        from .writing import WritingTestAttempt

        # Check chunk-level writing focuses
        focuses = self.writing_focuses.all()
        if focuses.exists():
            for focus in focuses:
                mastered = WritingTestAttempt.objects.filter(
                    user=user,
                    focus=focus,
                    is_mastered=True
                ).exists()
                if not mastered:
                    return False

        # Check unit-level writing tasks
        tasks = self.lesson.unit.writing_tasks.all()
        if tasks.exists():
            for task in tasks:
                mastered = WritingTestAttempt.objects.filter(
                    user=user,
                    task=task,
                    is_mastered=True
                ).exists()
                if not mastered:
                    return False

        return True

    def _writing_details(self, user):
        """Get detailed writing progress."""
        from .writing import WritingTestAttempt

        focuses = self.writing_focuses.all()
        details = []

        for focus in focuses:
            latest = WritingTestAttempt.objects.filter(
                user=user,
                focus=focus
            ).order_by('-created_at').first()

            details.append({
                'focus': focus.focus_title,
                'mastered': latest.is_mastered if latest else False,
                'latest_score': latest.overall_score if latest else 0,
                'attempts_used': latest.attempt_number if latest else 0,
            })

        return details

    def _pronunciation_mastered(self, user):
        """Check if pronunciation is mastered (score >= 90)."""
        from .pronunciation import PronunciationMastery

        focuses = self.pronunciation_focuses.all()
        if not focuses.exists():
            return True

        for focus in focuses:
            try:
                mastery = PronunciationMastery.objects.get(
                    user=user,
                    focus=focus
                )
                if not mastery.is_mastered:
                    return False
            except PronunciationMastery.DoesNotExist:
                return False

        return True

    def _pronunciation_details(self, user):
        """Get detailed pronunciation progress."""
        from .pronunciation import PronunciationMastery, PronunciationAttempt

        focuses = self.pronunciation_focuses.all()
        details = []

        for focus in focuses:
            try:
                mastery = PronunciationMastery.objects.get(
                    user=user,
                    focus=focus
                )
                details.append({
                    'focus': focus.focus_title,
                    'mastered': mastery.is_mastered,
                    'best_score': mastery.best_score,
                    'last_score': mastery.last_score,
                    'total_attempts': mastery.total_attempts,
                })
            except PronunciationMastery.DoesNotExist:
                details.append({
                    'focus': focus.focus_title,
                    'mastered': False,
                    'best_score': None,
                    'last_score': None,
                    'total_attempts': 0,
                })

        return details

    def _next_priority_domain(self, by_domain):
        """
        Determine which domain the user should work on next.
        Returns the domain with the lowest mastery score.
        """
        lowest_domain = None
        lowest_score = 101

        for domain, data in by_domain.items():
            if not data['mastered']:
                details = data['details']
                if not details:
                    avg_score = 0
                elif domain == 'vocabulary':
                    avg_score = sum(d['accuracy'] for d in details) / len(details)
                elif domain == 'pronunciation':
                    avg_score = sum(d['best_score'] or 0 for d in details) / len(details)
                else:
                    avg_score = sum(d['latest_score'] for d in details) / len(details)

                if avg_score < lowest_score:
                    lowest_score = avg_score
                    lowest_domain = domain

        return lowest_domain

    # -----------------------------------------------------------------
    # Utility Methods
    # -----------------------------------------------------------------

    def get_all_focuses(self):
        """Get all focuses across all domains for this chunk."""
        return {
            'grammar': self.grammar_focuses.all(),
            'punctuation': self.punctuation_focuses.all(),
            'comprehension': self.comprehension_focuses.all(),
            'vocabulary': self.vocab_items.all(),
            'writing': self.writing_focuses.all(),
            'pronunciation': self.pronunciation_focuses.all(),
        }

    def __str__(self):
        return f"{self.lesson} • Chunk {self.order}"