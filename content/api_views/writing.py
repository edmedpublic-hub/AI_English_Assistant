# content/api_views/writing.py
#
# Complete rewrite for the new three-tier writing architecture.
# Provides REST API endpoints for:
#   WritingAcademicYear  — system configuration
#   WritingStage         — read-only stage definitions
#   WritingStageContent  — content per stage per unit
#   WritingAttempt       — student submissions (all phases)
#   WritingStageMastery  — mastery records (read-only)
#   WritingIntervention  — sentence-level fix exercises
#   WritingProgress      — student progress and journey

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction
from django.db.models import Q, Count, Avg, Max, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404

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

from content.serializers.writing import (
    WritingAcademicYearSerializer,
    WritingAcademicYearListSerializer,
    WritingStageSerializer,
    WritingStageListSerializer,
    WritingStageContentSerializer,
    WritingStageContentListSerializer,
    WritingStageContentStudentSerializer,
    WritingAttemptSerializer,
    WritingAttemptStudentSerializer,
    WritingAttemptSubmitSerializer,
    WritingAttemptListSerializer,
    WritingStageMasterySerializer,
    WritingStageMasteryListSerializer,
    WritingInterventionSerializer,
    WritingInterventionFixSerializer,
    WritingStageProgressSerializer,
    WritingJourneySerializer,
    WritingProgressSummarySerializer,
)

from content.views.writing.core import (
    get_current_academic_year,
    get_all_stage_statuses,
    get_stage_status,
    get_cooldown_info,
    get_next_attempt_number,
    evaluate_automatic,
    detect_sentence_interventions,
    generate_cooldown_task,
    grant_mastery,
    evaluate_with_ai,
    COOLDOWN_HOURS,
)

from .base import BaseViewSet, ProgressViewSet, UserFilterMixin, log_user_activity


# ============================================================
# 1. ACADEMIC YEAR VIEWSET
# ============================================================

class WritingAcademicYearViewSet(viewsets.ModelViewSet):
    """
    Academic year configuration.
    Admin sets the current year once per year.
    Read access for all authenticated users.
    Write access for admin only.
    """

    queryset           = WritingAcademicYear.objects.all()
    serializer_class   = WritingAcademicYearSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return WritingAcademicYearListSerializer
        return WritingAcademicYearSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Return the current academic year."""
        year = WritingAcademicYear.get_current()
        if not year:
            return Response(
                {'detail': 'No current academic year set.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(WritingAcademicYearSerializer(year).data)


# ============================================================
# 2. WRITING STAGE VIEWSET
# ============================================================

class WritingStageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    The 16 writing stages.
    Read-only — stages are seeded via migration.
    """

    queryset           = WritingStage.objects.all().order_by('number')
    serializer_class   = WritingStageSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return WritingStageListSerializer
        return WritingStageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tier = self.request.query_params.get('tier')
        if tier:
            qs = qs.filter(tier=tier)
        eval_method = self.request.query_params.get('eval_method')
        if eval_method:
            qs = qs.filter(eval_method=eval_method)
        return qs

    @action(detail=False, methods=['get'])
    def by_tier(self, request):
        """Return stages grouped by tier."""
        result = {}
        for tier in (TIER_SENTENCE, TIER_PARAGRAPH, TIER_GENRE):
            stages = WritingStage.objects.filter(
                tier=tier
            ).order_by('number')
            result[tier] = WritingStageListSerializer(stages, many=True).data
        return Response(result)


# ============================================================
# 3. WRITING STAGE CONTENT VIEWSET
# ============================================================

