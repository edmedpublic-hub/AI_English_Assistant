# content/views/vocabulary/test.py

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.db import models
from django.utils import timezone

from content.models.core import LessonChunk
from content.models.testing import VocabularyUnitTestAttempt
from content.models.vocabulary import VocabularyItem
from ..test_engine import build_questions
from .core import get_vocab_context, _vocab_base_context, VocabularyBaseView


@login_required
def chunk_vocabulary_test(request, chunk_id):
    """
    High-stakes vocabulary assessment with session-based progress.
    URL: /vocabulary/test/<int:chunk_id>/
    """
    chunk, lesson = get_vocab_context(chunk_id)
    
    # Get vocabulary items
    vocab_items = list(chunk.vocab_items.all())
    
    if not vocab_items:
        messages.warning(request, "No vocabulary items available for this chunk.")
        return redirect('content:chunk_hub', chunk_id=chunk.id)

    # Handle retake logic
    if request.GET.get("retake") == "1":
        # Clear existing test session
        test_session_key = f"vocab_test_{chunk_id}"
        if test_session_key in request.session:
            del request.session[test_session_key]
        messages.info(request, "Starting a new test attempt.")
        return redirect('content:vocabulary:test', chunk_id=chunk.id)

    # Initialize test in session if not present
    test_session_key = f"vocab_test_{chunk_id}"
    
    if test_session_key not in request.session:
        questions = build_questions(vocab_items)

        if not questions:
            context = _vocab_base_context(chunk, lesson)
            context.update({
                "error": "No valid test questions could be generated.",
                "vocab_items": vocab_items,
            })
            return render(request, "content/vocab/test.html", context)

        request.session[test_session_key] = {
            "questions": questions,
            "current_index": 0,
            "score": 0,
            "started_at": timezone.now().isoformat(),
            "answers": [],  # Track user answers for each question
            "chunk_id": chunk_id,
        }
        request.session.modified = True

    test_data = request.session[test_session_key]
    questions = test_data["questions"]
    current_index = test_data["current_index"]

    # Test Completion Logic
    if current_index >= len(questions):
        total = len(questions)
        correct = test_data["score"]
        percent = round((correct / total) * 100) if total > 0 else 0

        # Save result if not already saved
        if not test_data.get("saved"):
            attempt = VocabularyUnitTestAttempt.objects.create(
                user=request.user,
                lesson=lesson,
                chunk=chunk,
                score_percent=percent,
                correct_answers=correct,
                total_questions=total,
                questions_data=questions,
                answers_data=test_data.get("answers", []),
            )
            test_data["saved"] = True
            test_data["attempt_id"] = attempt.id
            request.session.modified = True

        context = _vocab_base_context(chunk, lesson)
        context.update({
            "score": percent,
            "correct": correct,
            "total": total,
            "passed": percent >= 70,  # Consider 70% as passing
            "can_retake": percent < 100,
            "attempt_id": test_data.get("attempt_id"),
        })
        return render(request, "content/vocab/test/result.html", context)

    # Active Question Logic
    current_question = questions[current_index]

    if request.method == "POST":
        selected_option = request.POST.get("option")
        
        # Record answer
        is_correct = (selected_option == current_question["answer"])
        
        # Update test data
        test_data["answers"].append({
            "question_index": current_index,
            "question": current_question["question"],
            "selected": selected_option,
            "correct": current_question["answer"],
            "is_correct": is_correct,
        })
        
        if is_correct:
            test_data["score"] += 1
            
        test_data["current_index"] += 1
        request.session.modified = True
        
        return redirect('content:vocabulary:test', chunk_id=chunk.id)

    context = _vocab_base_context(chunk, lesson)
    context.update({
        "question": current_question,
        "question_number": current_index + 1,
        "total_questions": len(questions),
        "progress_percent": round(((current_index) / len(questions)) * 100) if questions else 0,
        "chunk_id": chunk_id,
    })
    
    return render(request, "content/vocab/test.html", context)


