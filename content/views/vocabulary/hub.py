# content/views/vocabulary/hub.py

from .core import VocabularyBaseView
from content.models.vocabulary import VocabularyAttempt


class ChunkVocabularyHubView(VocabularyBaseView):
    """
    Main landing page for a chunk's vocabulary section.
    URL: /vocabulary/hub/<int:chunk_id>/
    """
    template_name = "content/vocab/hub.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chunk, lesson = self.get_chunk_and_lesson()
        
        # Get all vocabulary items for this chunk
        vocab_items = chunk.vocab_items.all()
        
        # Get mastery stats using the base class method
        mastery_stats = self.get_mastery_stats(vocab_items)
        
        # Get attempt statistics
        attempts = VocabularyAttempt.objects.filter(
            user=self.request.user,
            vocab_item__in=vocab_items
        )
        
        total_attempts = attempts.count()
        correct_attempts = attempts.filter(is_correct=True).count()
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        # Get recent attempts (last 10)
        recent_attempts = attempts.select_related('vocab_item').order_by('-created_at')[:10]
        
        # Words needing review - optimized single pass
        needs_review = []
        for item in vocab_items:
            mastery = self.get_user_mastery(item)
            if not mastery:  # New words
                needs_review.append(item)
            elif mastery.mastery_level == 'review':  # Review state
                needs_review.append(item)
            elif mastery.accuracy_percentage < 70:  # Low accuracy
                needs_review.append(item)
        
        context.update({
            'chunk': chunk,
            'vocab_items': vocab_items,
            'mastery_stats': mastery_stats,
            'total_attempts': total_attempts,
            'accuracy': round(accuracy),
            'recent_attempts': recent_attempts,
            'needs_review': needs_review[:5],  # Top 5 needing review
            'words_mastered': mastery_stats['mastered'],
            'words_learning': mastery_stats['learning'] + mastery_stats['review'],
            'words_new': mastery_stats['new'],
        })
        
        return context


# Function-based view for URL routing
chunk_vocabulary = ChunkVocabularyHubView.as_view()