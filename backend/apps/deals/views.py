import logging

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.deals.models import (
    Activity,
    Approval,
    Comment,
    Deal,
    DealStageHistory,
    Task,
    TaskTemplate,
)
from apps.deals.serializers import (
    ActivitySerializer,
    ApprovalDecisionSerializer,
    ApprovalSerializer,
    CommentSerializer,
    DealCreateSerializer,
    DealDetailSerializer,
    DealListSerializer,
    DealStageHistorySerializer,
    DealTransitionSerializer,
    TaskSerializer,
    TaskTemplateSerializer,
)
from apps.deals.workflow import WorkflowEngine

logger = logging.getLogger(__name__)


# ── Deal ViewSet ─────────────────────────────────────────


class DealViewSet(viewsets.ModelViewSet):
    """
    CRUD for deals plus custom pipeline actions.

    Supports filtering by stage, owner, priority, and outcome.
    Search across title and notes.  Ordering by any core field.
    """

    queryset = Deal.objects.select_related("opportunity", "owner").prefetch_related(
        "team"
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "stage": ["exact", "in"],
        "owner": ["exact"],
        "priority": ["exact", "lte", "gte"],
        "outcome": ["exact"],
        "due_date": ["lte", "gte"],
    }
    search_fields = ["title", "notes", "opportunity__title"]
    ordering_fields = [
        "created_at",
        "updated_at",
        "priority",
        "due_date",
        "estimated_value",
        "composite_score",
        "win_probability",
    ]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return DealListSerializer
        if self.action == "create":
            return DealCreateSerializer
        return DealDetailSerializer

    # ── Custom actions ───────────────────────────────────

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        """Advance or move a deal to a new pipeline stage."""
        deal = self.get_object()
        serializer = DealTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        engine = WorkflowEngine()
        target = serializer.validated_data["target_stage"]
        reason = serializer.validated_data.get("reason", "")

        try:
            engine.transition(deal, target, user=request.user, reason=reason)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        deal.refresh_from_db()
        return Response(DealDetailSerializer(deal).data)

    @action(detail=True, methods=["post"], url_path="request-approval")
    def request_approval(self, request, pk=None):
        """Create an approval request for a HITL gate."""
        deal = self.get_object()
        serializer = ApprovalSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        approval = Approval.objects.create(
            deal=deal,
            approval_type=serializer.validated_data["approval_type"],
            requested_by=request.user,
            requested_from=serializer.validated_data.get("requested_from"),
            ai_recommendation=serializer.validated_data.get("ai_recommendation", ""),
            ai_confidence=serializer.validated_data.get("ai_confidence"),
        )

        Activity.objects.create(
            deal=deal,
            actor=request.user,
            action="approval_requested",
            description=(
                f"Approval requested: {approval.get_approval_type_display()}"
            ),
            metadata={
                "approval_id": str(approval.id),
                "approval_type": approval.approval_type,
            },
        )

        return Response(
            ApprovalSerializer(approval).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["get"], url_path="stage-history")
    def stage_history(self, request, pk=None):
        """Return the full stage transition history for a deal."""
        deal = self.get_object()
        history = DealStageHistory.objects.filter(deal=deal).select_related(
            "transitioned_by"
        )
        serializer = DealStageHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="pipeline-summary")
    def pipeline_summary(self, request, pk=None):
        """Return a high-level summary of the deal's pipeline status."""
        deal = self.get_object()
        tasks_qs = deal.tasks.all()
        return Response(
            {
                "deal_id": str(deal.id),
                "current_stage": deal.stage,
                "stage_display": deal.get_stage_display(),
                "stage_entered_at": deal.stage_entered_at,
                "total_tasks": tasks_qs.count(),
                "completed_tasks": tasks_qs.filter(status="completed").count(),
                "blocked_tasks": tasks_qs.filter(status="blocked").count(),
                "pending_approvals": deal.approvals.filter(
                    status="pending"
                ).count(),
                "total_comments": deal.comments.count(),
                "win_probability": deal.win_probability,
                "composite_score": deal.composite_score,
            }
        )

    @action(detail=True, methods=["post"], url_path="run-solution-architect")
    def run_solution_architect(self, request, pk=None):
        """Trigger the Solution Architect Agent for this deal.

        Runs the full 9-node LangGraph pipeline:
        load_context → analyze_requirements → select_frameworks →
        retrieve_knowledge → synthesize_solution → generate_diagrams →
        generate_volume → validate → (refine loop)

        Returns the complete architecture output synchronously.
        For long-running jobs, consider using a Celery task.
        """
        deal = self.get_object()

        try:
            import asyncio
            from ai_orchestrator.src.agents.solution_architect_agent import SolutionArchitectAgent

            agent = SolutionArchitectAgent()
            result = asyncio.run(agent.run(
                deal_id=str(deal.id),
                opportunity_id=str(deal.opportunity_id),
            ))

            # Persist the solution as TechnicalSolution + ArchitectureDiagram models
            try:
                from apps.proposals.models import (
                    ArchitectureDiagram,
                    Proposal,
                    ProposalSection,
                    SolutionValidationReport,
                    TechnicalSolution,
                )

                ts_data = result.get("technical_solution", {})
                ts, _ = TechnicalSolution.objects.update_or_create(
                    deal=deal,
                    defaults={
                        "iteration_count": result.get("iteration_count", 1),
                        "selected_frameworks": result.get("selected_frameworks", []),
                        "requirement_analysis": result.get("requirement_analysis", {}),
                        "executive_summary": ts_data.get("executive_summary", ""),
                        "architecture_pattern": ts_data.get("architecture_pattern", ""),
                        "core_components": ts_data.get("core_components", []),
                        "technology_stack": ts_data.get("technology_stack", {}),
                        "integration_points": ts_data.get("integration_points", []),
                        "scalability_approach": ts_data.get("scalability_approach", ""),
                        "security_architecture": ts_data.get("security_architecture", ""),
                        "deployment_model": ts_data.get("deployment_model", ""),
                        "technical_volume": result.get("technical_volume", {}).get("sections", {}),
                    },
                )

                # Persist diagrams
                ArchitectureDiagram.objects.filter(technical_solution=ts).delete()
                for diag in result.get("diagrams", []):
                    ArchitectureDiagram.objects.create(
                        technical_solution=ts,
                        title=diag.get("title", "Diagram"),
                        diagram_type=diag.get("type", "system_context"),
                        mermaid_code=diag.get("mermaid", ""),
                        description=diag.get("description", ""),
                    )

                # Persist validation report
                vr = result.get("validation_report", {})
                if vr:
                    SolutionValidationReport.objects.update_or_create(
                        technical_solution=ts,
                        defaults={
                            "overall_quality": vr.get("overall_quality", "fair"),
                            "score": vr.get("score"),
                            "passed": vr.get("pass", False),
                            "issues": vr.get("issues", []),
                            "suggestions": vr.get("suggestions", []),
                            "compliance_gaps": vr.get("compliance_gaps", []),
                        },
                    )

                # Also persist technical volume sections as ProposalSection if proposal exists
                proposal = Proposal.objects.filter(deal=deal).first()
                if proposal and ts.technical_volume:
                    for i, (title, content) in enumerate(ts.technical_volume.items()):
                        ProposalSection.objects.update_or_create(
                            proposal=proposal,
                            volume="Volume I - Technical",
                            title=title,
                            defaults={
                                "section_number": f"1.{i + 1}",
                                "order": i,
                                "ai_draft": content,
                            },
                        )
            except Exception:
                pass  # Persisting is optional; don't fail the whole request

            return Response(result, status=status.HTTP_200_OK)

        except ImportError as exc:
            return Response(
                {"error": f"Solution Architect Agent not available: {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception("Solution Architect Agent failed for deal %s", pk)
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ── Task ViewSet ─────────────────────────────────────────


class TaskViewSet(viewsets.ModelViewSet):
    """
    CRUD for deal tasks.

    Supports filtering by deal, status, assigned_to, stage, and priority.
    """

    queryset = Task.objects.select_related("deal", "assigned_to")
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "status": ["exact", "in"],
        "assigned_to": ["exact"],
        "stage": ["exact"],
        "priority": ["exact", "lte", "gte"],
        "is_ai_generated": ["exact"],
        "due_date": ["lte", "gte"],
    }
    search_fields = ["title", "description"]
    ordering_fields = ["priority", "due_date", "created_at", "status"]
    ordering = ["priority", "due_date"]

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        """Mark a task as completed."""
        task = self.get_object()
        task.status = "completed"
        task.completed_at = timezone.now()
        task.save(update_fields=["status", "completed_at", "updated_at"])

        Activity.objects.create(
            deal=task.deal,
            actor=request.user,
            action="task_completed",
            description=f"Task '{task.title}' marked as completed",
            metadata={"task_id": str(task.id)},
        )

        return Response(TaskSerializer(task).data)


# ── Task Template ViewSet ────────────────────────────────


class TaskTemplateViewSet(viewsets.ModelViewSet):
    """CRUD for task templates (admin configuration)."""

    queryset = TaskTemplate.objects.all()
    serializer_class = TaskTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "stage": ["exact"],
        "is_required": ["exact"],
        "is_auto_completable": ["exact"],
    }
    ordering_fields = ["stage", "order"]
    ordering = ["stage", "order"]