@login_required
@require_GET
def test_history(request, chunk_id=None):
    """
    Show all test attempts for the current user.
    If chunk_id provided, filter by that chunk.
    """
    # Base queryset
    attempts = VocabularyUnitTestAttempt.objects.filter(user=request.user)
    
    # Add chunk filter if provided
    if chunk_id:
        chunk = get_object_or_404(LessonChunk, id=chunk_id)
        attempts = attempts.filter(chunk=chunk)
    else:
        chunk = None
    
    # Optimize with select_related
    attempts = attempts.select_related("lesson", "chunk").order_by("-created_at")
    
    # Calculate statistics
    total_tests = attempts.count()
    passed_tests = attempts.filter(score_percent__gte=70).count()
    avg_score = attempts.aggregate(avg=models.Avg('score_percent'))['avg'] or 0
    
    # Group by chunk for better display
    chunk_stats = {}
    for attempt in attempts:
        chunk_id = attempt.chunk_id
        if chunk_id not in chunk_stats:
            chunk_stats[chunk_id] = {
                'chunk': attempt.chunk,
                'attempts': 0,
                'best_score': 0,
                'latest_attempt': attempt.created_at,
            }
        chunk_stats[chunk_id]['attempts'] += 1
        if attempt.score_percent > chunk_stats[chunk_id]['best_score']:
            chunk_stats[chunk_id]['best_score'] = attempt.score_percent
        if attempt.created_at > chunk_stats[chunk_id]['latest_attempt']:
            chunk_stats[chunk_id]['latest_attempt'] = attempt.created_at
    
    return render(request, "content/vocab/test/history.html", {
        "attempts": attempts,
        "chunk_stats": chunk_stats.values(),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "avg_score": round(avg_score),
        "chunk": chunk,  # Will be None for global history
    })


@login_required
@require_GET
def attempt_detail(request, attempt_id):
    """Show details of a specific test attempt."""
    attempt = get_object_or_404(
        VocabularyUnitTestAttempt, 
        id=attempt_id, 
        user=request.user
    )
    
    # Ensure questions_data is a list
    questions = attempt.questions_data or []
    answers = attempt.answers_data or []
    
    # Combine questions with answers for display
    question_data = []
    for i, q in enumerate(questions):
        answer_info = next((a for a in answers if a.get('question_index') == i), {})
        question_data.append({
            'question': q,
            'user_answer': answer_info.get('selected'),
            'correct_answer': answer_info.get('correct', q.get('answer')),
            'is_correct': answer_info.get('is_correct', False),
        })
    
    return render(request, "content/vocab/test/attempt_detail.html", {
        "attempt": attempt,
        "question_data": question_data,
        "chunk": attempt.chunk,
        "lesson": attempt.lesson,
    })


@login_required
@require_POST
def save_test_answer(request, chunk_id):
    """
    AJAX endpoint to save answer without page reload (for enhanced UX).
    """
    import json
    from django.http import JsonResponse
    
    try:
        data = json.loads(request.body)
        question_index = data.get('question_index')
        selected_option = data.get('selected_option')
        
        test_session_key = f"vocab_test_{chunk_id}"
        
        if test_session_key not in request.session:
            return JsonResponse({'error': 'Test session not found'}, status=404)
        
        test_data = request.session[test_session_key]
        questions = test_data["questions"]
        
        if question_index >= len(questions):
            return JsonResponse({'error': 'Invalid question index'}, status=400)
        
        current_question = questions[question_index]
        is_correct = (selected_option == current_question["answer"])
        
        # Record answer
        test_data["answers"].append({
            "question_index": question_index,
            "question": current_question["question"],
            "selected": selected_option,
            "correct": current_question["answer"],
            "is_correct": is_correct,
        })
        
        if is_correct:
            test_data["score"] += 1
            test_data["current_index"] += 1
            
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'is_correct': is_correct,
            'correct_answer': current_question["answer"],
            'current_score': test_data["score"],
            'next_index': test_data["current_index"] + 1,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Optional: Class-based version for more complex test logic
