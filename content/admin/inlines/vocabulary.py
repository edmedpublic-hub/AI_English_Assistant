from django.contrib import admin
from content.models.vocabulary import VocabularyItem


class VocabularyItemInline(admin.TabularInline):
    """
    Allows editing vocabulary directly inside LessonChunk.
    This is your main authoring UX.
    """
    model = VocabularyItem
    extra = 1

    fields = (
        "word",
        "part_of_speech",
        "urdu",
        "meaning",
        "synonyms",
        "antonyms",
        "example_sentence",
    )

    autocomplete_fields = ()