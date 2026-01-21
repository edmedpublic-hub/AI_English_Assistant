from django.urls import path, include

urlpatterns = [
    path("", include("content.urls.core_urls")),
    path("", include("content.urls.chunk_urls")),
    path("", include("content.urls.vocabulary_urls")),
    path("", include("content.urls.tests_urls")),
    path("", include("content.urls.grammar_urls")),
]
