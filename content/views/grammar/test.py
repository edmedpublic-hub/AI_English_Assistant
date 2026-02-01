from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from content.models.grammar import GrammarQuestion, GrammarTestAttempt
from .core import _chunk_context, get_grammar_objects

@login_required
def grammar_test(request, chunk_id, focus_id):
    """
    High-stakes grammar assessment. 
    Requires 100% score for mastery according to project goals.
    """
    chunk, focus = get_grammar_objects(chunk_id, focus_id)
    concept = focus.concept

    # Fetch all questions for this focus
    questions = GrammarQuestion.objects.filter(focus=focus).order_by('?') # Randomize for tests

    if request.method == "POST":
        correct_count = 0
        total_questions = questions.count()
        results_snapshot = {}

        for q in questions:
            user_answer = request.POST.get(f"q{q.id}", "").strip()
            is_correct = user_answer.lower() == q.correct_answer.lower()
            
            if is_correct:
                correct_count += 1
            
            # Save a snapshot of the performance for this specific test run
            results_snapshot[q.id] = {
                "user_answer": user_answer,
                "is_correct": is_correct
            }

        # Calculate percentage
        score_percent = int((correct_count / total_questions) * 100) if total_questions > 0 else 0

        # Save the attempt to the database
        GrammarTestAttempt.objects.create(
            student=request.user,
            focus=focus,
            score_percent=score_percent,
            correct_answers=correct_count,
            total_questions=total_questions,
            questions_snapshot=results_snapshot
        )

        # Mastery Logic: Provide feedback based on the 100% rule
        if score_percent == 100:
            messages.success(request, "Congratulations! You have mastered this concept.")
        else:
            messages.error(request, f"You scored {score_percent}%. Mastery requires 100%. Please review and try again.")

        context = _chunk_context(chunk_id, focus, concept)
        context.update({
            "score": score_percent,
            "correct": correct_count,
            "total": total_questions,
            "submitted": True,
        })
        return render(request, "content/grammar/test_result.html", context)

    # GET request: Display the test
    context = _chunk_context(chunk_id, focus, concept)
    context.update({
        "questions": questions,
    })

    return render(request, "content/grammar/test.html", context)