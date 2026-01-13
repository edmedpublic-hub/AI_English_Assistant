from django.db import models
from .core import Lesson, LessonChunk


# ============================================================
# 5. VOCABULARY
# ============================================================
class VocabularyItem(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="vocab_items")
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
    part_of_speech = models.CharField(max_length=20, choices=PARTS_OF_SPEECH, default="noun")

    class Meta:
        ordering = ["lesson_id", "word"]
        indexes = [
            models.Index(fields=["lesson", "word"]),
            models.Index(fields=["chunk", "word"]),
        ]

    def __str__(self):
        return f"{self.word} [{self.part_of_speech}]"


class VocabularyAttempt(models.Model):
    student_id = models.CharField(max_length=50, db_index=True)
    vocab_item = models.ForeignKey(VocabularyItem, on_delete=models.CASCADE, related_name="attempts")
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.student_id} — {self.vocab_item.word}"


# ============================================================
# 5b. VOCABULARY MASTERY
# ============================================================
class StudentVocabMastery(models.Model):
    student_id = models.CharField(max_length=50, db_index=True)
    vocab_item = models.ForeignKey(VocabularyItem, on_delete=models.CASCADE, related_name="mastery_records")

    MASTERY_LEVELS = [
        ("new", "New"),
        ("learning", "Learning"),
        ("review", "Needs Review"),
        ("mastered", "Mastered"),
    ]
    mastery_level = models.CharField(max_length=20, choices=MASTERY_LEVELS, default="new")

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student_id", "vocab_item"], name="unique_student_vocab_mastery"),
        ]

    def __str__(self):
        return f"{self.student_id} — {self.vocab_item.word} — {self.mastery_level}"
