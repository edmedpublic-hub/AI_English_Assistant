# content/views/writing/practice.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.utils import timezone

from content.models.writing import (
    WritingPrompt,
    WritingPracticeAttempt,
    ChunkWritingFocus,
)
from content.models.core import LessonChunk


class WritingPracticeView(LoginRequiredMixin, TemplateView):
    """
    Writing Practice View
    - Chunk + focus scoped
    - Tracks individual prompt attempts
    - Test unlocked if at least one valid response
    - 3 attempts max per cycle
    - For chunk-level writing (sentence/paragraph level)
    """
    template_name = "content/writing/practice.html"

    def get_chunk_and_focus(self):
        """Resolve chunk and focus objects from URL params."""
        chunk_id = self.kwargs.get('chunk_id')
        focus_id = self.kwargs.get('focus_id')
        
        chunk = get_object_or_404(LessonChunk, id=chunk_id)
        focus = get_object_or_404(
            ChunkWritingFocus, 
            id=focus_id,
            chunk=chunk
        )
        
        return chunk, focus

    def get_prompts(self, focus):
        """Fetch prompts for this focus."""
        return WritingPrompt.objects.filter(
            focus=focus
        ).order_by("id")

    def get_current_cycle(self, user, focus, prompt):
        """Get current practice cycle number for a specific prompt."""
        latest_attempt = WritingPracticeAttempt.objects.filter(
            user=user,
            prompt=prompt,
            focus=focus  # Focus is stored in practice attempts for chunk-level
        ).order_by('-cycle_number', '-attempt_number').first()
        
        if latest_attempt:
            return latest_attempt.cycle_number
        return 1

    def get_current_attempt_number(self, user, focus, prompt, cycle_number):
        """Get next attempt number for current cycle."""
        attempts_in_cycle = WritingPracticeAttempt.objects.filter(
            user=user,
            prompt=prompt,
            focus=focus,
            cycle_number=cycle_number
        ).count()
        
        return attempts_in_cycle + 1

    def get_practice_history(self, user, focus, prompt):
        """Get user's practice history for a specific prompt."""
        return WritingPracticeAttempt.objects.filter(
            user=user,
            prompt=prompt,
            focus=focus
        ).order_by('-cycle_number', '-attempt_number')

    def get_keyword_match_score(self, response_text, expected_keywords):
        """
        Calculate keyword match score.
        Returns percentage of expected keywords found in response.
        """
        if not expected_keywords:
            return 100  # No keywords to match = automatically pass
        
        # Parse expected keywords (comma-separated)
        keywords = [k.strip().lower() for k in expected_keywords.split(',') if k.strip()]
        
        if not keywords:
            return 100
        
        response_lower = response_text.lower()
        found_keywords = sum(1 for keyword in keywords if keyword in response_lower)
        
        return int((found_keywords / len(keywords)) * 100)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        chunk, focus = self.get_chunk_and_focus()
        prompts = self.get_prompts(focus)
        
        # Prepare prompts for template with attempt history
        for prompt in prompts:
            prompt.user_response = None
            prompt.feedback_ready = False
            
            # Get latest attempt for this prompt
            latest_attempt = WritingPracticeAttempt.objects.filter(
                user=self.request.user,
                prompt=prompt,
                focus=focus
            ).order_by('-created_at').first()
            
            if latest_attempt:
                prompt.latest_attempt = latest_attempt
                prompt.current_cycle = latest_attempt.cycle_number
                prompt.attempts_in_cycle = WritingPracticeAttempt.objects.filter(
                    user=self.request.user,
                    prompt=prompt,
                    focus=focus,
                    cycle_number=latest_attempt.cycle_number
                ).count()
                prompt.attempts_remaining = 3 - prompt.attempts_in_cycle
            else:
                prompt.latest_attempt = None
                prompt.current_cycle = 1
                prompt.attempts_in_cycle = 0
                prompt.attempts_remaining = 3
        
        context.update({
            "chunk": chunk,
            "focus": focus,
            "prompts": prompts,
            "submitted": False,
        })
        
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        chunk, focus = self.get_chunk_and_focus()
        prompts = self.get_prompts(focus)
        
        # Process responses
        any_answered = False
        any_valid = False
        practice_attempts = []
        
        for prompt in prompts:
            user_response = request.POST.get(f"p{prompt.id}", "").strip()
            
            if not user_response:
                continue
            
            any_answered = True
            
            # Basic validation: non-empty response
            is_valid = len(user_response) > 0
            
            # Get current cycle info for this prompt
            current_cycle = self.get_current_cycle(request.user, focus, prompt)
            attempt_number = self.get_current_attempt_number(
                request.user, focus, prompt, current_cycle
            )
            
            # Check if max attempts reached for this prompt
            if attempt_number > 3:
                messages.warning(
                    request,
                    f"You've used all 3 attempts for prompt {prompt.id}. "
                    f"This response will not be saved."
                )
                continue
            
            # Calculate keyword match score if expected keywords exist
            keyword_match_score = self.get_keyword_match_score(
                user_response, 
                prompt.expected_keywords
            )
            
            # For practice, we consider it valid if it's non-empty
            # Keyword matching is just for feedback, not for unlocking test
            if is_valid:
                any_valid = True
            
            # Create practice attempt
            practice_attempt = WritingPracticeAttempt.objects.create(
                user=request.user,
                focus=focus,
                prompt=prompt,
                attempt_number=attempt_number,
                cycle_number=current_cycle,
                response_text=user_response,
                keyword_match_score=keyword_match_score,
                time_spent_seconds=int(request.POST.get(f"time_{prompt.id}", 0) or 0),
                hints_used=int(request.POST.get(f"hints_{prompt.id}", 0) or 0),
            )
            
            practice_attempts.append(practice_attempt)
            
            # For template feedback
            prompt.user_response = user_response
            prompt.feedback_ready = True
            prompt.practice_attempt = practice_attempt
            
            # Provide keyword feedback
            if keyword_match_score is not None:
                if keyword_match_score == 100:
                    messages.success(
                        request,
                        f"Prompt {prompt.id}: Great! You used all expected keywords."
                    )
                elif keyword_match_score >= 70:
                    messages.info(
                        request,
                        f"Prompt {prompt.id}: Good attempt! You used most expected keywords."
                    )
                else:
                    messages.warning(
                        request,
                        f"Prompt {prompt.id}: Try to include more expected keywords: {prompt.expected_keywords}"
                    )
        
        if not any_answered:
            messages.warning(
                request,
                "Please attempt at least one prompt."
            )
            
            context = self.get_context_data()
            context.update({
                "prompts": prompts,
                "submitted": True,
            })
            return self.render_to_response(context)
        
        # Check if test should be unlocked (at least one valid response)
        if any_valid:
            messages.success(
                request,
                "Practice complete! You've submitted valid responses and unlocked the Final Test."
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
        
        context = self.get_context_data()
        context.update({
            "prompts": prompts,
            "submitted": True,
            "practice_attempts": practice_attempts,
        })
        
        return self.render_to_response(context)


class WritingPromptDetailView(LoginRequiredMixin, TemplateView):
    """
    Detailed view for a single writing prompt with attempt history.
    """
    template_name = "content/writing/prompt_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        prompt_id = self.kwargs.get('prompt_id')
        focus_id = self.kwargs.get('focus_id')
        chunk_id = self.kwargs.get('chunk_id')
        
        prompt = get_object_or_404(
            WritingPrompt,
            id=prompt_id,
            focus_id=focus_id,
            focus__chunk_id=chunk_id
        )
        
        # Get attempt history for this prompt
        attempts = WritingPracticeAttempt.objects.filter(
            user=self.request.user,
            prompt=prompt,
            focus_id=focus_id
        ).order_by('-cycle_number', '-attempt_number')
        
        # Group attempts by cycle
        attempts_by_cycle = {}
        for attempt in attempts:
            if attempt.cycle_number not in attempts_by_cycle:
                attempts_by_cycle[attempt.cycle_number] = []
            attempts_by_cycle[attempt.cycle_number].append(attempt)
        
        # Calculate stats
        total_attempts = attempts.count()
        best_score = attempts.order_by('-keyword_match_score').first()
        latest_attempt = attempts.first()
        
        context.update({
            "prompt": prompt,
            "focus": prompt.focus,
            "chunk": prompt.focus.chunk,
            "attempts": attempts,
            "attempts_by_cycle": attempts_by_cycle,
            "total_attempts": total_attempts,
            "best_score": best_score.keyword_match_score if best_score else None,
            "latest_attempt": latest_attempt,
            "has_mastered": attempts.filter(
                keyword_match_score=100
            ).exists(),
        })
        
        return context


class WritingPracticeHistoryView(LoginRequiredMixin, TemplateView):
    """
    Overview of all practice attempts for a focus.
    """
    template_name = "content/writing/practice_history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        chunk_id = self.kwargs.get('chunk_id')
        focus_id = self.kwargs.get('focus_id')
        
        focus = get_object_or_404(
            ChunkWritingFocus,
            id=focus_id,
            chunk_id=chunk_id
        )
        
        # Get all practice attempts for this focus
        attempts = WritingPracticeAttempt.objects.filter(
            user=self.request.user,
            focus=focus
        ).select_related(
            'prompt'
        ).order_by('-created_at')
        
        # Group by prompt
        attempts_by_prompt = {}
        for attempt in attempts:
            if attempt.prompt_id not in attempts_by_prompt:
                attempts_by_prompt[attempt.prompt_id] = {
                    'prompt': attempt.prompt,
                    'attempts': [],
                    'latest_attempt': attempt,
                    'best_score': 0,
                }
            
            attempts_by_prompt[attempt.prompt_id]['attempts'].append(attempt)
            
            if attempt.keyword_match_score and attempt.keyword_match_score > attempts_by_prompt[attempt.prompt_id]['best_score']:
                attempts_by_prompt[attempt.prompt_id]['best_score'] = attempt.keyword_match_score
        
        context.update({
            "focus": focus,
            "chunk": focus.chunk,
            "attempts_by_prompt": attempts_by_prompt,
            "total_prompts": WritingPrompt.objects.filter(focus=focus).count(),
            "completed_prompts": len([p for p in attempts_by_prompt.values() if p['attempts']]),
        })
        
        return context


# Keep the function-based view for backward compatibility if needed
writing_practice = WritingPracticeView.as_view()