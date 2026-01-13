from django.db import models
from .core import LessonChunk


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
