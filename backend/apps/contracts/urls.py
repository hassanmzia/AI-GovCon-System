from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.contracts.views import (
    ContractClauseViewSet,
    ContractMilestoneViewSet,
    ContractModificationViewSet,
    ContractTemplateViewSet,
    ContractVersionViewSet,
    ContractViewSet,
    OptionYearViewSet,
)

router = DefaultRouter()
router.register(r"templates", ContractTemplateViewSet, basename="contracttemplate")
router.register(r"clauses", ContractClauseViewSet, basename="contractclause")
router.register(r"contracts", ContractViewSet, basename="contract")
router.register(r"versions", ContractVersionViewSet, basename="contractversion")
router.register(r"milestones", ContractMilestoneViewSet, basename="contractmilestone")
router.register(r"modifications", ContractModificationViewSet, basename="contractmodification")
router.register(r"option-years", OptionYearViewSet, basename="optionyear")

urlpatterns = [
    path("", include(router.urls)),
]