class VocabularyTestView(VocabularyBaseView):
    """
    Class-based view for vocabulary testing (alternative to function-based).
    """
    template_name = "content/vocab/test.html"
    result_template = "content/vocab/test/result.html"
    
    def get(self, request, chunk_id):
        chunk, lesson = self.get_chunk_and_lesson()
        vocab_items = list(chunk.vocab_items.all())
        
        if not vocab_items:
            messages.warning(request, "No vocabulary items available for this chunk.")
            return redirect('content:chunk_hub', chunk_id=chunk.id)
        
        # Check for retake
        if request.GET.get("retake") == "1":
            self.clear_test_session(request, chunk_id)
            messages.info(request, "Starting a new test attempt.")
            return redirect('content:vocabulary:test', chunk_id=chunk.id)
        
        # Get or create test session
        test_data = self.get_test_session(request, chunk_id, vocab_items)
        
        if test_data['current_index'] >= test_data['total']:
            return self.render_result(request, chunk, lesson, test_data)
        
        return self.render_question(request, chunk, lesson, test_data)
    
    def post(self, request, chunk_id):
        test_session_key = f"vocab_test_{chunk_id}"
        test_data = request.session.get(test_session_key)
        
        if not test_data:
            return redirect('content:vocabulary:test', chunk_id=chunk_id)
        
        question_index = int(request.POST.get('question_index', 0))
        selected_option = request.POST.get('option')
        
        # Process answer
        self.process_answer(test_data, question_index, selected_option)
        request.session.modified = True
        
        return redirect('content:vocabulary:test', chunk_id=chunk_id)
    
    def clear_test_session(self, request, chunk_id):
        test_session_key = f"vocab_test_{chunk_id}"
        if test_session_key in request.session:
            del request.session[test_session_key]
    
    def get_test_session(self, request, chunk_id, vocab_items):
        test_session_key = f"vocab_test_{chunk_id}"
        
        if test_session_key not in request.session:
            questions = build_questions(vocab_items)
            request.session[test_session_key] = {
                "questions": questions,
                "current_index": 0,
                "score": 0,
                "started_at": timezone.now().isoformat(),
                "answers": [],
                "chunk_id": chunk_id,
            }
            request.session.modified = True
        
        return request.session[test_session_key]
    
    def process_answer(self, test_data, question_index, selected_option):
        questions = test_data["questions"]
        
        if question_index >= len(questions):
            return
        
        current_question = questions[question_index]
        is_correct = (selected_option == current_question["answer"])
        
        test_data["answers"].append({
            "question_index": question_index,
            "selected": selected_option,
            "is_correct": is_correct,
        })
        
        if is_correct:
            test_data["score"] += 1
            
        test_data["current_index"] += 1
    
    def render_question(self, request, chunk, lesson, test_data):
        questions = test_data["questions"]
        current_index = test_data["current_index"]
        current_question = questions[current_index]
        
        context = _vocab_base_context(chunk, lesson)
        context.update({
            "question": current_question,
            "question_number": current_index + 1,
            "total_questions": len(questions),
            "progress_percent": round((current_index / len(questions)) * 100),
            "chunk_id": chunk.id,
        })
        
        return render(request, self.template_name, context)
    
    def render_result(self, request, chunk, lesson, test_data):
        total = len(test_data["questions"])
        correct = test_data["score"]
        percent = round((correct / total) * 100) if total > 0 else 0
        
        # Save attempt if not already saved
        if not test_data.get("saved"):
            attempt = VocabularyUnitTestAttempt.objects.create(
                user=request.user,
                lesson=lesson,
                chunk=chunk,
                score_percent=percent,
                correct_answers=correct,
                total_questions=total,
                questions_data=test_data["questions"],
                answers_data=test_data["answers"],
            )
            test_data["saved"] = True
            test_data["attempt_id"] = attempt.id
            request.session.modified = True
        
        context = _vocab_base_context(chunk, lesson)
        context.update({
            "score": percent,
            "correct": correct,
            "total": total,
            "passed": percent >= 70,
            "can_retake": percent < 100,
            "attempt_id": test_data.get("attempt_id"),
        })
        
        return render(request, self.result_template, context)


# Export both function and class-based views

vocabulary_test_view = VocabularyTestView.as_view()  # Add class-based option