from django.urls import path, include

app_name = "content"

urlpatterns = [
    path("", include("content.urls.core_urls")),
    path("content/chunks/", include("content.urls.chunk_urls")),
    path("", include("content.urls.vocabulary_urls")),
    path("", include("content.urls.tests_urls")),
    path("writing/", include(("content.urls.writing", "content"))),
]