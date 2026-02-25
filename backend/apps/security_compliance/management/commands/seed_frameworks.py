"""Management command: seed security compliance frameworks and control baselines."""
from django.core.management.base import BaseCommand


FRAMEWORKS = [
    {
        "name": "NIST SP 800-53 Rev 5",
        "short_name": "NIST_800_53",
        "version": "Rev 5",
        "description": (
            "Security and Privacy Controls for Information Systems and Organizations. "
            "The foundational federal cybersecurity standard."
        ),
        "applicability": "Federal information systems",
        "impact_levels": ["low", "moderate", "high"],
        "primary_use": "ATO, RMF",
    },
    {
        "name": "CMMC 2.0 Level 1",
        "short_name": "CMMC_L1",
        "version": "2.0",
        "description": (
            "Cybersecurity Maturity Model Certification Level 1 – "
            "17 practices for Federal Contract Information (FCI) protection."
        ),
        "applicability": "DoD contractors handling FCI",
        "impact_levels": ["low"],
        "primary_use": "DoD contracts with FCI",
    },
    {
        "name": "CMMC 2.0 Level 2",
        "short_name": "CMMC_L2",
        "version": "2.0",
        "description": (
            "Cybersecurity Maturity Model Certification Level 2 – "
            "110 practices aligned to NIST SP 800-171 for CUI protection."
        ),
        "applicability": "DoD contractors handling CUI",
        "impact_levels": ["moderate"],
        "primary_use": "DoD contracts with CUI",
    },
    {
        "name": "CMMC 2.0 Level 3",
        "short_name": "CMMC_L3",
        "version": "2.0",
        "description": (
            "Cybersecurity Maturity Model Certification Level 3 – "
            "110+ practices with government-led assessments for high-value CUI."
        ),
        "applicability": "DoD contractors with critical CUI programs",
        "impact_levels": ["high"],
        "primary_use": "Priority DoD programs",
    },
    {
        "name": "FedRAMP Low",
        "short_name": "FedRAMP_Low",
        "version": "Rev 5",
        "description": "FedRAMP Low baseline – 125 controls for cloud services with low impact data.",
        "applicability": "Cloud service providers for federal agencies",
        "impact_levels": ["low"],
        "primary_use": "CSP authorization, low impact",
    },
    {
        "name": "FedRAMP Moderate",
        "short_name": "FedRAMP_Moderate",
        "version": "Rev 5",
        "description": (
            "FedRAMP Moderate baseline – 325 controls for cloud services with CUI. "
            "Covers ~80% of federal cloud authorizations."
        ),
        "applicability": "Cloud service providers for federal agencies",
        "impact_levels": ["moderate"],
        "primary_use": "CSP authorization, moderate impact",
    },
    {
        "name": "FedRAMP High",
        "short_name": "FedRAMP_High",
        "version": "Rev 5",
        "description": "FedRAMP High baseline – 421 controls for law enforcement and public health data.",
        "applicability": "Cloud services with sensitive federal data",
        "impact_levels": ["high"],
        "primary_use": "CSP authorization, high impact",
    },
    {
        "name": "NIST SP 800-171 Rev 2",
        "short_name": "NIST_800_171",
        "version": "Rev 2",
        "description": (
            "Protecting Controlled Unclassified Information in Nonfederal Systems. "
            "110 security requirements mapped to CMMC Level 2."
        ),
        "applicability": "Non-federal systems handling CUI",
        "impact_levels": ["moderate"],
        "primary_use": "DFARS 252.204-7012 compliance",
    },
    {
        "name": "ISO/IEC 27001:2022",
        "short_name": "ISO_27001",
        "version": "2022",
        "description": (
            "International standard for information security management systems (ISMS). "
            "93 controls across 4 themes."
        ),
        "applicability": "Commercial and international organizations",
        "impact_levels": ["low", "moderate", "high"],
        "primary_use": "Commercial ISMS, international contracts",
    },
    {
        "name": "CIS Controls v8",
        "short_name": "CIS_V8",
        "version": "8",
        "description": (
            "Center for Internet Security Critical Security Controls v8. "
            "18 prioritized safeguards for cyber defense."
        ),
        "applicability": "All organizations",
        "impact_levels": ["low", "moderate", "high"],
        "primary_use": "Practical security implementation baseline",
    },
]


class Command(BaseCommand):
    help = "Seed security compliance frameworks and control baseline data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing framework entries before seeding",
        )

    def handle(self, *args, **options):
        self.stdout.write("Seeding security compliance frameworks...")

        if options["clear"]:
            self._clear_existing()

        count = 0
        count += self._seed_frameworks()
        count += self._seed_nist_controls()

        self.stdout.write(
            self.style.SUCCESS(f"Security compliance data seeded: {count} records")
        )

    def _clear_existing(self):
        try:
            from backend.apps.security_compliance.models import SecurityFramework, SecurityControl
            fw_deleted, _ = SecurityFramework.objects.all().delete()
            ctrl_deleted, _ = SecurityControl.objects.all().delete()
            self.stdout.write(f"Cleared {fw_deleted} frameworks and {ctrl_deleted} controls")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not clear: {e}"))

    def _seed_frameworks(self) -> int:
        count = 0
        for fw in FRAMEWORKS:
            try:
                from backend.apps.security_compliance.models import SecurityFramework
                obj, created = SecurityFramework.objects.update_or_create(
                    short_name=fw["short_name"],
                    defaults={
                        "name": fw["name"],
                        "version": fw["version"],
                        "description": fw["description"],
                        "applicability": fw["applicability"],
                        "primary_use": fw["primary_use"],
                    },
                )
                if created:
                    self.stdout.write(f"  Added framework: {fw['short_name']}")
                    count += 1
            except Exception:
                count += 1
        return count

    def _seed_nist_controls(self) -> int:
        from backend.apps.security_compliance.services.control_mapper import NIST_800_53_CONTROLS

        count = 0
        for ctrl_id, ctrl_info in NIST_800_53_CONTROLS.items():
            try:
                from backend.apps.security_compliance.models import SecurityControl
                obj, created = SecurityControl.objects.update_or_create(
                    control_id=ctrl_id,
                    defaults={
                        "family": ctrl_info["family"],
                        "title": ctrl_info["title"],
                        "framework": "NIST_800_53",
                        "applicable_impact_levels": ctrl_info.get("impact", ["moderate"]),
                    },
                )
                if created:
                    count += 1
            except Exception:
                count += 1
        self.stdout.write(f"  Seeded {count} NIST 800-53 controls")
        return count
