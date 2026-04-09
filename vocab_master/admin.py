# PATH: vocab_master/admin.py

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.http import HttpResponseForbidden
from django.urls import path
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek

from .models import Vocabulary, Lesson, Unit, Textbook, Synonym, Antonym, ExampleSentence


# ═══════════════════════════════════════════════════════════════
#  CUSTOM ADMIN SITE
# ═══════════════════════════════════════════════════════════════

class DashboardAdminSite(AdminSite):
    site_header  = "AI English Assistant — Admin"
    site_title   = "Teaching Dashboard"
    index_title  = "Welcome to the Teaching Dashboard"

    def dashboard_view(self, request):
        if not request.user.is_active or not request.user.is_staff:
            return HttpResponseForbidden("You don't have permission.")

        total_vocab    = Vocabulary.objects.count()
        reviewed_vocab = Vocabulary.objects.filter(reviewed=True).count()
        progress       = (reviewed_vocab / total_vocab * 100) if total_vocab > 0 else 0

        pos_data   = Vocabulary.objects.values("part_of_speech").annotate(count=Count("id"))
        pos_labels = [i["part_of_speech"].capitalize() for i in pos_data]
        pos_counts = [i["count"] for i in pos_data]

        trend_data = (
            Vocabulary.objects.filter(reviewed=True)
            .annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(count=Count("id"))
            .order_by("week")
        )
        trend_labels = [str(i["week"].date()) for i in trend_data if i["week"]]
        trend_counts = [i["count"] for i in trend_data]

        lesson_progress = Lesson.objects.annotate(
            total_vocab=Count("vocabulary"),
            reviewed_vocab=Count("vocabulary", filter=Q(vocabulary__reviewed=True)),
        )
        unit_progress = Unit.objects.annotate(
            total_vocab=Count("lessons__vocabulary"),
            reviewed_vocab=Count(
                "lessons__vocabulary",
                filter=Q(lessons__vocabulary__reviewed=True),
            ),
        )
        textbook_progress = Textbook.objects.annotate(
            total_vocab=Count("units__lessons__vocabulary"),
            reviewed_vocab=Count(
                "units__lessons__vocabulary",
                filter=Q(units__lessons__vocabulary__reviewed=True),
            ),
        )

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
        return [
            path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
        ] + urls

    def get_app_list(self, request, app_label=None):
        default = {
            model_dict["object_name"]: model_dict
            for app in super().get_app_list(request)
            for model_dict in app["models"]
        }

        def pick(object_names):
            return [
                default[n] for n in object_names if n in default
            ]

        groups = [

            # ── Core structure ─────────────────────────────────
            {
                "name": "📚 Core Structure",
                "app_label": "core_structure",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "Textbook", "Unit", "Lesson", "LessonChunk",
                ]),
            },

            # ── Punctuation ────────────────────────────────────
            {
                "name": "⁖ Punctuation",
                "app_label": "punctuation",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "PunctuationMark",
                    "PunctuationRule",
                    "PunctuationExample",
                    "ChunkPunctuationFocus",
                    "ChunkPunctuationFocusRule",
                    "PunctuationQuestion",
                    "PunctuationPracticeAttempt",
                    "PunctuationTestAttempt",
                ]),
            },

            # ── Grammar ───────────────────────────────────────
            {
                "name": "📐 Grammar",
                "app_label": "grammar",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "GrammarConcept",
                    "GrammarRule",
                    "GrammarExample",
                    "ChunkGrammarFocus",
                    "GrammarQuestion",
                    "GrammarPracticeAttempt",
                    "GrammarTestAttempt",
                ]),
            },

            # ── Vocabulary ────────────────────────────────────
            {
                "name": "📖 Vocabulary",
                "app_label": "vocabulary",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "VocabularyItem",
                    "VocabularyAttempt",
                    "StudentVocabMastery",
                ]),
            },

            # ── Comprehension ─────────────────────────────────
            {
                "name": "🔍 Comprehension",
                "app_label": "comprehension",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "ChunkComprehensionFocus",
                    "ComprehensionQuestion",
                    "ComprehensionPracticeAttempt",
                    "ComprehensionTestAttempt",
                    "ComprehensionQuestionAttempt",
                ]),
            },

            # ── Writing ───────────────────────────────────────
            {
                "name": "✍️ Writing",
                "app_label": "writing",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "WritingAcademicYear",
                    "WritingStage",
                    "WritingStageContent",
                    "WritingAttempt",
                    "WritingStageMastery",
                    "WritingIntervention",
                ]),
            },

            # ── Pronunciation ─────────────────────────────────
            {
                "name": "🔊 Pronunciation",
                "app_label": "pronunciation",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "PronunciationFocus",
                    "PronunciationAttempt",
                    "PronunciationMastery",
                ]),
            },

            # ── Unit Testing ──────────────────────────────────
            {
                "name": "🧪 Unit Testing",
                "app_label": "unit_testing",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "UnitTestSession",
                    "UnitTestQuestion",
                    "UnitTestAnswer",
                    "VocabularyUnitTestAttempt",
                ]),
            },

            # ── Reading app ───────────────────────────────────
            {
                "name": "📰 Reading",
                "app_label": "reading",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "BookCategory",
                    "Book",
                    "ReadingLesson",
                ]),
            },

            # ── Translation app ───────────────────────────────
            {
                "name": "🌐 Translation",
                "app_label": "translation",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "TranslationTextbook",
                    "TranslationUnit",
                    "TranslationLesson",
                ]),
            },

            # ── Vocab Master app ──────────────────────────────
            {
                "name": "🗂 Vocab Master",
                "app_label": "vocab_master",
                "app_url": "",
                "has_module_perms": True,
                "models": pick([
                    "Vocabulary",
                    "Synonym",
                    "Antonym",
                    "ExampleSentence",
                ]),
            },

            # ── Auth ──────────────────────────────────────────
            {
                "name": "🔐 Auth & Permissions",
                "app_label": "auth",
                "app_url": "",
                "has_module_perms": True,
                "models": pick(["User", "Group", "Permission"]),
            },
        ]

        return [g for g in groups if g["models"]]


