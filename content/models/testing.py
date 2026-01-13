from django.db import models
from .core import LessonChunk
from .vocabulary import VocabularyItem
# ============================================================
# 10. VOCABULARY TESTING SYSTEM (ADDITIVE - SAFE)
# ============================================================

class VocabularyTestSession(models.Model):
    """
    Represents one full test attempt (e.g. 10 questions).
    """
    student_id = models.CharField(max_length=50, db_index=True)
    chunk = models.ForeignKey(LessonChunk, on_delete=models.CASCADE, related_name="vocab_test_sessions")

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    total_questions = models.PositiveIntegerField(default=10)
    correct_answers = models.PositiveIntegerField(default=0)

    score_percentage = models.FloatField(default=0.0)

    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student_id} — {self.chunk} — {self.score_percentage}%"


class VocabularyTestQuestion(models.Model):
    """
    Stores which vocabulary item appeared in a session and in what form.
    """
    QUESTION_TYPES = [
        ("meaning", "Meaning"),
        ("synonym", "Synonym"),
        ("antonym", "Antonym"),
        ("fill_blank", "Fill in the blank"),
    ]

    session = models.ForeignKey(VocabularyTestSession, on_delete=models.CASCADE, related_name="questions")
    vocab_item = models.ForeignKey(VocabularyItem, on_delete=models.CASCADE)

    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)

    question_text = models.TextField()
    options = models.JSONField()
    correct_answer = models.TextField()

    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.session.student_id} — Q{self.order}"


class VocabularyTestAnswer(models.Model):
    """
    Stores the student's answer for each question.
    """
    question = models.ForeignKey(VocabularyTestQuestion, on_delete=models.CASCADE, related_name="answers")

    selected_option = models.TextField()
    is_correct = models.BooleanField(default=False)

    answered_at = models.DateTimeField(auto_now_add=True)

    time_taken_seconds = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"Answer — {self.question.session.student_id}"
