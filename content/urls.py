from django.urls import path

from .views.home import content_home
from .views.textbooks import (
    content_textbook_list,
    content_unit_list,
)
from .views.lessons import (
    content_lesson_list,
    content_lesson_detail,
)
from .views.student import content_student_dashboard
from .views.vocab import (
    content_vocab_list,
    content_vocab_item_detail,
)

app_name = "content"

urlpatterns = [
    path("", content_home, name="content_home"),

    path("textbooks/", content_textbook_list, name="textbook-list"),
    path("textbooks/<int:textbook_id>/units/", content_unit_list, name="unit-list"),

    path(
        "student/<str:student_id>/units/<int:unit_id>/lessons/",
        content_lesson_list,
        name="lesson-list",
    ),
    path(
        "student/<str:student_id>/lessons/<int:lesson_id>/",
        content_lesson_detail,
        name="lesson-detail",
    ),

    path(
        "student/<str:student_id>/dashboard/",
        content_student_dashboard,
        name="student-dashboard",
    ),

    path(
        "student/<str:student_id>/lessons/<int:lesson_id>/vocabulary/",
        content_vocab_list,
        name="lesson-vocabulary",
    ),
    path(
        "vocabulary/<int:item_id>/",
        content_vocab_item_detail,
        name="vocab-item-detail",
    ),
]