# ═══════════════════════════════════════════════════════════════
#  INSTANTIATE THE CUSTOM SITE
# ═══════════════════════════════════════════════════════════════

admin_site = DashboardAdminSite(name="dashboard_admin")


# ═══════════════════════════════════════════════════════════════
#  VOCAB MASTER MODELS
# ═══════════════════════════════════════════════════════════════

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
    list_display  = ("word", "part_of_speech", "reviewed", "lesson")
    list_filter   = ("part_of_speech", "reviewed", "lesson__unit__textbook")
    search_fields = ("word", "definition", "urdu_meaning")
    inlines       = [SynonymInline, AntonymInline, ExampleSentenceInline]


admin_site.register(Vocabulary,      VocabularyAdmin)
admin_site.register(Synonym)
admin_site.register(Antonym)
admin_site.register(ExampleSentence)
admin_site.register(Lesson)
admin_site.register(Unit)
admin_site.register(Textbook)


# ═══════════════════════════════════════════════════════════════
#  CONTENT APP
# ═══════════════════════════════════════════════════════════════

# Core
from content.admin.core import (
    TextbookAdmin, UnitAdmin, LessonAdmin, LessonChunkAdmin,
)
from content.models.core import (
    Textbook as ContentTextbook,
    Unit as ContentUnit,
    Lesson as ContentLesson,
    LessonChunk,
)
admin_site.register(ContentTextbook, TextbookAdmin)
admin_site.register(ContentUnit,     UnitAdmin)
admin_site.register(ContentLesson,   LessonAdmin)
admin_site.register(LessonChunk,     LessonChunkAdmin)

