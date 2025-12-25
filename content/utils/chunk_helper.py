# content/utils/chunk_helper.py

import re
from content.models import Lesson, LessonChunk

def chunk_lesson_text(lesson: Lesson, chunk_size: int = 15):
    """
    Splits a lesson's english_text into chunks of ~chunk_size sentences
    and saves them as LessonChunk records.
    
    Args:
        lesson (Lesson): The Lesson object to chunk.
        chunk_size (int): Number of sentences per chunk (default 15).
    """
    # Split text into sentences using punctuation marks
    sentences = re.split(r'(?<=[.!?]) +', lesson.english_text.strip())

    # Group sentences into chunks
    for i in range(0, len(sentences), chunk_size):
        chunk_text = " ".join(sentences[i:i+chunk_size])
        LessonChunk.objects.create(
            lesson=lesson,
            order=(i // chunk_size) + 1,
            english_text=chunk_text,
            urdu_translation="",  # add later in admin
        )