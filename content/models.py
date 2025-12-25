from django.db import models

# -------------------------------
# 1. TEXTBOOK
# -------------------------------
class Textbook(models.Model):
    title = models.CharField(max_length=200)
    class_level = models.CharField(max_length=50, help_text="e.g., 9th, 10th, Inter, BA")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


# -------------------------------
# 2. UNIT
# -------------------------------
class Unit(models.Model):
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE, related_name="units")
    title = models.CharField(max_length=200)
    number = models.PositiveIntegerField()

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"{self.textbook.title} – Unit {self.number}: {self.title}"


# -------------------------------
# 3. LESSON
# -------------------------------
class Lesson(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    number = models.PositiveIntegerField()
    # Optional full text (chunks are preferred for delivery)
    english_text = models.TextField(blank=True, help_text="Optional: full English lesson text")
    translated_text = models.TextField(blank=True, help_text="Optional: full Urdu/Punjabi/Pashto translation")
    audio_file = models.FileField(upload_to="lesson_audio/", blank=True, null=True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"{self.unit} – Lesson {self.number}"



# -------------------------------
# 4. LESSON CHUNKS (preferred delivery)
# -------------------------------
class LessonChunk(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="chunks")
    order = models.PositiveIntegerField(help_text="Display order within the lesson")

    # Texts
    english_text = models.TextField()
    translated_text = models.TextField(blank=True, help_text="Urdu translation of the chunk")

    # Audio files
    audio_file = models.FileField(upload_to="chunk_audio/", blank=True, null=True, help_text="English audio")
    translated_audio_file = models.FileField(upload_to="chunk_audio_urdu/", blank=True, null=True, help_text="Urdu audio")  # ✅ new field

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.lesson} – Chunk {self.order}"



# -------------------------------
# 5. VOCABULARY ITEMS
# -------------------------------
class VocabularyItem(models.Model):
    lesson = models.ForeignKey("Lesson", on_delete=models.CASCADE, related_name="vocab_items")
    word = models.CharField(max_length=100)
    urdu = models.CharField(max_length=100, blank=True, null=True)
    meaning = models.TextField(blank=True, null=True)
    synonyms = models.TextField(blank=True, null=True)
    antonyms = models.TextField(blank=True, null=True)
    example_sentence = models.TextField(blank=True, null=True)

    # ✅ New field
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

    def __str__(self):
        return f"{self.word} ({self.part_of_speech})"


class VocabularyAttempt(models.Model):
    student_id = models.CharField(max_length=50)
    vocab_item = models.ForeignKey(VocabularyItem, on_delete=models.CASCADE, related_name="attempts")
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_id} - {self.vocab_item.word}"


# -------------------------------
# 6. WRITING TASKS + ATTEMPTS
# -------------------------------
class WritingTask(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="writing_tasks")
    prompt = models.TextField(help_text="Example: 'Write 5 sentences using the word honesty.'")
    difficulty = models.CharField(max_length=20, choices=[
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ])

    def __str__(self):
        return self.prompt[:40]


class SentenceAttempt(models.Model):
    writing_task = models.ForeignKey(WritingTask, on_delete=models.CASCADE, related_name="attempts")
    student_id = models.CharField(max_length=50)
    sentence = models.TextField()
    ai_score = models.IntegerField()
    feedback = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attempt by {self.student_id}"


# -------------------------------
# 7. GRAMMAR POINTS + ATTEMPTS
# -------------------------------
class GrammarPoint(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="grammar_points")
    title = models.CharField(max_length=200, help_text="e.g., 'Present Perfect Tense'")
    explanation = models.TextField(help_text="Explain the grammar rule here.")
    examples = models.TextField(help_text="Add example sentences here.")

    def __str__(self):
        return self.title


class GrammarAttempt(models.Model):
    student_id = models.CharField(max_length=50)
    grammar_point = models.ForeignKey(GrammarPoint, on_delete=models.CASCADE, related_name="attempts")
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_id} - {self.grammar_point.title}"


# -------------------------------
# 8. COMPREHENSION QUESTIONS + ATTEMPTS
# -------------------------------
class ComprehensionQuestion(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="comprehension_questions")
    question = models.TextField(help_text="Enter the comprehension question here.")
    answer = models.TextField(help_text="Enter the correct answer here.")

    def __str__(self):
        return self.question[:50]


class ComprehensionAttempt(models.Model):
    student_id = models.CharField(max_length=50)
    question = models.ForeignKey(ComprehensionQuestion, on_delete=models.CASCADE, related_name="attempts")
    answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_id} - {self.question.question[:30]}..."


# -------------------------------
# 9. PRONUNCIATION ATTEMPTS (NEW)
# -------------------------------
class PronunciationAttempt(models.Model):
    student_id = models.CharField(max_length=50)
    chunk = models.ForeignKey(LessonChunk, on_delete=models.CASCADE, related_name="pronunciation_attempts")
    recording = models.FileField(upload_to="student_audio/", blank=True, null=True)
    ai_feedback = models.TextField(blank=True, help_text="Feedback on pronunciation/intonation")
    ai_score = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_id} – Pronunciation of {self.chunk}"