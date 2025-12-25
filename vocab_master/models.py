from django.db import models
from django.core.exceptions import ValidationError

# -------------------------
# Hierarchy Models
# -------------------------

class Textbook(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Textbook"
        verbose_name_plural = "Textbooks"
        ordering = ["title"]
        indexes = [models.Index(fields=["title"])]

    def __str__(self):
        return self.title


class Unit(models.Model):
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE, related_name="units")
    title = models.CharField(max_length=200, db_index=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Unit"
        verbose_name_plural = "Units"
        ordering = ["textbook", "order"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["order"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["textbook", "title"], name="unique_unit_per_textbook")
        ]

    def clean(self):
        if Unit.objects.filter(textbook=self.textbook, title=self.title).exclude(pk=self.pk).exists():
            raise ValidationError("This textbook already has a unit with the same title.")

    def __str__(self):
        return f"{self.textbook.title} - {self.title}"


class Lesson(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200, db_index=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ["unit", "order"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["order"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["unit", "title"], name="unique_lesson_per_unit")
        ]

    def clean(self):
        if Lesson.objects.filter(unit=self.unit, title=self.title).exclude(pk=self.pk).exists():
            raise ValidationError("This unit already has a lesson with the same title.")

    def __str__(self):
        return f"{self.unit.title} - {self.title}"


# -------------------------
# Vocabulary + Related Models
# -------------------------

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


class Vocabulary(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="vocabulary")

    word = models.CharField(max_length=100, unique=True, db_index=True)
    part_of_speech = models.CharField(max_length=20, choices=PARTS_OF_SPEECH, db_index=True)
    definition = models.TextField()
    urdu_meaning = models.TextField()

    phonetic_spelling = models.CharField(max_length=100, blank=True, db_index=True)
    audio_pronunciation = models.FileField(upload_to="pronunciations/", blank=True, null=True)

    reviewed = models.BooleanField(default=False, db_index=True)

    # ✅ Time tracking fields
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vocabulary"
        verbose_name_plural = "Vocabulary"
        ordering = ["word"]
        indexes = [
            models.Index(fields=["word"]),
            models.Index(fields=["part_of_speech"]),
            models.Index(fields=["reviewed"]),
            models.Index(fields=["created_at"]),  # ✅ index for faster trend queries
        ]

    def __str__(self):
        return self.word


class Synonym(models.Model):
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name="synonyms")
    word = models.CharField(max_length=100, db_index=True)

    class Meta:
        verbose_name = "Synonym"
        verbose_name_plural = "Synonyms"
        ordering = ["word"]
        indexes = [models.Index(fields=["word"])]
        constraints = [
            models.UniqueConstraint(fields=["vocabulary", "word"], name="unique_synonym_per_vocab")
        ]

    def clean(self):
        if Synonym.objects.filter(vocabulary=self.vocabulary, word=self.word).exclude(pk=self.pk).exists():
            raise ValidationError("This synonym already exists for the selected vocabulary word.")

    def __str__(self):
        return self.word


class Antonym(models.Model):
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name="antonyms")
    word = models.CharField(max_length=100, db_index=True)

    class Meta:
        verbose_name = "Antonym"
        verbose_name_plural = "Antonyms"
        ordering = ["word"]
        indexes = [models.Index(fields=["word"])]
        constraints = [
            models.UniqueConstraint(fields=["vocabulary", "word"], name="unique_antonym_per_vocab")
        ]

    def clean(self):
        if Antonym.objects.filter(vocabulary=self.vocabulary, word=self.word).exclude(pk=self.pk).exists():
            raise ValidationError("This antonym already exists for the selected vocabulary word.")

    def __str__(self):
        return self.word


class ExampleSentence(models.Model):
    SENTENCE_TYPES = [
        ("simple", "Simple"),
        ("compound", "Compound"),
        ("complex", "Complex"),
    ]

    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name="examples")
    sentence = models.TextField(db_index=True)
    sentence_type = models.CharField(max_length=20, choices=SENTENCE_TYPES, db_index=True)

    class Meta:
        verbose_name = "Example sentence"
        verbose_name_plural = "Example sentences"
        ordering = ["sentence_type", "sentence"]
        indexes = [
            models.Index(fields=["sentence_type"]),
            models.Index(fields=["sentence"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["vocabulary", "sentence"], name="unique_example_per_vocab")
        ]

    def clean(self):
        if ExampleSentence.objects.filter(vocabulary=self.vocabulary, sentence=self.sentence).exclude(pk=self.pk).exists():
            raise ValidationError("This example sentence already exists for the selected vocabulary word.")

    def __str__(self):
        return f"{self.sentence_type}: {self.sentence[:50]}..."