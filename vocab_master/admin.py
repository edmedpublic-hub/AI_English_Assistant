# PATH: vocab_master/admin.py
# ACTION: Replace the entire existing file with this content.
#
# CHANGES FROM ORIGINAL:
#   - Removed the blind `for model in apps.get_models()` loop that dumped
#     every model into one flat list.
#   - Added explicit registration of all content/reading/translation/vocab_master
#     models using their proper ModelAdmin classes.
#   - Overrode get_app_list() to organise the sidebar into logical groups:
#       • Core Structure       (Textbooks, Units, Lessons, Chunks)
#       • Punctuation          (Global → Teaching → Attempts)
#       • Grammar              (Global → Teaching → Attempts)
#       • Vocabulary           (Global → Teaching → Attempts)
#       • Comprehension        (Teaching → Attempts)
#       • Writing              (Teaching → Attempts)
#       • Pronunciation        (Teaching → Attempts)
#       • Unit Testing         (Sessions, Questions, Answers)
#       • Reading App
#       • Translation App
#       • Vocab Master App
#       • Auth & Permissions

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

    # ── Dashboard view (unchanged from original) ──────────────

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

    # ── Organised sidebar ─────────────────────────────────────

    def get_app_list(self, request, app_label=None):
        """
        Replace Django's default app-based grouping with our own
        domain-based groups. Each group is a dict that matches
        Django's app_list structure so the default admin template
        renders it without any template changes.
        """
        # Collect the default list so we can pull models from it
        default = {
            model_dict["object_name"]: model_dict
            for app in super().get_app_list(request)
            for model_dict in app["models"]
        }

        def pick(object_names):
            """Return model dicts for the given object_names, in that order."""
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
                    # Global curriculum
                    "PunctuationMark",
                    "PunctuationRule",
                    "PunctuationExample",
                    # Teaching layer
                    "ChunkPunctuationFocus",
                    "ChunkPunctuationFocusRule",
                    "PunctuationQuestion",
                    # Attempts
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
                    # Global curriculum
                    "GrammarConcept",
                    "GrammarRule",
                    "GrammarExample",
                    # Teaching layer
                    "ChunkGrammarFocus",
                    "GrammarQuestion",
                    # Attempts
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
                    # Teaching layer
                    "VocabularyItem",
                    # Attempts
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
                    "ChunkWritingFocus",
                    "UnitWritingTask",
                    "WritingPrompt",
                    "WritingPracticeAttempt",
                    "WritingTestAttempt",
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
                    # add other reading models here as needed
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

        # Filter out empty groups (models the user has no perms for)
        return [g for g in groups if g["models"]]


# ═══════════════════════════════════════════════════════════════
#  INSTANTIATE THE CUSTOM SITE
# ═══════════════════════════════════════════════════════════════

admin_site = DashboardAdminSite(name="dashboard_admin")


# ═══════════════════════════════════════════════════════════════
#  VOCAB MASTER MODELS  (registered with custom admins)
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
    list_display = ("word", "part_of_speech", "reviewed", "lesson")
    list_filter  = ("part_of_speech", "reviewed", "lesson__unit__textbook")
    search_fields = ("word", "definition", "urdu_meaning")
    inlines = [SynonymInline, AntonymInline, ExampleSentenceInline]


admin_site.register(Vocabulary,     VocabularyAdmin)
admin_site.register(Synonym)
admin_site.register(Antonym)
admin_site.register(ExampleSentence)
# Lesson/Unit/Textbook from vocab_master are separate models from content app
# Register them simply so they appear in the Vocab Master group
admin_site.register(Lesson)
admin_site.register(Unit)
admin_site.register(Textbook)


# ═══════════════════════════════════════════════════════════════
#  CONTENT APP  (import and register all domain admins)
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
admin_site.register(ContentTextbook,  TextbookAdmin)
admin_site.register(ContentUnit,      UnitAdmin)
admin_site.register(ContentLesson,    LessonAdmin)
admin_site.register(LessonChunk,      LessonChunkAdmin)

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
admin_site.register(GrammarConcept,         GrammarConceptAdmin)
admin_site.register(GrammarRule,            GrammarRuleAdmin)
admin_site.register(GrammarExample,         GrammarExampleAdmin)
admin_site.register(ChunkGrammarFocus,      ChunkGrammarFocusAdmin)
admin_site.register(GrammarQuestion,        GrammarQuestionAdmin)
admin_site.register(GrammarPracticeAttempt, GrammarPracticeAttemptAdmin)
admin_site.register(GrammarTestAttempt,     GrammarTestAttemptAdmin)

