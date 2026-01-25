from django.urls import path, include

app_name = "content"   # 🔑 add this line

urlpatterns = [
    path("", include("content.urls.core_urls")),
    path("", include("content.urls.chunk_urls")),
    path("", include("content.urls.vocabulary_urls")),
    path("", include("content.urls.tests_urls")),
    path("", include("content.urls.grammar_urls")),
    path("", include("content.urls.punctuation")),
]