class WritingStageContentViewSet(BaseViewSet):
    """
    Stage content — what admin enters per stage per unit.
    GET endpoints serve student-facing content (answer hidden).
    Admin writes content via the Django admin.
    """

    queryset           = WritingStageContent.objects.filter(
        is_complete=True
    ).select_related('stage', 'unit__textbook')
    serializer_class   = WritingStageContentStudentSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Admin users see full content including dissect_answer
        if self.request.user and self.request.user.is_staff:
            return WritingStageContentSerializer
        return WritingStageContentStudentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            qs = qs.filter(unit_id=unit_id)
        stage_id = self.request.query_params.get('stage_id')
        if stage_id:
            qs = qs.filter(stage_id=stage_id)
        tier = self.request.query_params.get('tier')
        if tier:
            qs = qs.filter(stage__tier=tier)
        return qs.order_by('stage__number')

    @action(detail=False, methods=['get'])
    def hub(self, request, unit_id=None):
        """
        Return the complete writing journey for a student in a unit.
        Used by the writing hub page.
        Mirrors what the hub view passes to the template.
        """
        if not unit_id:
            unit_id = request.query_params.get('unit_id')
        if not unit_id:
            return Response(
                {'detail': 'unit_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unit = get_object_or_404(Unit, pk=unit_id)
        year = get_current_academic_year()

        if not year:
            return Response(
                {'detail': 'No current academic year set.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        all_stages = get_all_stage_statuses(request.user, unit, year)

        tiers = {
            TIER_SENTENCE:  [],
            TIER_PARAGRAPH: [],
            TIER_GENRE:     [],
        }
        for s in all_stages:
            tier = s['stage'].tier
            if tier in tiers:
                tiers[tier].append({
                    'content_id':    s['content'].id,
                    'stage_number':  s['stage'].number,
                    'stage_name':    s['stage'].name,
                    'stage_tier':    s['stage'].tier,
                    'eval_method':   s['stage'].eval_method,
                    'status':        s['status'],
                    'current_phase': s['current_phase'],
                    'is_in_cooldown': s['is_in_cooldown'],
                    'cooldown_ends_at': (
                        s['cooldown_ends_at'].isoformat()
                        if s['cooldown_ends_at'] else None
                    ),
                })

        tier_progress = {}
        for tier_key, stages in tiers.items():
            total    = len(stages)
            mastered = sum(1 for s in stages if s['status'] == 'mastered')
            tier_progress[tier_key] = {
                'total':    total,
                'mastered': mastered,
                'percent':  int((mastered / total) * 100) if total else 0,
                'stages':   stages,
            }

        total_stages    = len(all_stages)
        mastered_stages = sum(
            1 for s in all_stages if s['status'] == 'mastered'
        )

        return Response({
            'unit_id':              unit.id,
            'unit_title':           unit.title,
            'class_level':          unit.textbook.class_level,
            'academic_year_id':     year.id,
            'academic_year_label':  year.label,
            'overall_percent':      int((mastered_stages / total_stages) * 100) if total_stages else 0,
            'total_stages':         total_stages,
            'mastered_stages':      mastered_stages,
            'tiers':                tier_progress,
            'no_academic_year':     False,
        })


# ============================================================
# 4. WRITING ATTEMPT VIEWSET
# ============================================================

class WritingAttemptViewSet(BaseViewSet, UserFilterMixin):
    """
    Student writing submissions.

    Key endpoints:
    - POST /submit/         — submit a Dissect, Imitate, or Produce response
    - GET  /                — list user's attempt history
    - GET  /<pk>/           — retrieve a specific attempt
    - GET  /pending_review/ — teacher endpoint: list pending Produce submissions
    """

    queryset           = WritingAttempt.objects.all()
    serializer_class   = WritingAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'submit':
            return WritingAttemptSubmitSerializer
        if self.action == 'list':
            return WritingAttemptListSerializer
        if self.request.user and not self.request.user.is_staff:
            return WritingAttemptStudentSerializer
        return WritingAttemptSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Non-staff users only see their own attempts
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)

        content_id = self.request.query_params.get('content_id')
        if content_id:
            qs = qs.filter(content_id=content_id)

        phase = self.request.query_params.get('phase')
        if phase:
            qs = qs.filter(phase=phase)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs.select_related(
            'content__stage', 'content__unit', 'academic_year'
        ).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def submit(self, request):
        """
        Submit a writing attempt.
        Routes to the correct evaluator based on stage eval_method.
        Enforces cooldown on Produce phase.
        Creates mastery record on automatic/keyword pass.
        """
        serializer = WritingAttemptSubmitSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        content_id    = serializer.validated_data['content_id']
        phase         = serializer.validated_data['phase']
        response_text = serializer.validated_data['response_text']
        time_spent    = serializer.validated_data.get('time_spent_seconds')

        content       = get_object_or_404(
            WritingStageContent, pk=content_id, is_complete=True
        )
        academic_year = get_current_academic_year()

        if not academic_year:
            return Response(
                {'detail': 'Writing is not available right now.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Check stage is not locked
        stage_status = get_stage_status(request.user, content, academic_year)
        if stage_status == 'locked':
            return Response(
                {'detail': 'This stage is not yet available.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check cooldown for Produce
        if phase == PHASE_PRODUCE:
            cooldown = get_cooldown_info(request.user, content, academic_year)
            if cooldown['is_in_cooldown']:
                remaining = None
                latest = WritingAttempt.objects.filter(
                    user=request.user,
                    content=content,
                    academic_year=academic_year,
                    phase=PHASE_PRODUCE,
                ).order_by('-created_at').first()
                if latest:
                    r = latest.cooldown_remaining()
                    if r:
                        remaining = int(r.total_seconds())
                return Response(
                    {
                        'detail': 'You must wait before trying again.',
                        'cooldown_remaining_seconds': remaining,
                        'next_attempt_allowed_at': cooldown['ends_at'],
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        attempt_number = get_next_attempt_number(
            request.user, content, academic_year, phase
        )

        eval_method = content.stage.eval_method

        # ── Route to evaluator ────────────────────────────

        if eval_method in (EVAL_AUTOMATIC, EVAL_KEYWORD):
            return self._handle_automatic(
                request, content, academic_year,
                phase, response_text, time_spent, attempt_number,
            )

        elif eval_method == EVAL_TEACHER:
            return self._handle_teacher(
                request, content, academic_year,
                phase, response_text, time_spent, attempt_number,
            )

        elif eval_method == EVAL_AI_TEACHER:
            return self._handle_ai_teacher(
                request, content, academic_year,
                phase, response_text, time_spent, attempt_number,
            )

        return Response(
            {'detail': 'Unknown evaluation method.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _handle_automatic(
        self, request, content, academic_year,
        phase, response_text, time_spent, attempt_number,
    ):
        evaluation        = evaluate_automatic(response_text, content, phase)
        interventions_data = []
        if content.stage.number >= 6:
            interventions_data = detect_sentence_interventions(
                response_text, content.stage.number
            )

        has_interventions = len(interventions_data) > 0
        passed            = evaluation['passed'] and not has_interventions

        attempt = WritingAttempt.objects.create(
            user               = request.user,
            content            = content,
            academic_year      = academic_year,
            phase              = phase,
            attempt_number     = attempt_number,
            response_text      = response_text,
            status             = STATUS_PASSED if passed else STATUS_FAILED,
            auto_score         = evaluation['score'],
            auto_checks        = evaluation['checks'],
            intervention_flags = interventions_data,
            time_spent_seconds = time_spent,
        )

        for iv in interventions_data:
            WritingIntervention.objects.create(
                attempt       = attempt,
                sentence_text = iv['sentence'],
                issue_label   = iv['issue'],
                fix_exercise  = iv['fix_exercise'],
            )

        if passed and phase == PHASE_PRODUCE:
            grant_mastery(request.user, content, academic_year, attempt)
        elif not passed and phase == PHASE_PRODUCE:
            cooldown_task = generate_cooldown_task(evaluation, content)
            attempt.set_cooldown(hours=COOLDOWN_HOURS)
            attempt.cooldown_task = cooldown_task
            attempt.save()

        log_user_activity(
            request.user, 'writing_attempt_submitted',
            {
                'content_id':    content.id,
                'phase':         phase,
                'passed':        passed,
                'eval_method':   'automatic',
            },
        )

        return Response(
            WritingAttemptStudentSerializer(attempt).data,
            status=status.HTTP_201_CREATED,
        )

    def _handle_teacher(
        self, request, content, academic_year,
        phase, response_text, time_spent, attempt_number,
    ):
        evaluation        = evaluate_automatic(response_text, content, phase)
        interventions_data = []
        if content.stage.number >= 6:
            interventions_data = detect_sentence_interventions(
                response_text, content.stage.number
            )

        attempt = WritingAttempt.objects.create(
            user               = request.user,
            content            = content,
            academic_year      = academic_year,
            phase              = phase,
            attempt_number     = attempt_number,
            response_text      = response_text,
            status             = STATUS_PENDING,
            auto_score         = evaluation['score'],
            auto_checks        = evaluation['checks'],
            intervention_flags = interventions_data,
            time_spent_seconds = time_spent,
        )

        for iv in interventions_data:
            WritingIntervention.objects.create(
                attempt       = attempt,
                sentence_text = iv['sentence'],
                issue_label   = iv['issue'],
                fix_exercise  = iv['fix_exercise'],
            )

        log_user_activity(
            request.user, 'writing_attempt_submitted',
            {'content_id': content.id, 'phase': phase, 'eval_method': 'teacher'},
        )

        return Response(
            WritingAttemptStudentSerializer(attempt).data,
            status=status.HTTP_201_CREATED,
        )

    def _handle_ai_teacher(
        self, request, content, academic_year,
        phase, response_text, time_spent, attempt_number,
    ):
        evaluation        = evaluate_automatic(response_text, content, phase)
        interventions_data = []
        if content.stage.number >= 6:
            interventions_data = detect_sentence_interventions(
                response_text, content.stage.number
            )

        ai_result = evaluate_with_ai(response_text, content)

        attempt = WritingAttempt.objects.create(
            user               = request.user,
            content            = content,
            academic_year      = academic_year,
            phase              = phase,
            attempt_number     = attempt_number,
            response_text      = response_text,
            status             = STATUS_PENDING,
            auto_score         = evaluation['score'],
            auto_checks        = evaluation['checks'],
            intervention_flags = interventions_data,
            ai_score           = ai_result['score'],
            ai_feedback        = ai_result['feedback'],
            ai_rubric_scores   = ai_result['rubric_scores'],
            time_spent_seconds = time_spent,
        )

        for iv in interventions_data:
            WritingIntervention.objects.create(
                attempt       = attempt,
                sentence_text = iv['sentence'],
                issue_label   = iv['issue'],
                fix_exercise  = iv['fix_exercise'],
            )

        log_user_activity(
            request.user, 'writing_attempt_submitted',
            {'content_id': content.id, 'phase': phase, 'eval_method': 'ai_teacher'},
        )

        return Response(
            WritingAttemptStudentSerializer(attempt).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['get'])
    def pending_review(self, request):
        """
        Teacher endpoint — list Produce submissions pending review.
        """
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        pending = WritingAttempt.objects.filter(
            phase=PHASE_PRODUCE,
            status=STATUS_PENDING,
            content__stage__eval_method__in=(EVAL_TEACHER, EVAL_AI_TEACHER),
        ).select_related(
            'user', 'content__stage', 'content__unit', 'academic_year'
        ).order_by('created_at')

        unit_id = request.query_params.get('unit_id')
        if unit_id:
            pending = pending.filter(content__unit_id=unit_id)

        return Response(
            WritingAttemptSerializer(pending, many=True).data
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Teacher approves a pending submission.
        Creates mastery record.
        """
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        attempt          = self.get_object()
        teacher_feedback = request.data.get('teacher_feedback', '')
        teacher_score    = request.data.get('teacher_score')

        attempt.status           = STATUS_APPROVED
        attempt.teacher_feedback = teacher_feedback
        attempt.reviewed_by      = request.user
        attempt.reviewed_at      = timezone.now()
        if teacher_score is not None:
            attempt.teacher_score = int(teacher_score)
        attempt.save()

        if attempt.phase == PHASE_PRODUCE:
            grant_mastery(
                attempt.user, attempt.content,
                attempt.academic_year, attempt
            )

        return Response(WritingAttemptSerializer(attempt).data)

    @action(detail=True, methods=['post'])
    def request_revision(self, request, pk=None):
        """
        Teacher requests revision on a pending submission.
        """
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        attempt          = self.get_object()
        teacher_feedback = request.data.get('teacher_feedback', '')

        attempt.status           = STATUS_REVISION
        attempt.teacher_feedback = teacher_feedback
        attempt.reviewed_by      = request.user
        attempt.reviewed_at      = timezone.now()
        attempt.save()

        return Response(WritingAttemptSerializer(attempt).data)


# ============================================================
# 5. WRITING STAGE MASTERY VIEWSET
# ============================================================

class WritingStageMasteryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Mastery records — read-only.
    Mastery is granted by the system, not via API.
    """

    queryset           = WritingStageMastery.objects.all()
    serializer_class   = WritingStageMasterySerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return WritingStageMasteryListSerializer
        return WritingStageMasterySerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Non-staff users only see their own mastery
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)

        year_id = self.request.query_params.get('academic_year_id')
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        else:
            year = get_current_academic_year()
            if year:
                qs = qs.filter(academic_year=year)

        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            qs = qs.filter(content__unit_id=unit_id)

        tier = self.request.query_params.get('tier')
        if tier:
            qs = qs.filter(content__stage__tier=tier)

        return qs.select_related(
            'content__stage', 'content__unit__textbook',
            'academic_year', 'user',
        ).order_by('-mastered_at')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Return mastery summary for the current user."""
        year = get_current_academic_year()
        qs   = self.get_queryset()

        by_tier = {}
        for tier in (TIER_SENTENCE, TIER_PARAGRAPH, TIER_GENRE):
            tier_total    = WritingStageContent.objects.filter(
                stage__tier=tier, is_complete=True
            ).count()
            tier_mastered = qs.filter(content__stage__tier=tier).count()
            by_tier[tier] = {
                'total':    tier_total,
                'mastered': tier_mastered,
                'percent':  int((tier_mastered / tier_total) * 100)
                            if tier_total else 0,
            }

        return Response({
            'academic_year':   year.label if year else None,
            'total_mastered':  qs.count(),
            'by_tier':         by_tier,
        })


# ============================================================
# 6. WRITING INTERVENTION VIEWSET
# ============================================================

class WritingInterventionViewSet(viewsets.GenericViewSet):
    """
    Sentence-level fix exercises.
    Students submit fixes here.
    """

    queryset           = WritingIntervention.objects.all()
    serializer_class   = WritingInterventionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        # Students only see their own interventions
        if not self.request.user.is_staff:
            qs = qs.filter(attempt__user=self.request.user)
        return qs

    @action(detail=True, methods=['post'])
    def fix(self, request, pk=None):
        """
        Submit a fix for a sentence-level intervention.
        Attempting the fix is enough — does not need to be perfect.
        """
        intervention = get_object_or_404(
            WritingIntervention,
            pk=pk,
            attempt__user=request.user,
        )

        if intervention.is_resolved:
            return Response(
                {'detail': 'This intervention is already resolved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WritingInterventionFixSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fix_text = serializer.validated_data['fix_text']
        intervention.resolve(fix_text)

        # Check if all interventions for this attempt are resolved
        attempt      = intervention.attempt
        all_resolved = not attempt.interventions.filter(
            is_resolved=False
        ).exists()

        return Response({
            'resolved':    True,
            'all_resolved': all_resolved,
            'feedback': (
                'All sentences fixed. You can now resubmit.'
                if all_resolved
                else 'Sentence fixed. Check the remaining highlighted sentences.'
            ),
        })

    def retrieve(self, request, pk=None):
        intervention = get_object_or_404(
            self.get_queryset(), pk=pk
        )
        return Response(
            WritingInterventionSerializer(intervention).data
        )


# ============================================================
# 7. WRITING PROGRESS VIEWSET
# ============================================================

class WritingProgressViewSet(ProgressViewSet):
    """
    Writing progress and analytics.
    """

    serializer_class   = WritingProgressSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_user_progress(self, user):
        year = get_current_academic_year()

        total_stages    = WritingStageContent.objects.filter(
            is_complete=True
        ).count()
        mastered_stages = (
            WritingStageMastery.objects.filter(
                user=user, academic_year=year
            ).count()
            if year else 0
        )

        by_tier = {}
        for tier in (TIER_SENTENCE, TIER_PARAGRAPH, TIER_GENRE):
            total    = WritingStageContent.objects.filter(
                stage__tier=tier, is_complete=True
            ).count()
            mastered = (
                WritingStageMastery.objects.filter(
                    user=user, academic_year=year,
                    content__stage__tier=tier,
                ).count()
                if year else 0
            )
            by_tier[tier] = {
                'total':    total,
                'mastered': mastered,
                'percent':  int((mastered / total) * 100) if total else 0,
            }

        total_attempts   = WritingAttempt.objects.filter(user=user).count()
        dissect_attempts = WritingAttempt.objects.filter(
            user=user, phase=PHASE_DISSECT
        ).count()
        imitate_attempts = WritingAttempt.objects.filter(
            user=user, phase=PHASE_IMITATE
        ).count()
        produce_attempts = WritingAttempt.objects.filter(
            user=user, phase=PHASE_PRODUCE
        ).count()
        pending_review   = WritingAttempt.objects.filter(
            user=user, phase=PHASE_PRODUCE, status=STATUS_PENDING
        ).count()

        total_seconds = WritingAttempt.objects.filter(
            user=user
        ).aggregate(total=Sum('time_spent_seconds'))['total'] or 0

        last_activity = WritingAttempt.objects.filter(
            user=user
        ).order_by('-created_at').values_list(
            'created_at', flat=True
        ).first()

        needs_review_count = WritingAttempt.objects.filter(
            user=user,
            phase=PHASE_PRODUCE,
            status__in=(STATUS_FAILED, STATUS_COOLDOWN),
        ).values('content').distinct().count()

        recent_attempts   = WritingAttempt.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
        recent_masteries  = WritingStageMastery.objects.filter(
            user=user, academic_year=year
        ).order_by('-mastered_at')[:5] if year else []

        return {
            'academic_year_label':     year.label if year else None,
            'total_stages_available':  total_stages,
            'total_stages_mastered':   mastered_stages,
            'overall_percent':         int((mastered_stages / total_stages) * 100) if total_stages else 0,
            'sentence_total':          by_tier[TIER_SENTENCE]['total'],
            'sentence_mastered':       by_tier[TIER_SENTENCE]['mastered'],
            'paragraph_total':         by_tier[TIER_PARAGRAPH]['total'],
            'paragraph_mastered':      by_tier[TIER_PARAGRAPH]['mastered'],
            'genre_total':             by_tier[TIER_GENRE]['total'],
            'genre_mastered':          by_tier[TIER_GENRE]['mastered'],
            'total_attempts':          total_attempts,
            'dissect_attempts':        dissect_attempts,
            'imitate_attempts':        imitate_attempts,
            'produce_attempts':        produce_attempts,
            'pending_teacher_review':  pending_review,
            'total_time_spent':        total_seconds // 60,
            'last_activity':           last_activity,
            'needs_review_count':      needs_review_count,
            'recent_attempts':         WritingAttemptListSerializer(
                recent_attempts, many=True
            ).data,
            'recent_masteries':        WritingStageMasteryListSerializer(
                recent_masteries, many=True
            ).data,
        }

    @action(detail=False, methods=['get'])
    def journey(self, request):
        """
        Return the complete writing journey for a unit.
        Alias for WritingStageContentViewSet.hub — for API consistency.
        """
        unit_id = request.query_params.get('unit_id')
        if not unit_id:
            return Response(
                {'detail': 'unit_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unit = get_object_or_404(Unit, pk=unit_id)
        year = get_current_academic_year()

        if not year:
            return Response(
                {'detail': 'No current academic year set.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        all_stages      = get_all_stage_statuses(request.user, unit, year)
        total_stages    = len(all_stages)
        mastered_stages = sum(
            1 for s in all_stages if s['status'] == 'mastered'
        )

        return Response({
            'unit_id':             unit.id,
            'unit_title':          unit.title,
            'class_level':         unit.textbook.class_level,
            'academic_year_id':    year.id,
            'academic_year_label': year.label,
            'overall_percent':     int((mastered_stages / total_stages) * 100) if total_stages else 0,
            'total_stages':        total_stages,
            'mastered_stages':     mastered_stages,
            'stages': [
                {
                    'content_id':    s['content'].id,
                    'stage_number':  s['stage'].number,
                    'stage_name':    s['stage'].name,
                    'stage_tier':    s['stage'].tier,
                    'eval_method':   s['stage'].eval_method,
                    'status':        s['status'],
                    'current_phase': s['current_phase'],
                    'is_in_cooldown': s['is_in_cooldown'],
                    'cooldown_ends_at': (
                        s['cooldown_ends_at'].isoformat()
                        if s['cooldown_ends_at'] else None
                    ),
                }
                for s in all_stages
            ],
        })