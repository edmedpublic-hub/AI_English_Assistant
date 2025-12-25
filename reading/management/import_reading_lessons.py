import json
from django.core.management.base import BaseCommand
from reading.models import ReadingLesson
from django.conf import settings
import os

class Command(BaseCommand):
    help = "Import reading lessons from JSON file"

    def handle(self, *args, **kwargs):
        data_dir = os.path.join(settings.BASE_DIR, "data")
        file_path = os.path.join(data_dir, "reading_lesson1.json")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Supports both string text and list-of-paragraphs text
        text_content = (
            "\n\n".join(data["text"]) if isinstance(data["text"], list) else data["text"]
        )

        lesson = ReadingLesson.objects.create(
            title=data["title"],
            content=text_content,
        )

        self.stdout.write(self.style.SUCCESS(f"Imported lesson: {lesson.title}"))