# Punctuation
from content.admin.punctuation import (
    PunctuationMarkAdmin, PunctuationRuleAdmin, PunctuationExampleAdmin,
    ChunkPunctuationFocusAdmin, ChunkPunctuationFocusRuleAdmin,
    PunctuationQuestionAdmin, PunctuationPracticeAttemptAdmin,
    PunctuationTestAttemptAdmin,
)
from content.models.punctuation import (
    PunctuationMark, PunctuationRule, PunctuationExample,
    ChunkPunctuationFocus, ChunkPunctuationFocusRule,
    PunctuationQuestion, PunctuationPracticeAttempt, PunctuationTestAttempt,
)
admin_site.register(PunctuationMark,            PunctuationMarkAdmin)
admin_site.register(PunctuationRule,            PunctuationRuleAdmin)
admin_site.register(PunctuationExample,         PunctuationExampleAdmin)
admin_site.register(ChunkPunctuationFocus,      ChunkPunctuationFocusAdmin)
admin_site.register(ChunkPunctuationFocusRule,  ChunkPunctuationFocusRuleAdmin)
admin_site.register(PunctuationQuestion,        PunctuationQuestionAdmin)
admin_site.register(PunctuationPracticeAttempt, PunctuationPracticeAttemptAdmin)
admin_site.register(PunctuationTestAttempt,     PunctuationTestAttemptAdmin)

# Grammar
from content.admin.grammar import (
    GrammarConceptAdmin, GrammarRuleAdmin, GrammarExampleAdmin,
    ChunkGrammarFocusAdmin, GrammarQuestionAdmin,
    GrammarPracticeAttemptAdmin, GrammarTestAttemptAdmin,
)
from content.models.grammar import (
    GrammarConcept, GrammarRule, GrammarExample,
    ChunkGrammarFocus, GrammarQuestion,
    GrammarPracticeAttempt, GrammarTestAttempt,
)
admin_site.register(GrammarConcept,          GrammarConceptAdmin)
admin_site.register(GrammarRule,             GrammarRuleAdmin)
admin_site.register(GrammarExample,          GrammarExampleAdmin)
admin_site.register(ChunkGrammarFocus,       ChunkGrammarFocusAdmin)
admin_site.register(GrammarQuestion,         GrammarQuestionAdmin)
admin_site.register(GrammarPracticeAttempt,  GrammarPracticeAttemptAdmin)
admin_site.register(GrammarTestAttempt,      GrammarTestAttemptAdmin)

# Vocabulary
from content.admin.vocabulary import (
    VocabularyItemAdmin, VocabularyAttemptAdmin, StudentVocabMasteryAdmin,
)
from content.models.vocabulary import (
    VocabularyItem, VocabularyAttempt, StudentVocabMastery,
)
admin_site.register(VocabularyItem,      VocabularyItemAdmin)
admin_site.register(VocabularyAttempt,   VocabularyAttemptAdmin)
admin_site.register(StudentVocabMastery, StudentVocabMasteryAdmin)

# Comprehension
from content.admin.comprehension import (
    ChunkComprehensionFocusAdmin, ComprehensionQuestionAdmin,
    ComprehensionPracticeAttemptAdmin, ComprehensionTestAttemptAdmin,
    ComprehensionQuestionAttemptAdmin,
)
from content.models.comprehension import (
    ChunkComprehensionFocus, ComprehensionQuestion,
    ComprehensionPracticeAttempt, ComprehensionTestAttempt,
    ComprehensionQuestionAttempt,
)
admin_site.register(ChunkComprehensionFocus,       ChunkComprehensionFocusAdmin)
admin_site.register(ComprehensionQuestion,         ComprehensionQuestionAdmin)
admin_site.register(ComprehensionPracticeAttempt,  ComprehensionPracticeAttemptAdmin)
admin_site.register(ComprehensionTestAttempt,      ComprehensionTestAttemptAdmin)
admin_site.register(ComprehensionQuestionAttempt,  ComprehensionQuestionAttemptAdmin)

