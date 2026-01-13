from django.db import models
from .core import Lesson


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