# ── Approval ViewSet ─────────────────────────────────────


class ApprovalViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    List, create, and update approvals.

    Use the ``decide`` action to approve or reject.
    """

    queryset = Approval.objects.select_related(
        "deal", "requested_by", "requested_from"
    )
    serializer_class = ApprovalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "approval_type": ["exact"],
        "status": ["exact"],
        "requested_from": ["exact"],
        "requested_by": ["exact"],
    }
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="decide")
    def decide(self, request, pk=None):
        """Approve or reject an approval request."""
        approval = self.get_object()

        if approval.status != "pending":
            return Response(
                {"detail": "This approval has already been decided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approval.status = serializer.validated_data["status"]
        approval.decision_rationale = serializer.validated_data.get(
            "decision_rationale", ""
        )
        approval.decided_at = timezone.now()
        approval.save(
            update_fields=[
                "status",
                "decision_rationale",
                "decided_at",
                "updated_at",
            ]
        )

        action_verb = "approved" if approval.status == "approved" else "rejected"
        Activity.objects.create(
            deal=approval.deal,
            actor=request.user,
            action=f"approval_{action_verb}",
            description=(
                f"{approval.get_approval_type_display()} {action_verb} "
                f"by {request.user}"
            ),
            metadata={
                "approval_id": str(approval.id),
                "approval_type": approval.approval_type,
                "decision": approval.status,
            },
        )

        return Response(ApprovalSerializer(approval).data)


# ── Comment ViewSet ──────────────────────────────────────


class CommentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """List and create comments for deals."""

    queryset = Comment.objects.select_related("deal", "author")
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "author": ["exact"],
        "is_ai_generated": ["exact"],
    }
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# ── Activity ViewSet (read-only) ─────────────────────────


class ActivityViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only activity feed for deals."""

    queryset = Activity.objects.select_related("deal", "actor")
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "actor": ["exact"],
        "action": ["exact"],
        "is_ai_action": ["exact"],
    }
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