# Writing — new three-tier architecture
from content.admin.writing import (
    WritingAcademicYearAdmin,
    WritingStageAdmin,
    WritingStageContentAdmin,
    WritingAttemptAdmin,
    WritingStageMasteryAdmin,
    WritingInterventionAdmin,
)
from content.models.writing import (
    WritingAcademicYear,
    WritingStage,
    WritingStageContent,
    WritingAttempt,
    WritingStageMastery,
    WritingIntervention,
)
admin_site.register(WritingAcademicYear,  WritingAcademicYearAdmin)
admin_site.register(WritingStage,         WritingStageAdmin)
admin_site.register(WritingStageContent,  WritingStageContentAdmin)
admin_site.register(WritingAttempt,       WritingAttemptAdmin)
admin_site.register(WritingStageMastery,  WritingStageMasteryAdmin)
admin_site.register(WritingIntervention,  WritingInterventionAdmin)

# Pronunciation
from content.admin.pronunciation import (
    PronunciationFocusAdmin, PronunciationAttemptAdmin,
    PronunciationMasteryAdmin,
)
from content.models.pronunciation import (
    PronunciationFocus, PronunciationAttempt, PronunciationMastery,
)
admin_site.register(PronunciationFocus,   PronunciationFocusAdmin)
admin_site.register(PronunciationAttempt, PronunciationAttemptAdmin)
admin_site.register(PronunciationMastery, PronunciationMasteryAdmin)

# Testing
from content.admin.testing import (
    UnitTestSessionAdmin, UnitTestQuestionAdmin,
    UnitTestAnswerAdmin, VocabularyUnitTestAttemptAdmin,
)
from content.models.testing import (
    UnitTestSession, UnitTestQuestion,
    UnitTestAnswer, VocabularyUnitTestAttempt,
)
admin_site.register(UnitTestSession,           UnitTestSessionAdmin)
admin_site.register(UnitTestQuestion,          UnitTestQuestionAdmin)
admin_site.register(UnitTestAnswer,            UnitTestAnswerAdmin)
admin_site.register(VocabularyUnitTestAttempt, VocabularyUnitTestAttemptAdmin)


# ═══════════════════════════════════════════════════════════════
#  OTHER APPS  (reading, translation — simple registration)
# ═══════════════════════════════════════════════════════════════

from django.apps import apps as django_apps
from django.contrib.admin import ModelAdmin

_ALREADY_REGISTERED = {
    # content — core
    ContentTextbook, ContentUnit, ContentLesson, LessonChunk,
    # content — punctuation
    PunctuationMark, PunctuationRule, PunctuationExample,
    ChunkPunctuationFocus, ChunkPunctuationFocusRule,
    PunctuationQuestion, PunctuationPracticeAttempt, PunctuationTestAttempt,
    # content — grammar
    GrammarConcept, GrammarRule, GrammarExample,
    ChunkGrammarFocus, GrammarQuestion,
    GrammarPracticeAttempt, GrammarTestAttempt,
    # content — vocabulary
    VocabularyItem, VocabularyAttempt, StudentVocabMastery,
    # content — comprehension
    ChunkComprehensionFocus, ComprehensionQuestion,
    ComprehensionPracticeAttempt, ComprehensionTestAttempt,
    ComprehensionQuestionAttempt,
    # content — writing
    WritingAcademicYear, WritingStage, WritingStageContent,
    WritingAttempt, WritingStageMastery, WritingIntervention,
    # content — pronunciation
    PronunciationFocus, PronunciationAttempt, PronunciationMastery,
    # content — testing
    UnitTestSession, UnitTestQuestion,
    UnitTestAnswer, VocabularyUnitTestAttempt,
    # vocab_master
    Vocabulary, Synonym, Antonym, ExampleSentence,
    Lesson, Unit, Textbook,
}

for _app_label in ("reading", "translation", "vocab_master"):
    for _model in django_apps.get_app_config(_app_label).get_models():
        if _model not in _ALREADY_REGISTERED:
            try:
                admin_site.register(_model)
                _ALREADY_REGISTERED.add(_model)
            except admin.sites.AlreadyRegistered:
                pass

# Auth models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.admin import UserAdmin, GroupAdmin
try:
    admin_site.register(User,       UserAdmin)
    admin_site.register(Group,      GroupAdmin)
    admin_site.register(Permission)
except admin.sites.AlreadyRegistered:
    pass