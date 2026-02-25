# content/urls/__init__.py

from django.urls import include, path

app_name = "content"

urlpatterns = [
    # --------------------------------------------------
    # CORE (textbooks, units, lessons, chunks)
    # All chunk-level domain URLs are nested inside core
    # via chunk_urls.py
    # --------------------------------------------------
    path('', include('content.urls.core')),
]