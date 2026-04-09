# content/serializers/writing.py
#
# Complete rewrite against the new three-tier writing models.
# These serializers serve the REST API only.
# The Django web views use model querysets directly.
#
# Models covered:
#   WritingAcademicYear
#   WritingStage
#   WritingStageContent
#   WritingAttempt
#   WritingStageMastery
#   WritingIntervention

from rest_framework import serializers
from django.utils import timezone

from content.models.writing import (
    WritingAcademicYear,
    WritingStage,
    WritingStageContent,
    WritingAttempt,
    WritingStageMastery,
    WritingIntervention,
    PHASE_DISSECT,
    PHASE_IMITATE,
    PHASE_PRODUCE,
    EVAL_AUTOMATIC,
    EVAL_KEYWORD,
    EVAL_TEACHER,
    EVAL_AI_TEACHER,
    STATUS_PENDING,
    STATUS_PASSED,
    STATUS_FAILED,
    STATUS_COOLDOWN,
    STATUS_APPROVED,
    STATUS_REVISION,
    TIER_SENTENCE,
    TIER_PARAGRAPH,
    TIER_GENRE,
)
from content.models.core import Unit


# ============================================================
# 1. ACADEMIC YEAR SERIALIZERS
# ============================================================

class WritingAcademicYearSerializer(serializers.ModelSerializer):
    """
    Full serializer for WritingAcademicYear.
    Used by admin API and system configuration endpoints.
    """
    class Meta:
        model  = WritingAcademicYear
        fields = [
            "id",
            "label",
            "start_date",
            "is_current",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """
        Warn if trying to create a current year when one already exists.
        The model handles enforcement — this provides a clear API error.
        """
        if data.get("is_current"):
            existing = WritingAcademicYear.objects.filter(
                is_current=True
            ).exclude(
                pk=self.instance.pk if self.instance else None
            ).first()
            if existing:
                # Not an error — model will unset the old one.
                # Just pass through.
                pass
        return data


class WritingAcademicYearListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for academic year listings."""
    class Meta:
        model  = WritingAcademicYear
        fields = ["id", "label", "start_date", "is_current"]


# ============================================================
# 2. WRITING STAGE SERIALIZERS
# ============================================================

class WritingStageSerializer(serializers.ModelSerializer):
    """
    Full serializer for WritingStage.
    Includes min word counts per class level.
    Read-only — stages are seeded via migration, not created via API.
    """
    tier_display        = serializers.CharField(
        source="get_tier_display", read_only=True
    )
    eval_method_display = serializers.CharField(
        source="get_eval_method_display", read_only=True
    )
    unlocks_after_number = serializers.SerializerMethodField()

    class Meta:
        model  = WritingStage
        fields = [
            "id",
            "number",
            "name",
            "tier",
            "tier_display",
            "eval_method",
            "eval_method_display",
            "description",
            "min_words_class_9",
            "min_words_class_10",
            "min_words_class_11",
            "min_words_class_12",
            "unlocks_after_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_unlocks_after_number(self, obj):
        """Return the stage number that must be mastered before this one."""
        previous = obj.unlocks_after()
        return previous.number if previous else None


class WritingStageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for stage listings."""
    tier_display        = serializers.CharField(
        source="get_tier_display", read_only=True
    )
    eval_method_display = serializers.CharField(
        source="get_eval_method_display", read_only=True
    )

    class Meta:
        model  = WritingStage
        fields = [
            "id",
            "number",
            "name",
            "tier",
            "tier_display",
            "eval_method",
            "eval_method_display",
        ]


# ============================================================
# 3. WRITING STAGE CONTENT SERIALIZERS
# ============================================================

class WritingStageContentSerializer(serializers.ModelSerializer):
    """
    Full serializer for WritingStageContent.
    Used for content management endpoints.
    Includes all three phase fields.
    """
    stage_number        = serializers.IntegerField(
        source="stage.number", read_only=True
    )
    stage_name          = serializers.CharField(
        source="stage.name", read_only=True
    )
    stage_tier          = serializers.CharField(
        source="stage.tier", read_only=True
    )
    eval_method         = serializers.CharField(
        source="stage.eval_method", read_only=True
    )
    unit_title          = serializers.CharField(
        source="unit.title", read_only=True
    )
    class_level         = serializers.CharField(
        source="unit.textbook.class_level", read_only=True
    )
    effective_min_words = serializers.SerializerMethodField()
    required_keywords_list = serializers.SerializerMethodField()

    class Meta:
        model  = WritingStageContent
        fields = [
            "id",
            "stage",
            "stage_number",
            "stage_name",
            "stage_tier",
            "eval_method",
            "unit",
            "unit_title",
            "class_level",

            # Dissect phase
            "model_sentence_original",
            "model_sentence_converted",
            "conversion_note",
            "dissect_question",
            "dissect_answer",

            # Imitate phase
            "imitate_frame",
            "imitate_instruction",

            # Produce phase
            "produce_prompt",
            "produce_instruction",
            "min_word_count",
            "effective_min_words",

            # Evaluation
            "required_keywords",
            "required_keywords_list",
            "ai_rubric",

            # Status
            "is_complete",

            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "stage_number",
            "stage_name",
            "stage_tier",
            "eval_method",
            "unit_title",
            "class_level",
            "effective_min_words",
            "required_keywords_list",
            "created_at",
            "updated_at",
        ]

    def get_effective_min_words(self, obj):
        """Return the effective minimum word count for this content."""
        return obj.get_min_words()

    def get_required_keywords_list(self, obj):
        """Return required keywords as a clean list."""
        return obj.get_required_keywords_list()


class WritingStageContentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for stage content listings.
    Used in hub/journey views.
    """
    stage_number = serializers.IntegerField(
        source="stage.number", read_only=True
    )
    stage_name   = serializers.CharField(
        source="stage.name", read_only=True
    )
    stage_tier   = serializers.CharField(
        source="stage.tier", read_only=True
    )
    eval_method  = serializers.CharField(
        source="stage.eval_method", read_only=True
    )
    class_level  = serializers.CharField(
        source="unit.textbook.class_level", read_only=True
    )

    class Meta:
        model  = WritingStageContent
        fields = [
            "id",
            "stage",
            "stage_number",
            "stage_name",
            "stage_tier",
            "eval_method",
            "unit",
            "class_level",
            "is_complete",
        ]


class WritingStageContentStudentSerializer(serializers.ModelSerializer):
    """
    Student-facing serializer for WritingStageContent.
    Excludes dissect_answer and ai_rubric — these are internal.
    Includes only what the student needs to see.
    """
    stage_number        = serializers.IntegerField(
        source="stage.number", read_only=True
    )
    stage_name          = serializers.CharField(
        source="stage.name", read_only=True
    )
    stage_tier          = serializers.CharField(
        source="stage.tier", read_only=True
    )
    eval_method         = serializers.CharField(
        source="stage.eval_method", read_only=True
    )
    unit_title          = serializers.CharField(
        source="unit.title", read_only=True
    )
    class_level         = serializers.CharField(
        source="unit.textbook.class_level", read_only=True
    )
    effective_min_words    = serializers.SerializerMethodField()
    required_keywords_list = serializers.SerializerMethodField()

    class Meta:
        model  = WritingStageContent
        fields = [
            "id",
            "stage_number",
            "stage_name",
            "stage_tier",
            "eval_method",
            "unit_title",
            "class_level",

            # Dissect — no answer exposed
            "model_sentence_original",
            "model_sentence_converted",
            "conversion_note",
            "dissect_question",

            # Imitate
            "imitate_frame",
            "imitate_instruction",

            # Produce
            "produce_prompt",
            "produce_instruction",
            "effective_min_words",
            "required_keywords_list",
        ]
        read_only_fields = fields

    def get_effective_min_words(self, obj):
        return obj.get_min_words()

    def get_required_keywords_list(self, obj):
        return obj.get_required_keywords_list()


# ============================================================
# 4. WRITING ATTEMPT SERIALIZERS
# ============================================================

class WritingAttemptSerializer(serializers.ModelSerializer):
    """
    Full serializer for WritingAttempt.
    Used for teacher review and admin API endpoints.
    Includes all evaluation fields.
    """
    phase_display   = serializers.CharField(
        source="get_phase_display", read_only=True
    )
    status_display  = serializers.CharField(
        source="get_status_display", read_only=True
    )
    stage_number    = serializers.IntegerField(
        source="content.stage.number", read_only=True
    )
    stage_name      = serializers.CharField(
        source="content.stage.name", read_only=True
    )
    unit_title      = serializers.CharField(
        source="content.unit.title", read_only=True
    )
    class_level     = serializers.CharField(
        source="content.unit.textbook.class_level", read_only=True
    )
    effective_score = serializers.SerializerMethodField()
    is_passed       = serializers.SerializerMethodField()
    is_in_cooldown  = serializers.SerializerMethodField()
    cooldown_remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model  = WritingAttempt
        fields = [
            "id",
            "user",
            "content",
            "academic_year",
            "stage_number",
            "stage_name",
            "unit_title",
            "class_level",

            "phase",
            "phase_display",
            "attempt_number",
            "response_text",

            "status",
            "status_display",
            "auto_checks",
            "intervention_flags",
            "auto_score",
            "ai_score",
            "ai_feedback",
            "ai_rubric_scores",
            "teacher_score",
            "teacher_feedback",
            "reviewed_by",
            "reviewed_at",

            "effective_score",
            "is_passed",

            "cooldown_task",
            "next_attempt_allowed_at",
            "is_in_cooldown",
            "cooldown_remaining_seconds",

            "time_spent_seconds",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "content",
            "academic_year",
            "stage_number",
            "stage_name",
            "unit_title",
            "class_level",
            "phase",
            "phase_display",
            "attempt_number",
            "response_text",
            "status_display",
            "auto_checks",
            "intervention_flags",
            "auto_score",
            "ai_score",
            "ai_feedback",
            "ai_rubric_scores",
            "reviewed_by",
            "reviewed_at",
            "effective_score",
            "is_passed",
            "cooldown_task",
            "next_attempt_allowed_at",
            "is_in_cooldown",
            "cooldown_remaining_seconds",
            "time_spent_seconds",
            "created_at",
            "updated_at",
        ]

    def get_effective_score(self, obj):
        return obj.effective_score()

    def get_is_passed(self, obj):
        return obj.is_passed()

    def get_is_in_cooldown(self, obj):
        return obj.is_in_cooldown()

    def get_cooldown_remaining_seconds(self, obj):
        remaining = obj.cooldown_remaining()
        if remaining:
            return int(remaining.total_seconds())
        return None


class WritingAttemptStudentSerializer(serializers.ModelSerializer):
    """
    Student-facing serializer for WritingAttempt.
    Excludes internal fields like auto_checks details
    that students do not need to see raw.
    Shows feedback and scores clearly.
    """
    phase_display   = serializers.CharField(
        source="get_phase_display", read_only=True
    )
    status_display  = serializers.CharField(
        source="get_status_display", read_only=True
    )
    effective_score = serializers.SerializerMethodField()
    is_passed       = serializers.SerializerMethodField()
    is_in_cooldown  = serializers.SerializerMethodField()
    cooldown_remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model  = WritingAttempt
        fields = [
            "id",
            "phase",
            "phase_display",
            "attempt_number",
            "response_text",
            "status",
            "status_display",
            "effective_score",
            "is_passed",
            "ai_feedback",
            "teacher_feedback",
            "cooldown_task",
            "next_attempt_allowed_at",
            "is_in_cooldown",
            "cooldown_remaining_seconds",
            "created_at",
        ]
        read_only_fields = fields

    def get_effective_score(self, obj):
        return obj.effective_score()

    def get_is_passed(self, obj):
        return obj.is_passed()

    def get_is_in_cooldown(self, obj):
        return obj.is_in_cooldown()

    def get_cooldown_remaining_seconds(self, obj):
        remaining = obj.cooldown_remaining()
        if remaining:
            return int(remaining.total_seconds())
        return None


class WritingAttemptSubmitSerializer(serializers.Serializer):
    """
    Serializer for submitting a writing attempt via the API.
    Validates the submission before the view processes it.

    Required fields:
        content_id      — WritingStageContent pk
        phase           — dissect / imitate / produce
        response_text   — the student's written response

    Optional fields:
        time_spent_seconds
    """
    content_id         = serializers.IntegerField()
    phase              = serializers.ChoiceField(
        choices=[PHASE_DISSECT, PHASE_IMITATE, PHASE_PRODUCE]
    )
    response_text      = serializers.CharField()
    time_spent_seconds = serializers.IntegerField(
        min_value=0, required=False, allow_null=True
    )

    def validate_content_id(self, value):
        """Validate the content exists and is complete."""
        try:
            content = WritingStageContent.objects.get(pk=value, is_complete=True)
        except WritingStageContent.DoesNotExist:
            raise serializers.ValidationError(
                "Writing stage content not found or not yet available."
            )
        return value

    def validate_response_text(self, value):
        """Validate response is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Response text cannot be empty."
            )
        return value.strip()

    def validate(self, data):
        """
        Cross-field validation.
        Check cooldown if phase is Produce.
        """
        request = self.context.get("request")
        if not request:
            return data

        content_id = data.get("content_id")
        phase      = data.get("phase")

        if phase == PHASE_PRODUCE and content_id:
            try:
                from content.models.writing import WritingAcademicYear
                from content.views.writing.core import get_cooldown_info
                content      = WritingStageContent.objects.get(pk=content_id)
                academic_year = WritingAcademicYear.get_current()
                if academic_year:
                    cooldown = get_cooldown_info(
                        request.user, content, academic_year
                    )
                    if cooldown["is_in_cooldown"]:
                        raise serializers.ValidationError(
                            "You must wait before attempting Produce again. "
                            "Complete your focus tasks first."
                        )
            except WritingStageContent.DoesNotExist:
                pass

        return data


class WritingAttemptListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for attempt listings.
    Used in progress and history endpoints.
    """
    phase_display  = serializers.CharField(
        source="get_phase_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    stage_number   = serializers.IntegerField(
        source="content.stage.number", read_only=True
    )
    stage_name     = serializers.CharField(
        source="content.stage.name", read_only=True
    )
    effective_score = serializers.SerializerMethodField()

    class Meta:
        model  = WritingAttempt
        fields = [
            "id",
            "stage_number",
            "stage_name",
            "phase",
            "phase_display",
            "attempt_number",
            "status",
            "status_display",
            "effective_score",
            "created_at",
        ]
        read_only_fields = fields

    def get_effective_score(self, obj):
        return obj.effective_score()


# ============================================================
# 5. WRITING STAGE MASTERY SERIALIZERS
# ============================================================

class WritingStageMasterySerializer(serializers.ModelSerializer):
    """
    Full serializer for WritingStageMastery.
    Read-only — mastery is granted by the system, not via API.
    """
    stage_number        = serializers.IntegerField(
        source="content.stage.number", read_only=True
    )
    stage_name          = serializers.CharField(
        source="content.stage.name", read_only=True
    )
    stage_tier          = serializers.CharField(
        source="content.stage.tier", read_only=True
    )
    unit_title          = serializers.CharField(
        source="content.unit.title", read_only=True
    )
    class_level         = serializers.CharField(
        source="content.unit.textbook.class_level", read_only=True
    )
    mastered_via_display = serializers.SerializerMethodField()
    academic_year_label  = serializers.CharField(
        source="academic_year.label", read_only=True
    )

    class Meta:
        model  = WritingStageMastery
        fields = [
            "id",
            "user",
            "content",
            "stage_number",
            "stage_name",
            "stage_tier",
            "unit_title",
            "class_level",
            "academic_year",
            "academic_year_label",
            "mastered_at",
            "mastered_via",
            "mastered_via_display",
            "mastery_attempt",
            "created_at",
        ]
        read_only_fields = fields

    def get_mastered_via_display(self, obj):
        return obj.get_mastered_via_display()


class WritingStageMasteryListSerializer(serializers.ModelSerializer):
    """Lightweight mastery serializer for listings."""
    stage_number = serializers.IntegerField(
        source="content.stage.number", read_only=True
    )
    stage_name   = serializers.CharField(
        source="content.stage.name", read_only=True
    )
    academic_year_label = serializers.CharField(
        source="academic_year.label", read_only=True
    )

    class Meta:
        model  = WritingStageMastery
        fields = [
            "id",
            "stage_number",
            "stage_name",
            "academic_year_label",
            "mastered_at",
            "mastered_via",
        ]
        read_only_fields = fields


# ============================================================
# 6. WRITING INTERVENTION SERIALIZERS
# ============================================================

class WritingInterventionSerializer(serializers.ModelSerializer):
    """
    Full serializer for WritingIntervention.
    Used by student-facing API to show fix exercises.
    """
    class Meta:
        model  = WritingIntervention
        fields = [
            "id",
            "attempt",
            "sentence_text",
            "issue_label",
            "fix_exercise",
            "student_fix",
            "is_resolved",
            "created_at",
            "resolved_at",
        ]
        read_only_fields = [
            "id",
            "attempt",
            "sentence_text",
            "issue_label",
            "fix_exercise",
            "is_resolved",
            "created_at",
            "resolved_at",
        ]


class WritingInterventionFixSerializer(serializers.Serializer):
    """
    Serializer for submitting a fix for a sentence intervention.
    The student rewrites the problematic sentence.
    """
    fix_text = serializers.CharField()

    def validate_fix_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Please write your fix before submitting."
            )
        return value.strip()


# ============================================================
# 7. PROGRESS SERIALIZERS
# ============================================================

class WritingStageProgressSerializer(serializers.Serializer):
    """
    Progress for a single stage — used in hub/journey API.
    Combines content, status, and attempt data.
    """
    content_id      = serializers.IntegerField()
    stage_number    = serializers.IntegerField()
    stage_name      = serializers.CharField()
    stage_tier      = serializers.CharField()
    eval_method     = serializers.CharField()
    status          = serializers.ChoiceField(
        choices=["locked", "available", "in_progress", "mastered"]
    )
    current_phase   = serializers.CharField(allow_null=True)
    is_in_cooldown  = serializers.BooleanField()
    cooldown_ends_at = serializers.DateTimeField(allow_null=True)


class WritingTierProgressSerializer(serializers.Serializer):
    """Progress summary for a single tier."""
    tier        = serializers.CharField()
    tier_label  = serializers.CharField()
    total       = serializers.IntegerField()
    mastered    = serializers.IntegerField()
    percent     = serializers.IntegerField()
    stages      = WritingStageProgressSerializer(many=True)


class WritingJourneySerializer(serializers.Serializer):
    """
    Complete writing journey for a student in a unit.
    Used by the hub API endpoint.
    Mirrors what the hub view passes to the template.
    """
    unit_id          = serializers.IntegerField()
    unit_title       = serializers.CharField()
    class_level      = serializers.CharField()
    academic_year_id = serializers.IntegerField(allow_null=True)
    academic_year_label = serializers.CharField(allow_null=True)

    overall_percent  = serializers.IntegerField()
    total_stages     = serializers.IntegerField()
    mastered_stages  = serializers.IntegerField()

    tiers = serializers.DictField(
        child=WritingTierProgressSerializer()
    )

    no_academic_year = serializers.BooleanField()


class WritingProgressSummarySerializer(serializers.Serializer):
    """
    Summary of writing progress across all units
    for a given student and academic year.
    """
    academic_year_label  = serializers.CharField()
    total_stages_available = serializers.IntegerField()
    total_stages_mastered  = serializers.IntegerField()
    overall_percent        = serializers.IntegerField()

    # By tier
    sentence_total    = serializers.IntegerField()
    sentence_mastered = serializers.IntegerField()
    paragraph_total   = serializers.IntegerField()
    paragraph_mastered = serializers.IntegerField()
    genre_total       = serializers.IntegerField()
    genre_mastered    = serializers.IntegerField()

    # Attempts
    total_attempts          = serializers.IntegerField()
    dissect_attempts        = serializers.IntegerField()
    imitate_attempts        = serializers.IntegerField()
    produce_attempts        = serializers.IntegerField()
    pending_teacher_review  = serializers.IntegerField()

    # Recent activity
    recent_attempts = WritingAttemptListSerializer(many=True)
    recent_masteries = WritingStageMasteryListSerializer(many=True)


# ============================================================
# 8. MOBILE-OPTIMIZED SERIALIZERS
# ============================================================

class WritingStageContentMobileSerializer(serializers.ModelSerializer):
    """
    Lightweight content serializer for mobile.
    Strips heavy fields not needed on first load.
    Full content loaded on demand.
    """
    stage_number = serializers.IntegerField(
        source="stage.number", read_only=True
    )
    stage_name   = serializers.CharField(
        source="stage.name", read_only=True
    )
    eval_method  = serializers.CharField(
        source="stage.eval_method", read_only=True
    )

    class Meta:
        model  = WritingStageContent
        fields = [
            "id",
            "stage_number",
            "stage_name",
            "eval_method",
            "produce_prompt",
            "is_complete",
        ]
        read_only_fields = fields


class WritingAttemptMobileSerializer(serializers.ModelSerializer):
    """
    Mobile-optimized attempt serializer.
    Minimal fields for bandwidth efficiency.
    """
    effective_score = serializers.SerializerMethodField()
    is_passed       = serializers.SerializerMethodField()

    class Meta:
        model  = WritingAttempt
        fields = [
            "id",
            "content",
            "phase",
            "attempt_number",
            "status",
            "effective_score",
            "is_passed",
            "ai_feedback",
            "teacher_feedback",
            "cooldown_task",
            "next_attempt_allowed_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_effective_score(self, obj):
        return obj.effective_score()

    def get_is_passed(self, obj):
        return obj.is_passed()


class WritingStageMasteryMobileSerializer(serializers.ModelSerializer):
    """Mobile-optimized mastery serializer."""
    stage_number = serializers.IntegerField(
        source="content.stage.number", read_only=True
    )

    class Meta:
        model  = WritingStageMastery
        fields = [
            "id",
            "stage_number",
            "mastered_at",
            "mastered_via",
        ]
        read_only_fields = fields