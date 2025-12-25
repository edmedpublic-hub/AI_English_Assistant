from django.contrib import admin
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.http import HttpResponseForbidden
from django.urls import path
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek
from django.apps import apps

from .models import Vocabulary, Lesson, Unit, Textbook, Synonym, Antonym, ExampleSentence


# -------------------------
# Custom Dashboard Admin Site
# -------------------------
class DashboardAdminSite(AdminSite):
    site_header = "Teaching Dashboard"
    site_title = "Teaching Dashboard"
    index_title = "Welcome to the Teaching Dashboard"

    def dashboard_view(self, request):
        # Allow only active staff/superusers
        if not request.user.is_active or not request.user.is_staff:
            return HttpResponseForbidden("You don’t have permission to view this page.")

        # -------------------------
        # Vocabulary Stats
        # -------------------------
        total_vocab = Vocabulary.objects.count()
        reviewed_vocab = Vocabulary.objects.filter(reviewed=True).count()
        progress = (reviewed_vocab / total_vocab * 100) if total_vocab > 0 else 0

        # Parts of speech distribution
        pos_data = Vocabulary.objects.values("part_of_speech").annotate(count=Count("id"))
        pos_labels = [item["part_of_speech"].capitalize() for item in pos_data]
        pos_counts = [item["count"] for item in pos_data]

        # Review progress over time (weekly, based on created_at)
        trend_data = (
            Vocabulary.objects.filter(reviewed=True)
            .annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(count=Count("id"))
            .order_by("week")
        )
        trend_labels = [str(item["week"].date()) for item in trend_data if item["week"]]
        trend_counts = [item["count"] for item in trend_data]

        # -------------------------
        # Lesson Progress
        # -------------------------
        lesson_progress = Lesson.objects.annotate(
            total_vocab=Count("vocabulary"),
            reviewed_vocab=Count("vocabulary", filter=Q(vocabulary__reviewed=True))
        )

        # -------------------------
        # Unit Progress
        # -------------------------
        unit_progress = Unit.objects.annotate(
            total_vocab=Count("lessons__vocabulary"),
            reviewed_vocab=Count("lessons__vocabulary", filter=Q(lessons__vocabulary__reviewed=True))
        )

        # -------------------------
        # Textbook Progress
        # -------------------------
        textbook_progress = Textbook.objects.annotate(
            total_vocab=Count("units__lessons__vocabulary"),
            reviewed_vocab=Count("units__lessons__vocabulary", filter=Q(units__lessons__vocabulary__reviewed=True))
        )

        # Context for template
        context = dict(
            self.each_context(request),
            total_vocab=total_vocab,
            reviewed_vocab=reviewed_vocab,
            progress=progress,
            pos_labels=pos_labels,
            pos_counts=pos_counts,
            trend_labels=trend_labels,
            trend_counts=trend_counts,
            lesson_progress=lesson_progress,
            unit_progress=unit_progress,
            textbook_progress=textbook_progress,
        )
        return TemplateResponse(request, "admin/dashboard.html", context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
        ]
        return custom_urls + urls


# -------------------------
# Vocabulary Admin with Inlines
# -------------------------
class SynonymInline(admin.TabularInline):
    model = Synonym
    extra = 1


class AntonymInline(admin.TabularInline):
    model = Antonym
    extra = 1


class ExampleSentenceInline(admin.TabularInline):
    model = ExampleSentence
    extra = 1


class VocabularyAdmin(admin.ModelAdmin):
    list_display = ("word", "part_of_speech", "reviewed", "lesson")
    list_filter = ("part_of_speech", "reviewed", "lesson__unit__textbook")
    search_fields = ("word", "definition", "urdu_meaning")
    inlines = [SynonymInline, AntonymInline, ExampleSentenceInline]


# ✅ Replace default admin site with our custom one
admin_site = DashboardAdminSite(name="dashboard_admin")

# ✅ Register Vocabulary with custom admin (so inlines appear)
admin_site.register(Vocabulary, VocabularyAdmin)

# ✅ Automatically register all other models
for model in apps.get_models():
    if model not in [Vocabulary]:  # skip Vocabulary, already registered
        try:
            admin_site.register(model)
        except admin.sites.AlreadyRegistered:
            pass