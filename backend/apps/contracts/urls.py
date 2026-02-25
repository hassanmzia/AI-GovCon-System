from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.contracts.views import (
    ContractClauseViewSet,
    ContractTemplateViewSet,
    ContractVersionViewSet,
    ContractViewSet,
)

router = DefaultRouter()
router.register(r"templates", ContractTemplateViewSet, basename="contracttemplate")
router.register(r"clauses", ContractClauseViewSet, basename="contractclause")
router.register(r"contracts", ContractViewSet, basename="contract")
router.register(r"versions", ContractVersionViewSet, basename="contractversion")

urlpatterns = [
    path("", include(router.urls)),
]
