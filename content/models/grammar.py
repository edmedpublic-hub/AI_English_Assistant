from django.db import models
from .core import Lesson


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
