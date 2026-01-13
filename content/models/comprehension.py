from django.db import models
from .core import Lesson


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
