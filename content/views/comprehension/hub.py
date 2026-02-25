from django.views.generic import TemplateView

from .core import build_chunk_context, get_comprehension_objects
from content.models.comprehension import (
    ChunkComprehensionFocus,
    ComprehensionTestAttempt,
)
from django.contrib.auth.mixins import LoginRequiredMixin

class ChunkComprehensionHubView(TemplateView):
    template_name = "content/chunks/chunk_comprehension.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request
        chunk_id = self.kwargs["chunk_id"]

        # --- 1. Resolve chunk via audited helper ---
        chunk, _ = get_comprehension_objects(chunk_id)
        context.update(build_chunk_context(chunk))

        # --- 2. Fetch focuses in deterministic pedagogical order ---
        focuses = list(
            ChunkComprehensionFocus.objects
            .filter(chunk=chunk)
            .order_by("sequence_order", "level", "id")
        )

        mastered_focus_ids = set()
        attempted_focus_ids = set()

        # --- 3. Bulk-load student attempts (single query, no N+1) ---
        if request.user.is_authenticated and focuses:
            focus_ids = [f.id for f in focuses]

            user_attempts = (
                ComprehensionTestAttempt.objects
                .filter(user=request.user, focus_id__in=focus_ids)
                .values_list("focus_id", "is_mastered")
            )

            for f_id, is_mastered in user_attempts:
                attempted_focus_ids.add(f_id)
                if is_mastered:
                    mastered_focus_ids.add(f_id)

        # --- 4. Attach LMS progress state (pure Python, O(n)) ---
        for focus in focuses:
            is_mastered = focus.id in mastered_focus_ids
            is_attempted = focus.id in attempted_focus_ids

            focus.is_mastered = is_mastered
            focus.practice_attempted = is_attempted

            if is_mastered:
                focus.progress_state = "mastered"
            elif is_attempted:
                focus.progress_state = "in_progress"
            else:
                focus.progress_state = "not_started"

        # --- 4.5 Sequential locking (LMS progression gate) ---
        previous_mastered = True
        for focus in focuses:
            focus.is_locked = not previous_mastered
            previous_mastered = focus.is_mastered

        # --- 5. Summary metrics for progress bar ---
        total_focuses = len(focuses)
        mastered_count = len(mastered_focus_ids)

        mastery_percent = (
            int((mastered_count / total_focuses) * 100)
            if total_focuses > 0 else 0
        )

        context.update({
            "focuses": focuses,
            "total_focuses": total_focuses,
            "mastered_count": mastered_count,
            "mastery_percent": mastery_percent,
        })

        return context


# Backward-compatible alias (keeps URLs unchanged)
chunk_comprehension_view = ChunkComprehensionHubView.as_view()
