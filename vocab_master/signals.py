from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Vocabulary, Synonym, Antonym, ExampleSentence

def check_reviewed_status(vocab):
    """
    Automatically mark a vocabulary as reviewed if it has:
    - At least 3 synonyms
    - At least 2 antonyms
    - At least 3 example sentences (covering simple, compound, complex)
    """
    synonyms_count = vocab.synonyms.count()
    antonyms_count = vocab.antonyms.count()
    examples = vocab.examples.all()

    # Check sentence types covered
    sentence_types = set(examples.values_list("sentence_type", flat=True))

    if synonyms_count >= 3 and antonyms_count >= 2 and {"simple", "compound", "complex"} <= sentence_types:
        if not vocab.reviewed:
            vocab.reviewed = True
            vocab.save(update_fields=["reviewed"])
    else:
        if vocab.reviewed:
            vocab.reviewed = False
            vocab.save(update_fields=["reviewed"])


@receiver([post_save, post_delete], sender=Synonym)
@receiver([post_save, post_delete], sender=Antonym)
@receiver([post_save, post_delete], sender=ExampleSentence)
def update_vocabulary_reviewed(sender, instance, **kwargs):
    """
    Triggered whenever synonyms, antonyms, or example sentences are added/removed.
    """
    check_reviewed_status(instance.vocabulary)