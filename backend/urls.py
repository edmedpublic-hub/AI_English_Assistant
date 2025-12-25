from django.urls import path, include
from django.views.generic import TemplateView
from vocab_master.admin import admin_site

urlpatterns = [
    # Admin
    path("admin/", admin_site.urls),

    # API endpoints (no namespaces)
    path("api/content/", include("content.api_urls")),
    path("api/reading/", include("reading.api_urls")),
    path("api/translation/", include("translation.api_urls")),

    # Frontend pages
    path("", TemplateView.as_view(template_name="index.html"), name="index"),

    path("reading/", include("reading.urls")),
    path("vocab/", include("vocab_master.urls")),
    path("content/", include("content.urls")),

    # Translation frontend (namespace is fine here)
    path(
        "translation/",
        include(("translation.urls", "translation"), namespace="translation"),
    ),
]
