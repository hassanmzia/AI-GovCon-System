from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/health/", include("apps.core.urls")),
    path("django-admin/", admin.site.urls),
    # API schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # App APIs
    path("api/auth/", include("apps.accounts.urls")),
    path("api/opportunities/", include("apps.opportunities.urls")),
    path("api/deals/", include("apps.deals.urls")),
    path("api/rfp/", include("apps.rfp.urls")),
    path("api/past-performance/", include("apps.past_performance.urls")),
    path("api/proposals/", include("apps.proposals.urls")),
    path("api/pricing/", include("apps.pricing.urls")),
    path("api/contracts/", include("apps.contracts.urls")),
    path("api/strategy/", include("apps.strategy.urls")),
    path("api/marketing/", include("apps.marketing.urls")),
    path("api/research/", include("apps.research.urls")),
    path("api/legal/", include("apps.legal.urls")),
    path("api/teaming/", include("apps.teaming.urls")),
    path("api/security-compliance/", include("apps.security_compliance.urls")),
    path("api/knowledge-vault/", include("apps.knowledge_vault.urls")),
    path("api/communications/", include("apps.communications.urls")),
    path("api/policies/", include("apps.policies.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
]
