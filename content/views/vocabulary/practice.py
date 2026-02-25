# content/views/vocabulary/practice.py

import random
import re
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .core import VocabularyBaseView, get_vocab_context, _vocab_base_context
from .mixins import VocabularyPracticeMixin
from content.models.vocabulary import VocabularyItem, StudentVocabMastery


class PracticeHubView(VocabularyPracticeMixin, VocabularyBaseView):
    """
    Practice hub with flip cards for a specific chunk.
    URL: /vocabulary/practice/<int:chunk_id>/
    """
    template_name = "content/vocab/practice.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chunk, lesson = self.get_chunk_and_lesson()
        
        # Get all vocabulary items for this chunk
        vocab_items = list(chunk.vocab_items.all())
        
        # Get mastery stats
        mastery_stats = self.get_mastery_stats(chunk.vocab_items.all())
        
        # Get prioritized words for practice (review first, then new, then learning)
        practice_words = self.get_words_for_practice(
            vocab_items, 
            user=self.request.user,
            limit=len(vocab_items)  # Get all, but prioritized
        )
        
        # Add mastery info to each vocab item
        for item in practice_words:
            item.mastery = self.get_user_mastery(item)
        
        context.update({
            'chunk': chunk,  # Explicitly add chunk to context
            'lesson': lesson,
            'vocab_items': practice_words,
            'total_count': len(practice_words),
            'mastery_stats': mastery_stats,
        })
        
        return context


# Export the view with the expected function name
chunk_vocabulary_practice = PracticeHubView.as_view()


@require_GET
def chunk_vocab_fill(request, chunk_id):
    """
    Fill-in-the-blank practice mode.
    """
    chunk, lesson = get_vocab_context(chunk_id)
    vocab_items = list(chunk.vocab_items.all())
    questions = []
    session_id = generate_session_id()

    for vocab in vocab_items:
        if not vocab.example_sentence:
            continue

        sentences = [s.strip() for s in vocab.example_sentence.split('.') if s.strip()]
        if not sentences:
            continue

        sentence = sentences[0]
        # Replace the word with blanks
        blank = re.sub(re.escape(vocab.word), "________", sentence, flags=re.IGNORECASE)

        # Get distractors (words from same chunk, excluding current)
        distractors = [v.word for v in vocab_items if v.id != vocab.id]
        
        # Select 3 random distractors (or fewer if not enough)
        num_distractors = min(3, len(distractors))
        selected_distractors = random.sample(distractors, num_distractors) if distractors else []
        
        # Create options (distractors + correct answer)
        options = selected_distractors + [vocab.word]
        random.shuffle(options)

        questions.append({
            'id': vocab.id,
            'word': vocab.word,
            'sentence': blank,
            'options': options,
            'answer': vocab.word,
            'session_id': session_id,
        })

    context = _vocab_base_context(chunk, lesson)
    context.update({
        'chunk': chunk,  # Explicitly add chunk
        'questions': questions,
        'mode': 'fill',
        'total_questions': len(questions),
    })
    
    return render(request, "content/vocab/practice/fill.html", context)


@require_GET
def chunk_vocab_synonyms(request, chunk_id):
    """
    Synonym matching practice mode.
    """
    chunk, lesson = get_vocab_context(chunk_id)
    vocab_items = list(chunk.vocab_items.all())
    questions = []
    session_id = generate_session_id()

    for vocab in vocab_items:
        if not vocab.synonyms:
            continue

        # Parse synonyms (comma-separated)
        syns = [s.strip() for s in vocab.synonyms.split(',') if s.strip()]
        if not syns:
            continue

        # Use first synonym as correct answer
        correct = syns[0]
        
        # Build distractor pool from other words' synonyms
        distractor_pool = []
        for other in vocab_items:
            if other.id == vocab.id or not other.synonyms:
                continue
            other_syns = [s.strip() for s in other.synonyms.split(',') if s.strip()]
            distractor_pool.extend(other_syns)

        # Select 3 random distractors
        if len(distractor_pool) >= 3:
            distractors = random.sample(distractor_pool, 3)
        else:
            # Fallback to other words if not enough synonyms
            other_words = [v.word for v in vocab_items if v.id != vocab.id]
            distractors = random.sample(other_words, min(3, len(other_words)))

        options = distractors + [correct]
        random.shuffle(options)

        questions.append({
            'id': vocab.id,
            'word': vocab.word,
            'sentence': f"Choose the best synonym for '{vocab.word}':",
            'options': options,
            'answer': correct,
            'session_id': session_id,
        })

    context = _vocab_base_context(chunk, lesson)
    context.update({
        'chunk': chunk,  # Explicitly add chunk
        'questions': questions,
        'mode': 'synonyms',
        'total_questions': len(questions),
    })
    
    return render(request, "content/vocab/practice/synonyms.html", context)


@require_GET
def chunk_vocab_antonyms(request, chunk_id):
    """
    Antonym matching practice mode.
    """
    chunk, lesson = get_vocab_context(chunk_id)
    vocab_items = list(chunk.vocab_items.all())
    questions = []
    session_id = generate_session_id()

    for vocab in vocab_items:
        if not vocab.antonyms:
            continue

        # Parse antonyms (comma-separated)
        ants = [a.strip() for a in vocab.antonyms.split(',') if a.strip()]
        if not ants:
            continue

        # Use first antonym as correct answer
        correct = ants[0]
        
        # Use other words from chunk as distractors
        distractors = [v.word for v in vocab_items if v.id != vocab.id]
        
        # Select 3 random distractors
        selected_distractors = random.sample(distractors, min(3, len(distractors)))

        options = selected_distractors + [correct]
        random.shuffle(options)

        questions.append({
            'id': vocab.id,
            'word': vocab.word,
            'sentence': f"Choose the best antonym for '{vocab.word}':",
            'options': options,
            'answer': correct,
            'session_id': session_id,
        })

    context = _vocab_base_context(chunk, lesson)
    context.update({
        'chunk': chunk,  # Explicitly add chunk
        'questions': questions,
        'mode': 'antonyms',
        'total_questions': len(questions),
    })
    
    return render(request, "content/vocab/practice/antonyms.html", context)


# AJAX endpoint for recording practice attempts
@login_required
@require_POST
def record_practice_attempt(request):
    """
    AJAX endpoint to record a practice attempt and return updated mastery.
    """
    import json
    
    try:
        data = json.loads(request.body)
        
        vocab_id = data.get('vocab_id')
        is_correct = data.get('is_correct')
        session_id = data.get('session_id')
        time_taken = data.get('time_taken')  # in seconds
        
        vocab_item = VocabularyItem.objects.get(id=vocab_id)
        
        # Use the mixin methods
        helper = VocabularyPracticeMixin()
        attempt, mastery = helper.record_attempt(
            user=request.user,
            vocab_item=vocab_item,
            is_correct=is_correct,
            session_id=session_id,
            time_taken=time_taken
        )
        
        return JsonResponse({
            'success': True,
            'mastery_level': mastery.mastery_level,
            'accuracy': mastery.accuracy_percentage,
            'total_attempts': mastery.total_attempts,
        })
        
    except VocabularyItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vocabulary item not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# Helper function to generate session ID
def generate_session_id():
    """Generate a unique session ID."""
    import uuid
    return str(uuid.uuid4())