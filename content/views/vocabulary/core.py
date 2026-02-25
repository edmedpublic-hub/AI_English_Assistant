# content/views/vocabulary/core.py

from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from content.models.core import LessonChunk
from content.models.vocabulary import VocabularyItem, StudentVocabMastery


def get_vocab_context(chunk_id):
    """
    Centralized helper to fetch the LessonChunk and its hierarchy.
    Used by practice, testing, and hub views to ensure consistent object fetching.
    """
    chunk = get_object_or_404(
        LessonChunk.objects.select_related(
            "lesson__unit__textbook"
        ), 
        id=chunk_id
    )
    lesson = chunk.lesson
    
    return chunk, lesson


def _vocab_base_context(chunk, lesson):
    """
    Standardizes the context dictionary for vocabulary templates.
    """
    return {
        "chunk": chunk,
        "lesson": lesson,
        "unit": lesson.unit,
        "textbook": lesson.unit.textbook,
    }


class VocabularyBaseView(LoginRequiredMixin, TemplateView):
    """
    Base class for all vocabulary views with common functionality.
    """
    
    def get_chunk_and_lesson(self):
        """Get chunk and lesson from URL kwargs."""
        chunk_id = self.kwargs.get('chunk_id')
        return get_vocab_context(chunk_id)
    
    def get_base_context(self):
        """Get base context with chunk, lesson, unit, textbook."""
        chunk, lesson = self.get_chunk_and_lesson()
        return _vocab_base_context(chunk, lesson)
    
    def get_user_mastery(self, vocab_item):
        """Get user's mastery for a specific vocabulary item."""
        try:
            return StudentVocabMastery.objects.get(
                user=self.request.user,
                vocab_item=vocab_item
            )
        except StudentVocabMastery.DoesNotExist:
            return None
    
    def get_mastery_stats(self, vocab_items):
        mastery_records = StudentVocabMastery.objects.filter(
            user=self.request.user,
            vocab_item__in=vocab_items
        )
        mastery_map = {m.vocab_item_id: m for m in mastery_records}
        stats = {'total': 0, 'mastered': 0, 'learning': 0, 'review': 0, 'new': 0}
        for item in vocab_items:
            stats['total'] += 1
            m = mastery_map.get(item.id)
            stats[m.mastery_level if m else 'new'] += 1
        return stats