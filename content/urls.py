# content/urls.py
from django.urls import path, include

app_name = "content"

urlpatterns = [
    path("", include("content.urls.core_urls")),

    # ✅ Mount chunk routes under /content/chunks/
    path("content/chunks/", include("content.urls.chunk_urls")),

    path("", include("content.urls.vocabulary_urls")),
    path("", include("content.urls.tests_urls")),

    # Grammar focus-level routes are already nested inside chunk_urls.py
    # so no need to include grammar_urls separately here.

    # Punctuation focus-level routes are also nested inside chunk_urls.py
    # so no need to include punctuation separately here either.
]