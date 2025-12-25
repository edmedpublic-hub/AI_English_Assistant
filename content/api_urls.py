from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    TextbookViewSet,
    UnitViewSet,
    LessonViewSet,
    VocabularyItemViewSet,
    ComprehensionQuestionViewSet,
    GrammarPointViewSet,
    WritingTaskViewSet,
    SentenceAttemptViewSet,
    ExtractGrammar,
    
)

# ======================================================
# MAIN ROUTER (Flat CRUD for all models)
# ======================================================
router = DefaultRouter()
router.register(r"textbooks", TextbookViewSet)
router.register(r"units", UnitViewSet)
router.register(r"lessons", LessonViewSet)
router.register(r"vocabulary", VocabularyItemViewSet)
router.register(r"questions", ComprehensionQuestionViewSet)
router.register(r"grammar", GrammarPointViewSet)
router.register(r"writing-tasks", WritingTaskViewSet)
router.register(r"sentence-attempts", SentenceAttemptViewSet)


# ======================================================
# NESTED ENDPOINTS (Custom filtered list views)
# ======================================================
urlpatterns = [

    # Textbook → Units
    path(
        "textbooks/<int:textbook_id>/units/",
        UnitViewSet.as_view({"get": "list"}),
        name="textbook-units-list",
    ),

    # Unit → Lessons
    path(
        "units/<int:unit_id>/lessons/",
        LessonViewSet.as_view({"get": "list"}),
        name="unit-lessons-list",
    ),

    # Lesson → Vocabulary
    path(
        "lessons/<int:lesson_id>/vocab/",
        VocabularyItemViewSet.as_view({"get": "list"}),
        name="lesson-vocab-list",
    ),

    # Lesson → Writing Tasks
    path(
        "lessons/<int:lesson_id>/writing_tasks/",
        WritingTaskViewSet.as_view({"get": "list"}),
        name="lesson-writing-tasks-list",
    ),
path(
        "lessons/<int:lesson_id>/extract-grammar/",
        ExtractGrammar.as_view(),
        name="extract-grammar",
    ),
   
]

# Add automatically generated CRUD routes
urlpatterns += router.urls
