# content/views/writing/practice.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from content.models.writing import (
    WritingPrompt,
    WritingResponse,
    WritingAttempt,
    WritingPracticeAttempt,
)
from .core import _chunk_context, get_writing_objects


@login_required
def writing_practice(request, chunk_id, focus_id):
    """
    Writing Practice View
    - Chunk + focus scoped
    - Safe if no prompts
    - Test unlocked if ≥1 valid response
    - Redirects to Final Test on success
    """

    # 1. Resolve core objects
    chunk, focus, unit, task = get_writing_objects(chunk_id, focus_id=focus_id)

    # 2. Fetch prompts
    prompts = WritingPrompt.objects.filter(focus=focus).order_by("id")

    if not prompts.exists():
        messages.error(
            request,
            "This writing focus has no practice prompts yet."
        )
        return redirect(
            "content:chunk_writing",
            chunk_id=chunk.id
        )

    # 3. Normalize (attach placeholders for UI)
    for p in prompts:
        p.user_response = None
        p.feedback_ready = False

    submitted = False

    # 4. Handle POST
    if request.method == "POST":
        submitted = True
        any_valid = False
        any_answered = False

        for p in prompts:
            user_response = request.POST.get(f"p{p.id}", "").strip()
            if not user_response:
                continue

            any_answered = True

            # Basic validation: non-empty response unlocks practice
            is_valid = len(user_response) > 0
            if is_valid:
                any_valid = True

            # Save/update response
            response_obj, _ = WritingResponse.objects.update_or_create(
                student=request.user,
                prompt=p,
                defaults={
                    "response_text": user_response,
                }
            )

            # Log attempt
            WritingAttempt.objects.create(
                response=response_obj,
                attempt_number=response_obj.attempts.count() + 1,
                time_spent="00:00:00",  # placeholder, can be tracked via frontend
                hints_used=0,
            )

            p.user_response = user_response
            p.feedback_ready = True

        if not any_answered:
            messages.warning(
                request,
                "Please attempt at least one prompt."
            )

        elif any_valid:
            WritingPracticeAttempt.objects.get_or_create(
                student=request.user,
                focus=focus,
            )

            messages.success(
                request,
                "Practice complete! Redirecting you to the Final Test."
            )

            return redirect(
                "content:writing:test",
                chunk_id=chunk.id,
                focus_id=focus.id,
            )

        else:
            messages.warning(
                request,
                "You must submit at least one valid response to unlock the Final Test."
            )

    # 5. Context
    context = _chunk_context(chunk, focus, task)
    context.update({
        "prompts": prompts,
        "submitted": submitted,
    })

    return render(
        request,
        "content/writing/practice.html",
        context
    )