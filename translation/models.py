import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.urls import reverse


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class TranslationTextbook(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, null=True, unique=True)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=10, default='en')  # primary language of textbook
    is_active = models.BooleanField(default=True)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class TranslationUnit(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    textbook = models.ForeignKey(TranslationTextbook, on_delete=models.CASCADE, related_name='units')
    unit_number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['unit_number']
        unique_together = ('textbook', 'unit_number')

    def __str__(self):
        return f"{self.textbook.title} - Unit {self.unit_number}: {self.title}"


class TranslationLesson(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey(TranslationUnit, on_delete=models.CASCADE, related_name='lessons')
    lesson_number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255, blank=True)
    # store the full chunk(s)
    english_chunk = models.TextField(blank=True)
    urdu_chunk = models.TextField(blank=True)

    # metadata & workflow fields
    source_language = models.CharField(max_length=10, default='en')  # e.g., 'en'
    target_language = models.CharField(max_length=10, default='ur')  # e.g., 'ur'
    normalized_english = models.TextField(blank=True)  # optional preprocessed copy used for splitting
    normalized_urdu = models.TextField(blank=True)
    audio_cache_url = models.URLField(blank=True, null=True)  # optional pre-generated audio file for whole lesson
    difficulty = models.CharField(max_length=50, blank=True)  # e.g., "A1", "Intermediate"
    author = models.ForeignKey(getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
                               on_delete=models.SET_NULL, null=True, blank=True)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['lesson_number']
        unique_together = ('unit', 'lesson_number')

    def __str__(self):
        return f"{self.unit.title} - Lesson {self.lesson_number}: {self.title or 'Untitled'}"

    def mark_published(self):
        if not self.published:
            self.published = True
            self.published_at = timezone.now()
            self.save(update_fields=['published', 'published_at'])

    def get_absolute_url(self):
        # example URL pattern name: translation:lesson-detail
        return reverse('translation:lesson-detail', kwargs={'pk': str(self.pk)})
