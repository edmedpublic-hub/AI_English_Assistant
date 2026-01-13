import spacy
from ..models import VocabularyItem

nlp = spacy.load("en_core_web_sm")

def generate_vocab(modeladmin, request, queryset):
    """Admin action: generate vocabulary for selected LessonChunks"""
    for chunk in queryset:
        doc = nlp(chunk.english_text)
        candidates = [t for t in doc if t.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]]
        for token in candidates[:7]:
            VocabularyItem.objects.get_or_create(
                lesson=chunk.lesson,
                chunk=chunk,
                word=token.text,
                part_of_speech=token.pos_.lower()
            )
    modeladmin.message_user(request, "Vocabulary generated for selected chunks.")

generate_vocab.short_description = "Generate vocabulary for selected chunks"