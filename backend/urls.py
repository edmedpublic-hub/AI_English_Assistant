# backend/urls.py

from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from vocab_master.admin import admin_site

urlpatterns = [
    # Admin
    path("admin/", admin_site.urls),

    # API endpoints
    path("api/content/", include("content.api_urls")),
    path("api/reading/", include("reading.api_urls")),
    path("api/translation/", include("translation.api_urls")),

    # Frontend pages
    path("", TemplateView.as_view(template_name="index.html"), name="index"),
    path("reading/", include("reading.urls")),
    path("vocab/", include("vocab_master.urls")),
    path("content/", include("content.urls")),

    # Translation frontend (explicit namespace)
    path(
        "translation/",
        include(("translation.urls", "translation"), namespace="translation"),
    ),
]

# Serve media in development
# Serve media and static in development



if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    
