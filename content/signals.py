from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LessonChunk, VocabularyItem
import spacy

nlp = spacy.load("en_core_web_sm")

@receiver(post_save, sender=LessonChunk)
def generate_vocab_for_chunk(sender, instance, created, **kwargs):
    """
    Automatically extract 5–7 vocabulary words when a new LessonChunk is created.
    """
    if created:
        doc = nlp(instance.english_text)
        # Filter: nouns, verbs, adjectives, adverbs
        candidates = [t for t in doc if t.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]]
        # Limit to 7 words max
        for token in candidates[:7]:
            VocabularyItem.objects.get_or_create(
                lesson=instance.lesson,
                chunk=instance,
                word=token.text,
                part_of_speech=token.pos_.lower()
            )
