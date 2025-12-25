# content/urls.py
from django.urls import path
from . import views

app_name = "content"

urlpatterns = [
    # Home
    path("", views.content_home, name="content_home"),

    # Textbooks → Units → Lessons (template views)
    path("textbooks/", views.content_textbook_list, name="textbook-list"),
    path("textbooks/<int:textbook_id>/units/", views.content_unit_list, name="unit-list"),

    # Lessons list & detail (student-prefixed template views)
    path("student/<str:student_id>/units/<int:unit_id>/lessons/",
         views.content_lesson_list,
         name="lesson-list"),
    path("student/<str:student_id>/lessons/<int:lesson_id>/",
         views.content_lesson_detail,
         name="lesson-detail"),
    path("student/<str:student_id>/dashboard/",
         views.content_student_dashboard,
         name="student-dashboard"),

    # ✅ Vocabulary routes
    path("student/<str:student_id>/lessons/<int:lesson_id>/vocabulary/",
         views.content_vocab_list,
         name="lesson-vocabulary"),
    path("vocabulary/<int:item_id>/",
         views.content_vocab_item_detail,
         name="vocab-item-detail"),
]