from django.db import models
from django.conf import settings
from .core import Lesson, LessonChunk

# ============================================================
# 5. VOCABULARY
# ============================================================

class VocabularyItem(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="vocab_items"
    )
    chunk = models.ForeignKey(
        LessonChunk,
        on_delete=models.CASCADE,
        related_name="vocab_items",
        blank=True,
        null=True,
        help_text="Optional: link vocabulary to a specific chunk"
    )
    word = models.CharField(max_length=100)
    urdu = models.CharField(max_length=100, blank=True, null=True)
    meaning = models.TextField(blank=True, null=True)
    synonyms = models.TextField(blank=True, null=True)
    antonyms = models.TextField(blank=True, null=True)
    example_sentence = models.TextField(blank=True, null=True)

    PARTS_OF_SPEECH = [
        ("noun", "Noun"),
        ("verb", "Verb"),
        ("adjective", "Adjective"),
        ("adverb", "Adverb"),
        ("pronoun", "Pronoun"),
        ("preposition", "Preposition"),
        ("conjunction", "Conjunction"),
        ("interjection", "Interjection"),
    ]

    part_of_speech = models.CharField(
        max_length=20,
        choices=PARTS_OF_SPEECH,
        default="noun"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson_id", "word"]
        indexes = [
            models.Index(fields=["lesson", "word"]),
            models.Index(fields=["chunk", "word"]),
        ]

    def __str__(self):
        return f"{self.word} [{self.part_of_speech}]"


class VocabularyAttempt(models.Model):
    """Tracks individual vocabulary practice attempts."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vocabulary_attempts"
    )
    vocab_item = models.ForeignKey(
        VocabularyItem,
        on_delete=models.CASCADE,
        related_name="attempts"
    )
    
    # Context fields
    session_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Groups attempts from same practice session"
    )
    cycle_number = models.PositiveSmallIntegerField(
        default=1,
        help_text="Retry cycle (1, 2, 3, ...)"
    )
    
    # Attempt data
    is_correct = models.BooleanField(default=False)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "vocab_item"]),
            models.Index(fields=["user", "session_id"]),
            models.Index(fields=["user", "cycle_number"]),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.vocab_item.word} — {'✓' if self.is_correct else '✗'}"


class StudentVocabMastery(models.Model):
    """Tracks current mastery state for vocabulary items."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vocab_mastery_records"
    )
    vocab_item = models.ForeignKey(
        VocabularyItem,
        on_delete=models.CASCADE,
        related_name="mastery_records"
    )

    MASTERY_LEVELS = [
        ("new", "New"),
        ("learning", "Learning"),
        ("review", "Needs Review"),
        ("mastered", "Mastered"),
    ]

    mastery_level = models.CharField(
        max_length=20,
        choices=MASTERY_LEVELS,
        default="new"
    )
    
    # Track history
    last_practiced = models.DateTimeField(null=True, blank=True)
    total_attempts = models.PositiveIntegerField(default=0)
    correct_attempts = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "vocab_item"],
                name="unique_user_vocab_mastery"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "mastery_level"]),
        ]

    @property
    def accuracy_percentage(self):
        """Calculate accuracy rate."""
        if self.total_attempts == 0:
            return 0
        return (self.correct_attempts / self.total_attempts) * 100

    def __str__(self):
        return f"{self.user.username} — {self.vocab_item.word} — {self.mastery_level}"