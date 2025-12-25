# content/utils/ai_helpers.py

from gtts import gTTS
from deep_translator import GoogleTranslator
import os

from content.models import LessonChunk


def translate_to_urdu(text: str) -> str:
    """
    Translate English text into Urdu using deep-translator.
    """
    try:
        return GoogleTranslator(source="en", target="ur").translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return ""


def generate_audio(text: str, lang: str, filename: str) -> str:
    """
    Generate an MP3 audio file for given text using gTTS.
    Args:
        text (str): The text to convert to speech.
        lang (str): Language code ('en' for English, 'ur' for Urdu).
        filename (str): Output filename.
    Returns:
        str: Path to the saved audio file.
    """
    try:
        tts = gTTS(text=text, lang=lang)
        filepath = os.path.join("media", "chunk_audios", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        tts.save(filepath)
        return filepath
    except Exception as e:
        print(f"Audio generation error: {e}")
        return ""


def process_lesson_chunks_with_audio(lesson_id: int):
    """
    For all chunks in a lesson:
    - Use existing Urdu translations (already pasted by teacher).
    - Generate English + Urdu audio files.
    - Attach audio file paths to chunk fields.
    """
    chunks = LessonChunk.objects.filter(lesson_id=lesson_id)
    if not chunks.exists():
        print(f"No chunks found for lesson {lesson_id}.")
        return

    for chunk in chunks:
        print(f"Processing chunk {chunk.id}...")

        # Generate English audio
        en_audio_path = generate_audio(chunk.english_text, "en", f"chunk_{chunk.id}_en.mp3")
        if en_audio_path:
            chunk.english_audio = en_audio_path

        # Generate Urdu audio (using teacher's own translation)
        if chunk.urdu_translation:
            ur_audio_path = generate_audio(chunk.urdu_translation, "ur", f"chunk_{chunk.id}_ur.mp3")
            if ur_audio_path:
                chunk.urdu_audio = ur_audio_path

        chunk.save()

    print(f"Processed {chunks.count()} chunks for lesson {lesson_id}.")