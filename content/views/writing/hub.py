# content/views/writing/hub.py
#
# The writing module home page for students.
# Renders the staircase journey — all stages for a unit,
# with status, current phase, and cooldown information.
#
# URL pattern expected:
#   writing/unit/<unit_id>/                → WritingHubView
#
# What this view does:
#   1. Validates the student has access to this unit
#   2. Gets or warns about current academic year
#   3. Builds the full stage status list for the staircase
#   4. Separates stages into tiers for visual grouping
#   5. Calculates overall tier progress for the progress bar

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.http import Http404

from content.models.core import Unit
from content.models.writing import (
    WritingStageContent,
    WritingStageMastery,
    WritingAttempt,
    TIER_SENTENCE,
    TIER_PARAGRAPH,
    TIER_GENRE,
)
from .core import (
    get_current_academic_year,
    get_all_stage_statuses,
)


class WritingHubView(LoginRequiredMixin, TemplateView):
    template_name = "content/writing/hub.html"

    def get(self, request, unit_id, *args, **kwargs):
        self.unit         = get_object_or_404(Unit, pk=unit_id)
        self.academic_year = get_current_academic_year()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user    = self.request.user
        unit    = self.unit
        year    = self.academic_year

        # ── Stage statuses ────────────────────────────────
        if year:
            all_stages = get_all_stage_statuses(user, unit, year)
        else:
            # No academic year set — show all stages as locked
            # with a warning. Admin must set academic year.
            all_stages = self._build_locked_stages(unit)

        # ── Separate into tiers ───────────────────────────
        tiers = {
            TIER_SENTENCE:  [],
            TIER_PARAGRAPH: [],
            TIER_GENRE:     [],
        }
        for stage_data in all_stages:
            tier = stage_data["stage"].tier
            if tier in tiers:
                tiers[tier].append(stage_data)

        # ── Tier progress ─────────────────────────────────
        tier_progress = {}
        for tier_key, stages in tiers.items():
            if not stages:
                tier_progress[tier_key] = {
                    "total":    0,
                    "mastered": 0,
                    "percent":  0,
                }
                continue
            total    = len(stages)
            mastered = sum(
                1 for s in stages
                if s["status"] == "mastered"
            )
            tier_progress[tier_key] = {
                "total":    total,
                "mastered": mastered,
                "percent":  int((mastered / total) * 100)
                            if total else 0,
            }

        # ── Overall progress ──────────────────────────────
        total_stages    = len(all_stages)
        mastered_stages = sum(
            1 for s in all_stages
            if s["status"] == "mastered"
        )
        overall_percent = (
            int((mastered_stages / total_stages) * 100)
            if total_stages else 0
        )

        # ── Find the active stage ─────────────────────────
        # The first stage that is available or in_progress
        active_stage = next(
            (
                s for s in all_stages
                if s["status"] in ("available", "in_progress")
            ),
            None,
        )

        # ── Class level display ───────────────────────────
        class_level = unit.textbook.class_level

        context.update({
            # Core data
            "unit":          unit,
            "academic_year": year,
            "class_level":   class_level,

            # Stage data
            "all_stages":    all_stages,
            "tiers":         tiers,
            "active_stage":  active_stage,

            # Tier labels for template
            "tier_sentence":  TIER_SENTENCE,
            "tier_paragraph": TIER_PARAGRAPH,
            "tier_genre":     TIER_GENRE,

            # Tier display names
            "tier_labels": {
                TIER_SENTENCE:  "Tier 1 — Sentence",
                TIER_PARAGRAPH: "Tier 2 — Paragraph",
                TIER_GENRE:     "Tier 3 — Genre",
            },
            "tier_descriptions": {
                TIER_SENTENCE: (
                    "Build the unit of thought. "
                    "Learn to write every type of sentence correctly."
                ),
                TIER_PARAGRAPH: (
                    "Build the unit of communication. "
                    "Learn to organise sentences into a clear paragraph."
                ),
                TIER_GENRE: (
                    "Build the unit of purpose. "
                    "Learn to write for real goals — "
                    "essays, summaries, and more."
                ),
            },

            # Progress
            "tier_progress":    tier_progress,
            "total_stages":     total_stages,
            "mastered_stages":  mastered_stages,
            "overall_percent":  overall_percent,

            # Warning flag
            "no_academic_year": year is None,
        })

        return context

    def _build_locked_stages(self, unit):
        """
        Fallback when no academic year is set.
        Returns all stage data with status locked
        so the template renders without errors.
        """
        contents = (
            WritingStageContent.objects
            .filter(unit=unit, is_complete=True)
            .select_related("stage")
            .order_by("stage__number")
        )
        return [
            {
                "content":          content,
                "stage":            content.stage,
                "status":           "locked",
                "current_phase":    None,
                "is_in_cooldown":   False,
                "cooldown_ends_at": None,
            }
            for content in contents
        ]