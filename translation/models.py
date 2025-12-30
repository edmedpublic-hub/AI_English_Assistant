import uuid
from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint, Index
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TranslationTextbook(TimestampedModel):  # ✅ now inherits TimestampedModel
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)  # allow blank in forms, enforce unique in DB
    description = models.TextField(blank=True)
    language = models.CharField(max_length=10, default='en')
    is_active = models.BooleanField(default=True)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["title"]
        indexes = [
            Index(fields=["slug"]),
            Index(fields=["published"]),
            Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate slug if missing
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class TranslationUnit(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    textbook = models.ForeignKey(
        TranslationTextbook,
        on_delete=models.CASCADE,
        related_name="units"
    )
    unit_number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["unit_number"]
        constraints = [
            UniqueConstraint(
                fields=["textbook", "unit_number"],
                name="uniq_unit_per_textbook"
            )
        ]
        indexes = [
            Index(fields=["unit_number"]),
        ]

    def __str__(self):
        return f"{self.textbook.title} - Unit {self.unit_number}: {self.title}"


class TranslationLesson(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey(
        TranslationUnit,
        on_delete=models.CASCADE,
        related_name="lessons"
    )
    lesson_number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255, blank=True)

    english_chunk = models.TextField(blank=True)
    urdu_chunk = models.TextField(blank=True)

    source_language = models.CharField(max_length=10, default="en")
    target_language = models.CharField(max_length=10, default="ur")

    normalized_english = models.TextField(blank=True)
    normalized_urdu = models.TextField(blank=True)

    audio_cache_url = models.URLField(blank=True, null=True)
    difficulty = models.CharField(max_length=50, blank=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["lesson_number"]
        constraints = [
            UniqueConstraint(
                fields=["unit", "lesson_number"],
                name="uniq_lesson_per_unit"
            )
        ]
        indexes = [
            Index(fields=["lesson_number"]),
            Index(fields=["published"]),
            Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.unit.title} - Lesson {self.lesson_number}: {self.title or 'Untitled'}"

    def mark_published(self):
        if not self.published:
            self.published = True
            self.published_at = timezone.now()
            self.save(update_fields=["published", "published_at"])

    def get_absolute_url(self):
        return reverse("translation:lesson-detail", kwargs={"pk": str(self.pk)})