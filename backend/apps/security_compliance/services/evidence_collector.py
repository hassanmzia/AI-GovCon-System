"""
Automated Evidence Collection Service.

Gathers compliance evidence from integrated systems to support
continuous ATO (Authority to Operate) monitoring.
"""

import logging
from datetime import datetime

from django.utils import timezone

logger = logging.getLogger(__name__)


class EvidenceCollector:
    """
    Collects evidence for security control compliance.

    Evidence sources:
    - System configurations (from deployment records)
    - Access control logs (from audit trail)
    - Training records (from workforce module)
    - Vulnerability scan results (external integration)
    - Change management records (from contract modifications)
    """

    def collect_for_contract(self, contract_id: str) -> list[dict]:
        """
        Collect all available evidence for a contract's security controls.

        Returns list of evidence items with control mapping.
        """
        evidence = []

        # 1. Audit trail evidence
        evidence.extend(self._collect_audit_evidence(contract_id))

        # 2. Personnel/clearance evidence
        evidence.extend(self._collect_personnel_evidence(contract_id))

        # 3. Document/policy evidence
        evidence.extend(self._collect_document_evidence(contract_id))

        # 4. Change management evidence
        evidence.extend(self._collect_change_evidence(contract_id))

        logger.info(
            "Collected %d evidence items for contract %s",
            len(evidence), contract_id,
        )
        return evidence

    def _collect_audit_evidence(self, contract_id: str) -> list[dict]:
        """Collect evidence from audit logs."""
        from apps.core.models import AuditLog

        now = timezone.now()
        thirty_days_ago = now - timezone.timedelta(days=30)

        logs = AuditLog.objects.filter(
            entity_type__in=["contract", "deal"],
            entity_id=contract_id,
            timestamp__gte=thirty_days_ago,
        ).count()

        return [{
            "evidence_type": "audit_trail",
            "control_family": "AU",  # NIST AU family
            "description": f"Audit logging active: {logs} events in last 30 days",
            "status": "collected" if logs > 0 else "gap",
            "collected_at": now.isoformat(),
            "details": {"event_count": logs, "period_days": 30},
        }]

    def _collect_personnel_evidence(self, contract_id: str) -> list[dict]:
        """Collect evidence about personnel security."""
        evidence = []

        try:
            from apps.workforce.models import Assignment, Employee

            active_assignments = Assignment.objects.filter(
                contract_id=contract_id,
                is_active=True,
            ).select_related("employee")

            for assignment in active_assignments:
                emp = assignment.employee
                clearance_ok = emp.clearance_status == "active"
                evidence.append({
                    "evidence_type": "personnel_clearance",
                    "control_family": "PS",  # NIST PS family
                    "description": (
                        f"{emp.name}: clearance {emp.clearance_type} — "
                        f"{'Active' if clearance_ok else 'ISSUE: ' + emp.clearance_status}"
                    ),
                    "status": "collected" if clearance_ok else "gap",
                    "collected_at": timezone.now().isoformat(),
                    "details": {
                        "employee_id": str(emp.id),
                        "clearance_type": emp.clearance_type,
                        "clearance_status": emp.clearance_status,
                    },
                })
        except Exception:
            logger.debug("Workforce module not available for evidence collection")

        return evidence

    def _collect_document_evidence(self, contract_id: str) -> list[dict]:
        """Collect evidence from knowledge vault documents."""
        evidence = []

        try:
            from apps.knowledge_vault.models import KnowledgeDocument

            docs = KnowledgeDocument.objects.filter(
                category__in=["security_plan", "ssp", "poam", "ato_package"],
            ).order_by("-created_at")[:10]

            for doc in docs:
                evidence.append({
                    "evidence_type": "documentation",
                    "control_family": "PL",  # NIST PL family
                    "description": f"Document: {doc.title}",
                    "status": "collected",
                    "collected_at": timezone.now().isoformat(),
                    "details": {
                        "document_id": str(doc.id),
                        "category": doc.category,
                        "last_updated": doc.updated_at.isoformat() if doc.updated_at else "",
                    },
                })
        except Exception:
            logger.debug("Knowledge vault not available for evidence collection")

        return evidence

    def _collect_change_evidence(self, contract_id: str) -> list[dict]:
        """Collect evidence from contract modifications (change management)."""
        evidence = []

        try:
            from apps.contracts.models import ContractModification

            mods = ContractModification.objects.filter(
                contract_id=contract_id,
            ).order_by("-created_at")[:10]

            evidence.append({
                "evidence_type": "change_management",
                "control_family": "CM",  # NIST CM family
                "description": f"{mods.count()} contract modifications tracked",
                "status": "collected",
                "collected_at": timezone.now().isoformat(),
                "details": {"modification_count": mods.count()},
            })
        except Exception:
            logger.debug("Contracts module not available for evidence collection")

        return evidence
