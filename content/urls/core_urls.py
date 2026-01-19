from django.urls import path
from .. import views

urlpatterns = [
    path("", views.index, name="content_index"),

    path("textbooks/", views.textbook_list, name="textbook_list"),
    path("textbooks/<int:pk>/", views.textbook_detail, name="textbook_detail"),

    path("units/", views.unit_list, name="unit_list"),
    path("units/<int:pk>/", views.unit_detail, name="unit_detail"),

    path("lessons/", views.lesson_list, name="lesson_list"),
    path("lessons/<int:pk>/", views.lesson_detail, name="lesson_detail"),

    path("chunks/<int:pk>/", views.chunk_detail, name="chunk_detail"),
]
