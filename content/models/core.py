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
    lesson = models.ForeignKey("Lesson", on_delete=models.CASCADE, related_name="chunks")
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

    # --- NEW MASTERY LOGIC (Safe from Circular Imports) ---
    def is_mastered_by(self, user):
        """
        Calculates if the student has achieved 100% on every 
        grammar focus associated with this chunk.
        """
        if not user.is_authenticated:
            return False
        
        # Move import inside the method to prevent Circular Import error
        from content.models.grammar import GrammarTestAttempt
            
        focuses = self.grammar_focuses.all()
        if not focuses.exists():
            return True  # Unlocked if no grammar is assigned

        # Count distinct focuses passed at 100%
        mastered_count = GrammarTestAttempt.objects.filter(
            student=user,
            focus__in=focuses,
            score_percent=100
        ).values('focus').distinct().count()

        return mastered_count == focuses.count()

    def __str__(self):
        return f"{self.lesson} • Chunk {self.order}"