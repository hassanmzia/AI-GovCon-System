import logging

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.deals.models import (
    Activity,
    AgencyContact,
    AgencyInteraction,
    Approval,
    CapturePlan,
    Comment,
    Deal,
    DealStageHistory,
    GateReviewCriteria,
    Stakeholder,
    Task,
    TaskTemplate,
)
from apps.deals.serializers import (
    ActivitySerializer,
    AgencyContactSerializer,
    AgencyInteractionSerializer,
    ApprovalDecisionSerializer,
    ApprovalSerializer,
    CapturePlanSerializer,
    CommentSerializer,
    DealCreateSerializer,
    DealDetailSerializer,
    DealListSerializer,
    DealStageHistorySerializer,
    DealTransitionSerializer,
    GateEvaluationSerializer,
    GateReviewCriteriaSerializer,
    StakeholderSerializer,
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

    def perform_create(self, serializer):
        deal = serializer.save(owner=self.request.user)
        # Emit deal.created event to AI orchestrator via Redis
        try:
            from apps.deals.signals import on_deal_created
            on_deal_created(
                deal_id=str(deal.id),
                opportunity_id=str(deal.opportunity_id) if deal.opportunity_id else "",
                user_id=self.request.user.id,
            )
        except Exception:
            logger.warning(
                "Failed to emit deal.created signal for deal %s",
                deal.id,
                exc_info=True,
            )
        # Auto-generate stage tasks for initial stage
        try:
            from apps.deals.tasks import auto_generate_stage_tasks
            auto_generate_stage_tasks.delay(str(deal.id), deal.stage)
        except Exception:
            logger.warning(
                "Failed to enqueue auto_generate_stage_tasks for deal %s",
                deal.id,
                exc_info=True,
            )

    # ── Custom actions ───────────────────────────────────

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        """Advance or move a deal to a new pipeline stage.

        For HITL gate stages (bid_no_bid, final_review, submit, contract_setup),
        auto-creates an approved Approval record when the user explicitly
        triggers the transition — the user clicking the button IS the human
        approval.
        """
        from apps.deals.workflow import HITL_GATES

        deal = self.get_object()
        serializer = DealTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        engine = WorkflowEngine()
        target = serializer.validated_data["target_stage"]
        reason = serializer.validated_data.get("reason", "")

        # Auto-create approval for HITL gates if none exists yet
        if target in HITL_GATES:
            has_approval = deal.approvals.filter(
                approval_type=target,
                status__in=["pending", "approved"],
            ).exists()
            if not has_approval:
                Approval.objects.create(
                    deal=deal,
                    approval_type=target,
                    requested_by=request.user,
                    requested_from=request.user,
                    status="approved",
                    decision_rationale=reason or "Approved via stage transition",
                    decided_at=timezone.now(),
                )

        try:
            engine.transition(deal, target, user=request.user, reason=reason)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as exc:
            logger.exception(
                "Unexpected error transitioning deal %s to %s", pk, target
            )
            return Response(
                {"detail": f"Transition failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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

    @action(detail=True, methods=["get"], url_path="evaluate-gate")
    def evaluate_gate(self, request, pk=None):
        """Evaluate gate readiness criteria for the deal's next stage transition."""
        deal = self.get_object()
        target_stage = request.query_params.get("target_stage", "")

        if not target_stage:
            # Infer next stage from current stage
            from apps.deals.workflow import VALID_TRANSITIONS
            targets = VALID_TRANSITIONS.get(deal.stage, [])
            target_stage = targets[0] if targets else deal.stage

        engine = WorkflowEngine()
        evaluation = engine.evaluate_gate(deal, target_stage)
        return Response(evaluation)

    @action(detail=True, methods=["get"], url_path="capture-plan")
    def get_capture_plan(self, request, pk=None):
        """Get the capture plan for this deal."""
        deal = self.get_object()
        try:
            plan = CapturePlan.objects.get(deal=deal)
            return Response(CapturePlanSerializer(plan).data)
        except CapturePlan.DoesNotExist:
            return Response(
                {"detail": "No capture plan exists for this deal."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["patch"], url_path="capture-plan")
    def update_capture_plan(self, request, pk=None):
        """Update the capture plan for this deal."""
        deal = self.get_object()
        plan, _ = CapturePlan.objects.get_or_create(deal=deal)
        serializer = CapturePlanSerializer(plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="artifacts")
    def artifacts(self, request, pk=None):
        """Return a summary of all pipeline artifacts linked to this deal."""
        deal = self.get_object()
        result = {}

        # Opportunity Score
        try:
            from apps.opportunities.models import OpportunityScore
            score = OpportunityScore.objects.filter(
                opportunity=deal.opportunity
            ).first()
            result["opportunity_score"] = {
                "total_score": score.total_score,
                "recommendation": score.recommendation,
            } if score else None
        except Exception:
            result["opportunity_score"] = None

        # Technical Solution
        try:
            from apps.proposals.models import TechnicalSolution
            ts = TechnicalSolution.objects.filter(deal=deal).first()
            result["technical_solution"] = {
                "id": str(ts.id),
                "executive_summary": ts.executive_summary[:200] if ts.executive_summary else "",
                "architecture_pattern": ts.architecture_pattern,
                "diagram_count": ts.diagrams.count(),
            } if ts else None
        except Exception:
            result["technical_solution"] = None

        # Pricing
        try:
            from apps.pricing.models import CostModel, PricingScenario
            scenarios = PricingScenario.objects.filter(deal=deal)
            recommended = scenarios.filter(is_recommended=True).first()
            cost_model = CostModel.objects.filter(deal=deal).order_by("-version").first()
            result["pricing"] = {
                "scenario_count": scenarios.count(),
                "recommended": {
                    "name": recommended.name,
                    "total_price": str(recommended.total_price),
                    "margin_pct": recommended.margin_pct,
                    "probability_of_win": recommended.probability_of_win,
                } if recommended else None,
                "cost_model": {
                    "total_cost": str(cost_model.total_cost),
                    "direct_labor": str(cost_model.direct_labor),
                } if cost_model else None,
            } if scenarios.exists() else None
        except Exception:
            result["pricing"] = None

        # Proposal
        try:
            from apps.proposals.models import Proposal
            proposal = Proposal.objects.filter(deal=deal).first()
            result["proposal"] = {
                "id": str(proposal.id),
                "title": proposal.title,
                "status": proposal.status,
                "section_count": proposal.sections.count(),
            } if proposal else None
        except Exception:
            result["proposal"] = None

        # Pricing Volume
        try:
            from apps.pricing.models import PricingVolume
            pv = PricingVolume.objects.filter(deal=deal).first()
            result["pricing_volume"] = {
                "id": str(pv.id),
                "status": pv.status,
                "total_price": str(pv.total_price),
            } if pv else None
        except Exception:
            result["pricing_volume"] = None

        return Response(result)

    @action(detail=True, methods=["post"], url_path="rescore")
    def rescore(self, request, pk=None):
        """Trigger (re-)scoring of the deal's opportunity and update deal fields."""
        deal = self.get_object()
        from apps.deals.tasks import auto_score_opportunity
        auto_score_opportunity.delay(str(deal.id))
        return Response({"detail": "Scoring queued"}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"], url_path="run-solution-architect")
    def run_solution_architect(self, request, pk=None):
        """Trigger the Solution Architect Agent for this deal.

        Calls the AI Orchestrator service which runs the full 9-node
        LangGraph pipeline, then persists results to Django models.
        """
        import os
        import time

        import httpx

        deal = self.get_object()
        orchestrator_url = os.getenv(
            "AI_ORCHESTRATOR_URL", "http://ai-orchestrator:8003"
        )

        try:
            client = httpx.Client(timeout=30)

            # 1. Kick off the agent run via the AI Orchestrator service
            start_resp = client.post(
                f"{orchestrator_url}/ai/agents/solution-architect/run",
                json={
                    "deal_id": str(deal.id),
                    "opportunity_id": str(deal.opportunity_id),
                },
            )
            start_resp.raise_for_status()
            run_data = start_resp.json()
            run_id = run_data["run_id"]

            # 2. Poll for completion (the agent pipeline can take 30-120s)
            max_wait = 180  # seconds
            poll_interval = 3  # seconds
            elapsed = 0
            result = None

            while elapsed < max_wait:
                time.sleep(poll_interval)
                elapsed += poll_interval

                poll_resp = client.get(
                    f"{orchestrator_url}/ai/agents/runs/{run_id}",
                )
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()

                if poll_data["status"] == "completed":
                    result = poll_data.get("result", {})
                    break
                elif poll_data["status"] == "failed":
                    error_msg = poll_data.get("result", {}).get(
                        "error", "Agent run failed"
                    )
                    # Return 402 for credit/billing errors so frontend can show
                    # a specific message directing the user to Settings
                    error_lower = error_msg.lower()
                    if "credit" in error_lower or "billing" in error_lower or "quota" in error_lower:
                        return Response(
                            {
                                "error": error_msg,
                                "error_type": "llm_credit_error",
                                "action": "Please add API credits or switch to a different LLM provider in Settings.",
                            },
                            status=status.HTTP_402_PAYMENT_REQUIRED,
                        )
                    if "api key" in error_lower or "authentication" in error_lower:
                        return Response(
                            {
                                "error": error_msg,
                                "error_type": "llm_auth_error",
                                "action": "Please check your API key or switch to a different LLM provider in Settings.",
                            },
                            status=status.HTTP_401_UNAUTHORIZED,
                        )
                    return Response(
                        {"error": error_msg},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            client.close()

            if result is None:
                return Response(
                    {"error": "Solution Architect Agent timed out after 180 seconds"},
                    status=status.HTTP_504_GATEWAY_TIMEOUT,
                )

            # 3. Persist the solution as TechnicalSolution + ArchitectureDiagram models
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

        except httpx.ConnectError:
            return Response(
                {"error": "AI Orchestrator service is not reachable. Please ensure it is running."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except httpx.HTTPStatusError as exc:
            logger.exception("AI Orchestrator returned an error for deal %s", pk)
            return Response(
                {"error": f"AI Orchestrator error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
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


# ── Agency Contact ViewSet ──────────────────────────────


class AgencyContactViewSet(viewsets.ModelViewSet):
    """CRUD for agency contacts on deals."""

    queryset = AgencyContact.objects.select_related("deal").prefetch_related(
        "interactions"
    )
    serializer_class = AgencyContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "contact_type": ["exact"],
        "relationship_strength": ["exact", "gte"],
    }
    search_fields = ["name", "title", "agency", "office"]
    ordering_fields = ["relationship_strength", "created_at"]
    ordering = ["-relationship_strength"]


# ── Agency Interaction ViewSet ──────────────────────────


class AgencyInteractionViewSet(viewsets.ModelViewSet):
    """CRUD for agency interactions (meetings, emails, etc.)."""

    queryset = AgencyInteraction.objects.select_related("contact", "deal", "logged_by")
    serializer_class = AgencyInteractionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "contact": ["exact"],
        "deal": ["exact"],
        "interaction_type": ["exact"],
    }
    ordering_fields = ["date", "created_at"]
    ordering = ["-date"]

    def perform_create(self, serializer):
        serializer.save(logged_by=self.request.user)


# ── Stakeholder ViewSet ─────────────────────────────────


class StakeholderViewSet(viewsets.ModelViewSet):
    """CRUD for deal stakeholder mapping."""

    queryset = Stakeholder.objects.select_related("deal")
    serializer_class = StakeholderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "influence_level": ["exact"],
        "disposition": ["exact"],
    }
    search_fields = ["name", "title", "organization"]
    ordering_fields = ["influence_level", "created_at"]
    ordering = ["-influence_level"]


# ── Gate Review Criteria ViewSet ────────────────────────


class GateReviewCriteriaViewSet(viewsets.ModelViewSet):
    """CRUD for gate review criteria (admin configuration)."""

    queryset = GateReviewCriteria.objects.all()
    serializer_class = GateReviewCriteriaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {"stage": ["exact"], "is_critical": ["exact"]}
    ordering_fields = ["stage", "order"]
    ordering = ["stage", "order"]
