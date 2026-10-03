"""
URL configuration for Faculty Learning Hub.

All application endpoints live under /api/v1/ — the same public surface the
frontend and (later) the academic system integration consume, see
docs/adr/002-frontend-consumes-public-api.md.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # API v1 — add every new app's urls here under /api/v1/.
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/material/", include("materials.urls")),
    path("api/v1/drive/", include("materials.drive_urls")),

    # OpenAPI schema + interactive docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

# Dev only: Django never serves media when DEBUG is False.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
