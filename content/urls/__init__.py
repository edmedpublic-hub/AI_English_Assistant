# content/urls/__init__.py
from django.urls import include, path

app_name = "content"

urlpatterns = [
    path('', include('content.urls.core')),
    path("content/chunks/", include("content.urls.chunk_urls")),
    path("", include("content.urls.vocabulary")),
    path("", include("content.urls.tests_urls")),
    path("writing/", include("content.urls.writing")),
]