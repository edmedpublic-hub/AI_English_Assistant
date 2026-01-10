from django.db import models


# ============================================================
# 1. TEXTBOOK
# ============================================================
class Textbook(models.Model):
    title = models.CharField(max_length=200)
    class_level = models.CharField(max_length=50, help_text="Example: 9th, 10th, Inter, BA")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} ({self.class_level})"


# ============================================================
# 2. UNIT
# ============================================================
class Unit(models.Model):
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE, related_name="units")
    title = models.CharField(max_length=200)
    number = models.PositiveIntegerField()

    class Meta:
        ordering = ["number"]
        indexes = [
            models.Index(fields=["textbook", "number"]),
        ]

    def __str__(self):
        return f"{self.textbook.title} • Unit {self.number}: {self.title}"


# ============================================================
# 3. LESSON
# ============================================================
class Lesson(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    number = models.PositiveIntegerField()

    english_text = models.TextField(blank=True)
    translated_text = models.TextField(blank=True)

    audio_file = models.FileField(upload_to="lesson_audio/", blank=True, null=True)

    class Meta:
        ordering = ["number"]
        indexes = [
            models.Index(fields=["unit", "number"]),
        ]

    def __str__(self):
        return f"{self.unit} • Lesson {self.number}: {self.title}"


# ============================================================
# 4. LESSON CHUNKS
# ============================================================
class LessonChunk(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="chunks")
    order = models.PositiveIntegerField(help_text="Display order within the lesson")

    english_text = models.TextField()
    translated_text = models.TextField(blank=True)

    audio_file = models.FileField(upload_to="chunk_audio/", blank=True, null=True)
    translated_audio_file = models.FileField(upload_to="chunk_audio_urdu/", blank=True, null=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["lesson", "order"], name="unique_chunk_order_per_lesson"),
        ]

    def __str__(self):
        return f"{self.lesson} • Chunk {self.order}"


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


# ============================================================
# 6. WRITING
# ============================================================
class WritingTask(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="writing_tasks")
    prompt = models.TextField()
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ("easy", "Easy"),
            ("medium", "Medium"),
            ("hard", "Hard"),
        ]
    )

    def __str__(self):
        return self.prompt[:60]


class SentenceAttempt(models.Model):
    writing_task = models.ForeignKey(WritingTask, on_delete=models.CASCADE, related_name="attempts")
    student_id = models.CharField(max_length=50, db_index=True)
    sentence = models.TextField()

    ai_score = models.IntegerField()
    feedback = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.student_id} — Writing Attempt"


# ============================================================
# 7. GRAMMAR
# ============================================================
class GrammarPoint(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="grammar_points")
    title = models.CharField(max_length=200)
    explanation = models.TextField()
    examples = models.TextField()

    def __str__(self):
        return self.title


class GrammarAttempt(models.Model):
    student_id = models.CharField(max_length=50, db_index=True)
    grammar_point = models.ForeignKey(GrammarPoint, on_delete=models.CASCADE, related_name="attempts")
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.student_id} — {self.grammar_point.title}"


# ============================================================
# 8. COMPREHENSION
# ============================================================
class ComprehensionQuestion(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="comprehension_questions")
    question = models.TextField()
    answer = models.TextField()

    def __str__(self):
        return self.question[:60]


class ComprehensionAttempt(models.Model):
    student_id = models.CharField(max_length=50, db_index=True)
    question = models.ForeignKey(ComprehensionQuestion, on_delete=models.CASCADE, related_name="attempts")
    answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.student_id} — {self.question.question[:30]}..."


# ============================================================
# 9. PRONUNCIATION
# ============================================================
class PronunciationAttempt(models.Model):
    student_id = models.CharField(max_length=50, db_index=True)
    chunk = models.ForeignKey(LessonChunk, on_delete=models.CASCADE, related_name="pronunciation_attempts")

    recording = models.FileField(upload_to="student_audio/", blank=True, null=True)
    ai_feedback = models.TextField(blank=True)
    ai_score = models.IntegerField(blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.student_id} — Pronunciation: {self.chunk}"
