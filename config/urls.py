"""
URL configuration for Faculty Learning Hub.

All application endpoints live under /api/v1/ — the same public surface the
frontend and (later) the academic system integration consume, see
docs/adr/002-frontend-consumes-public-api.md.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # API v1 — add every new app's urls here under /api/v1/.
    path("api/v1/auth/", include("accounts.urls")),

    # OpenAPI schema + interactive docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
