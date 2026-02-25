# content/views/vocabulary/mixins.py

import uuid
import random
from django.db import transaction
from django.utils import timezone
from content.models.vocabulary import VocabularyAttempt, StudentVocabMastery


class VocabularyPracticeMixin:
    """Mixin with shared vocabulary practice functionality."""
    
    def generate_session_id(self):
        """Generate a unique session ID for grouping attempts."""
        return str(uuid.uuid4())
    
    @transaction.atomic
    def record_attempt(self, user, vocab_item, is_correct, session_id, time_taken=None):
        """Record a vocabulary attempt and update mastery."""
        
        # Create attempt record
        attempt = VocabularyAttempt.objects.create(
            user=user,
            vocab_item=vocab_item,
            session_id=session_id,
            is_correct=is_correct,
            time_taken_seconds=time_taken,
        )
        
        # Update or create mastery record
        mastery, created = StudentVocabMastery.objects.get_or_create(
            user=user,
            vocab_item=vocab_item,
            defaults={
                'mastery_level': 'learning',
                'last_practiced': timezone.now(),
                'total_attempts': 1,
                'correct_attempts': 1 if is_correct else 0,
            }
        )
        
        if not created:
            mastery.total_attempts += 1
            if is_correct:
                mastery.correct_attempts += 1
            mastery.last_practiced = timezone.now()
            
            # Calculate new mastery level based on accuracy and attempt count
            accuracy = mastery.accuracy_percentage
            
            if accuracy >= 90 and mastery.total_attempts >= 5:
                mastery.mastery_level = 'mastered'
            elif accuracy >= 70:
                mastery.mastery_level = 'learning'
            elif accuracy < 50 and mastery.total_attempts >= 3:
                mastery.mastery_level = 'review'
            
            mastery.save()
        
        return attempt, mastery
    
    def get_words_for_practice(self, vocab_items, user, limit=10, prioritize_review=True):
        """Get words prioritized for practice."""
        words = list(vocab_items)
        
        if prioritize_review:
            # Sort: review first, then new, then learning, then mastered last
            def priority(item):
                try:
                    mastery = StudentVocabMastery.objects.get(
                        user=user,
                        vocab_item=item
                    )
                    if mastery.mastery_level == 'review':
                        return 0
                    if mastery.mastery_level == 'learning':
                        return 2
                    if mastery.mastery_level == 'mastered':
                        return 3
                    return 1  # Should not happen
                except StudentVocabMastery.DoesNotExist:
                    return 1  # New words
            
            words.sort(key=priority)
        
        return words[:limit]