from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.conf.urls.static import static
from .graphql import AuthenticatedGraphQLView

urlpatterns = [
    path("admin/", admin.site.urls),

    # === API GraphQL ===
    path("graphql/", csrf_exempt(AuthenticatedGraphQLView.as_view(graphiql=True))),

    # === API REST ===
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/marketplace/", include("apps.marketplace.urls")),
    path("api/v1/community/", include("apps.community.urls")),
    path("api/v1/webhooks/", include("apps.webhooks.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
