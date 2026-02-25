# content/admin/inlines/core.py

from django.contrib import admin
from django.utils.html import format_html
from content.models.core import LessonChunk


class LessonChunkInline(admin.StackedInline):
    """
    Allows teachers to break English text into smaller,
    manageable chunks for students to read.
    Each chunk can have its own audio files and focuses.
    """
    model = LessonChunk
    extra = 1
    min_num = 1
    max_num = 20  # Reasonable limit per lesson
    
    fields = (
        "order",
        "english_text",
        "translated_text",
        "audio_file",
        "translated_audio_file",
        "estimated_time_minutes",
        "chunk_preview",
    )
    
    readonly_fields = ("chunk_preview",)
    ordering = ("order",)
    
    def chunk_preview(self, obj):
        """Show a preview of the chunk with focus counts"""
        if not obj.pk:
            return "Preview available after saving"
        
        # Count focuses across all domains
        grammar_count = obj.grammar_focuses.count()
        punct_count = obj.punctuation_focuses.count()
        comp_count = obj.comprehension_focuses.count()
        vocab_count = obj.vocab_items.count()
        writing_count = obj.writing_focuses.count()
        pron_count = obj.pronunciation_focuses.count()
        
        total_focuses = grammar_count + punct_count + comp_count + vocab_count + writing_count + pron_count
        
        html = f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px;">
            <p><strong>Text Preview:</strong> {obj.english_text[:100]}...</p>
            <p><strong>Total Focuses:</strong> {total_focuses}</p>
            <table style="width:100%; font-size:0.9em;">
                <tr>
                    <td style="color: {'green' if grammar_count > 0 else 'gray'};">Grammar: {grammar_count}</td>
                    <td style="color: {'green' if punct_count > 0 else 'gray'};">Punctuation: {punct_count}</td>
                </tr>
                <tr>
                    <td style="color: {'green' if comp_count > 0 else 'gray'};">Comprehension: {comp_count}</td>
                    <td style="color: {'green' if vocab_count > 0 else 'gray'};">Vocabulary: {vocab_count}</td>
                </tr>
                <tr>
                    <td style="color: {'green' if writing_count > 0 else 'gray'};">Writing: {writing_count}</td>
                    <td style="color: {'green' if pron_count > 0 else 'gray'};">Pronunciation: {pron_count}</td>
                </tr>
            </table>
        """
        
        if obj.audio_file and obj.translated_audio_file:
            html += '<p style="color:green;">✓ Both audio files present</p>'
        elif obj.audio_file or obj.translated_audio_file:
            html += '<p style="color:orange;">⚠️ Only one audio file</p>'
        else:
            html += '<p style="color:red;">✗ No audio files</p>'
        
        html += "</div>"
        
        return format_html(html)
    chunk_preview.short_description = "Chunk Overview"