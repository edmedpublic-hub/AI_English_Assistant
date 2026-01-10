# content/management/commands/generate_vocab.py
from django.core.management.base import BaseCommand
from content.models import LessonChunk, VocabularyItem
import spacy

nlp = spacy.load("en_core_web_sm")

class Command(BaseCommand):
    help = "Generate vocabulary items for all existing chunks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing vocabulary items"
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        for chunk in LessonChunk.objects.all():
            doc = nlp(chunk.english_text)
            candidates = [t for t in doc if t.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]]
            for token in candidates[:7]:
                if overwrite:
                    VocabularyItem.objects.update_or_create(
                        lesson=chunk.lesson,
                        chunk=chunk,
                        word=token.text,
                        defaults={"part_of_speech": token.pos_.lower()}
                    )
                else:
                    VocabularyItem.objects.get_or_create(
                        lesson=chunk.lesson,
                        chunk=chunk,
                        word=token.text,
                        part_of_speech=token.pos_.lower()
                    )
        self.stdout.write(self.style.SUCCESS("Vocabulary generated for all chunks"))