# Vocabulary
from content.admin.vocabulary import (
    VocabularyItemAdmin, VocabularyAttemptAdmin, StudentVocabMasteryAdmin,
)
from content.models.vocabulary import (
    VocabularyItem, VocabularyAttempt, StudentVocabMastery,
)
admin_site.register(VocabularyItem,       VocabularyItemAdmin)
admin_site.register(VocabularyAttempt,    VocabularyAttemptAdmin)
admin_site.register(StudentVocabMastery,  StudentVocabMasteryAdmin)

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
admin_site.register(ChunkComprehensionFocus,        ChunkComprehensionFocusAdmin)
admin_site.register(ComprehensionQuestion,          ComprehensionQuestionAdmin)
admin_site.register(ComprehensionPracticeAttempt,   ComprehensionPracticeAttemptAdmin)
admin_site.register(ComprehensionTestAttempt,       ComprehensionTestAttemptAdmin)
admin_site.register(ComprehensionQuestionAttempt,   ComprehensionQuestionAttemptAdmin)

# Writing
from content.admin.writing import (
    ChunkWritingFocusAdmin, UnitWritingTaskAdmin, WritingPromptAdmin,
    WritingPracticeAttemptAdmin, WritingTestAttemptAdmin,
)
from content.models.writing import (
    ChunkWritingFocus, UnitWritingTask, WritingPrompt,
    WritingPracticeAttempt, WritingTestAttempt,
)
admin_site.register(ChunkWritingFocus,      ChunkWritingFocusAdmin)
admin_site.register(UnitWritingTask,        UnitWritingTaskAdmin)
admin_site.register(WritingPrompt,          WritingPromptAdmin)
admin_site.register(WritingPracticeAttempt, WritingPracticeAttemptAdmin)
admin_site.register(WritingTestAttempt,     WritingTestAttemptAdmin)

# Pronunciation
from content.admin.pronunciation import (
    PronunciationFocusAdmin, PronunciationAttemptAdmin, PronunciationMasteryAdmin,
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
admin_site.register(UnitTestSession,             UnitTestSessionAdmin)
admin_site.register(UnitTestQuestion,            UnitTestQuestionAdmin)
admin_site.register(UnitTestAnswer,              UnitTestAnswerAdmin)
admin_site.register(VocabularyUnitTestAttempt,   VocabularyUnitTestAttemptAdmin)


# ═══════════════════════════════════════════════════════════════
#  OTHER APPS  (reading, translation — simple registration)
#  If these apps have their own ModelAdmin classes, import and
#  use them here the same way as the content app above.
# ═══════════════════════════════════════════════════════════════

from django.apps import apps as django_apps
from django.contrib.admin import ModelAdmin

_ALREADY_REGISTERED = {
    # content
    ContentTextbook, ContentUnit, ContentLesson, LessonChunk,
    PunctuationMark, PunctuationRule, PunctuationExample,
    ChunkPunctuationFocus, ChunkPunctuationFocusRule,
    PunctuationQuestion, PunctuationPracticeAttempt, PunctuationTestAttempt,
    GrammarConcept, GrammarRule, GrammarExample,
    ChunkGrammarFocus, GrammarQuestion,
    GrammarPracticeAttempt, GrammarTestAttempt,
    VocabularyItem, VocabularyAttempt, StudentVocabMastery,
    ChunkComprehensionFocus, ComprehensionQuestion,
    ComprehensionPracticeAttempt, ComprehensionTestAttempt,
    ComprehensionQuestionAttempt,
    ChunkWritingFocus, UnitWritingTask, WritingPrompt,
    WritingPracticeAttempt, WritingTestAttempt,
    PronunciationFocus, PronunciationAttempt, PronunciationMastery,
    UnitTestSession, UnitTestQuestion, UnitTestAnswer, VocabularyUnitTestAttempt,
    # vocab_master
    Vocabulary, Synonym, Antonym, ExampleSentence,
    Lesson, Unit, Textbook,
}

# Register remaining models from reading, translation, vocab_master simply.
# They will appear in their respective sidebar groups via get_app_list.
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