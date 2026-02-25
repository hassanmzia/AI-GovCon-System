from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.workforce.views import (
    AnalyticsViewSet,
    AssignmentViewSet,
    ClearanceRecordViewSet,
    EmployeeViewSet,
    HiringRequisitionViewSet,
    SkillMatrixViewSet,
)

router = DefaultRouter()
router.register(r"employees", EmployeeViewSet, basename="employee")
router.register(r"skill-matrix", SkillMatrixViewSet, basename="skill-matrix")
router.register(r"clearance-records", ClearanceRecordViewSet, basename="clearance-record")
router.register(r"assignments", AssignmentViewSet, basename="assignment")
router.register(r"hiring-requisitions", HiringRequisitionViewSet, basename="hiring-requisition")
router.register(r"analytics", AnalyticsViewSet, basename="workforce-analytics")

urlpatterns = [
    path("", include(router.urls)),
]
