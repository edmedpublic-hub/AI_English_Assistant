# content/api_urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views.lessons import LessonViewSet
from .views.vocab import VocabularyItemViewSet
from .views.grammar import GrammarPointViewSet
from .views.writing import WritingTaskViewSet, SentenceAttemptViewSet
from .views.comprehension import ComprehensionQuestionViewSet

# ======================================================
# MAIN ROUTER (CRUD routes for all core models)
# ======================================================
router = DefaultRouter()


router.register(r"lessons", LessonViewSet, basename="lesson")
router.register(r"vocabulary", VocabularyItemViewSet, basename="vocabulary")
router.register(r"questions", ComprehensionQuestionViewSet, basename="question")
router.register(r"grammar", GrammarPointViewSet, basename="grammar")
router.register(r"writing-tasks", WritingTaskViewSet, basename="writing-task")
router.register(r"sentence-attempts", SentenceAttemptViewSet, basename="sentence-attempt")

# ======================================================
# NESTED ENDPOINTS (Filtered list views by parent)
# ======================================================
urlpatterns = [

  

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

   
]

# Append the router-generated CRUD routes
urlpatterns += router.urls
