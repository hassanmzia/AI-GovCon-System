"""Seed security compliance frameworks and representative controls."""
from django.core.management.base import BaseCommand
from apps.security_compliance.models import SecurityFramework, SecurityControl


FRAMEWORKS = [
    {
        "name": "NIST SP 800-53",
        "version": "Rev 5",
        "description": (
            "Security and Privacy Controls for Information Systems and Organizations. "
            "The foundational federal cybersecurity standard required for ATO/RMF."
        ),
        "control_families": [
            "AC - Access Control", "AT - Awareness and Training",
            "AU - Audit and Accountability", "CA - Assessment, Authorization, and Monitoring",
            "CM - Configuration Management", "CP - Contingency Planning",
            "IA - Identification and Authentication", "IR - Incident Response",
            "MA - Maintenance", "MP - Media Protection", "PE - Physical and Environmental Protection",
            "PL - Planning", "PM - Program Management", "PS - Personnel Security",
            "PT - PII Processing and Transparency", "RA - Risk Assessment",
            "SA - System and Services Acquisition", "SC - System and Communications Protection",
            "SI - System and Information Integrity", "SR - Supply Chain Risk Management",
        ],
    },
    {
        "name": "CMMC 2.0 Level 1",
        "version": "2.0",
        "description": (
            "Cybersecurity Maturity Model Certification Level 1 — "
            "17 practices for Federal Contract Information (FCI) protection."
        ),
        "control_families": [
            "AC - Access Control", "IA - Identification and Authentication",
            "MP - Media Protection", "PE - Physical Protection",
            "SC - System and Communications Protection", "SI - System and Information Integrity",
        ],
    },
    {
        "name": "CMMC 2.0 Level 2",
        "version": "2.0",
        "description": (
            "Cybersecurity Maturity Model Certification Level 2 — "
            "110 practices aligned to NIST SP 800-171 for CUI protection."
        ),
        "control_families": [
            "AC - Access Control", "AT - Awareness and Training",
            "AU - Audit and Accountability", "CM - Configuration Management",
            "IA - Identification and Authentication", "IR - Incident Response",
            "MA - Maintenance", "MP - Media Protection",
            "PE - Physical Protection", "PS - Personnel Security",
            "RA - Risk Assessment", "SC - System and Communications Protection",
            "SI - System and Information Integrity", "CA - Security Assessment",
        ],
    },
    {
        "name": "FedRAMP Moderate",
        "version": "Rev 5",
        "description": (
            "FedRAMP Moderate baseline — 325 controls for cloud services with CUI. "
            "Covers ~80%% of federal cloud authorizations."
        ),
        "control_families": [
            "AC - Access Control", "AU - Audit and Accountability",
            "CA - Security Assessment", "CM - Configuration Management",
            "CP - Contingency Planning", "IA - Identification and Authentication",
            "IR - Incident Response", "MA - Maintenance",
            "PE - Physical and Environmental Protection", "PL - Planning",
            "PS - Personnel Security", "RA - Risk Assessment",
            "SA - System and Services Acquisition", "SC - System and Communications Protection",
            "SI - System and Information Integrity",
        ],
    },
    {
        "name": "FedRAMP High",
        "version": "Rev 5",
        "description": "FedRAMP High baseline — 421 controls for law enforcement and public health data.",
        "control_families": [
            "AC - Access Control", "AU - Audit and Accountability",
            "CA - Security Assessment", "CM - Configuration Management",
            "CP - Contingency Planning", "IA - Identification and Authentication",
            "IR - Incident Response", "MA - Maintenance",
            "PE - Physical and Environmental Protection", "PL - Planning",
            "PS - Personnel Security", "RA - Risk Assessment",
            "SA - System and Services Acquisition", "SC - System and Communications Protection",
            "SI - System and Information Integrity",
        ],
    },
    {
        "name": "NIST SP 800-171",
        "version": "Rev 2",
        "description": (
            "Protecting Controlled Unclassified Information in Nonfederal Systems. "
            "110 security requirements mapped to CMMC Level 2."
        ),
        "control_families": [
            "3.1 - Access Control", "3.2 - Awareness and Training",
            "3.3 - Audit and Accountability", "3.4 - Configuration Management",
            "3.5 - Identification and Authentication", "3.6 - Incident Response",
            "3.7 - Maintenance", "3.8 - Media Protection",
            "3.9 - Personnel Security", "3.10 - Physical Protection",
            "3.11 - Risk Assessment", "3.12 - Security Assessment",
            "3.13 - System and Communications Protection",
            "3.14 - System and Information Integrity",
        ],
    },
    {
        "name": "ISO/IEC 27001",
        "version": "2022",
        "description": (
            "International standard for information security management systems (ISMS). "
            "93 controls across 4 themes."
        ),
        "control_families": [
            "A.5 - Organizational Controls", "A.6 - People Controls",
            "A.7 - Physical Controls", "A.8 - Technological Controls",
        ],
    },
    {
        "name": "CIS Controls",
        "version": "v8",
        "description": (
            "Center for Internet Security Critical Security Controls v8. "
            "18 prioritized safeguards for cyber defense."
        ),
        "control_families": [
            "CIS 1 - Inventory and Control of Enterprise Assets",
            "CIS 2 - Inventory and Control of Software Assets",
            "CIS 3 - Data Protection",
            "CIS 4 - Secure Configuration of Enterprise Assets and Software",
            "CIS 5 - Account Management",
            "CIS 6 - Access Control Management",
            "CIS 7 - Continuous Vulnerability Management",
            "CIS 8 - Audit Log Management",
            "CIS 9 - Email and Web Browser Protections",
            "CIS 10 - Malware Defenses",
            "CIS 11 - Data Recovery",
            "CIS 12 - Network Infrastructure Management",
            "CIS 13 - Network Monitoring and Defense",
            "CIS 14 - Security Awareness and Skills Training",
            "CIS 15 - Service Provider Management",
            "CIS 16 - Application Software Security",
            "CIS 17 - Incident Response Management",
            "CIS 18 - Penetration Testing",
        ],
    },
]


# Representative NIST 800-53 controls (core controls across families)
NIST_CONTROLS = [
    ("AC-1", "Access Control Policy and Procedures", "AC - Access Control", "P1", "low", "Develop, document, and disseminate an access control policy and procedures."),
    ("AC-2", "Account Management", "AC - Access Control", "P1", "low", "Manage system accounts including establishing, activating, modifying, reviewing, disabling, and removing accounts."),
    ("AC-3", "Access Enforcement", "AC - Access Control", "P1", "low", "Enforce approved authorizations for logical access to information and system resources."),
    ("AC-4", "Information Flow Enforcement", "AC - Access Control", "P1", "moderate", "Enforce approved authorizations for controlling the flow of information within the system and between connected systems."),
    ("AC-5", "Separation of Duties", "AC - Access Control", "P1", "moderate", "Separate duties of individuals to prevent malevolent activity."),
    ("AC-6", "Least Privilege", "AC - Access Control", "P1", "moderate", "Employ the principle of least privilege."),
    ("AC-7", "Unsuccessful Logon Attempts", "AC - Access Control", "P1", "low", "Enforce a limit of consecutive invalid logon attempts by a user."),
    ("AC-8", "System Use Notification", "AC - Access Control", "P1", "low", "Display an approved system use notification message before granting access."),
    ("AC-17", "Remote Access", "AC - Access Control", "P1", "moderate", "Establish and document usage restrictions and implementation guidance for remote access."),
    ("AT-1", "Awareness and Training Policy", "AT - Awareness and Training", "P1", "low", "Develop, document, and disseminate a security awareness and training policy."),
    ("AT-2", "Literacy Training and Awareness", "AT - Awareness and Training", "P1", "low", "Provide security and privacy literacy training to system users."),
    ("AT-3", "Role-Based Training", "AT - Awareness and Training", "P1", "moderate", "Provide role-based security and privacy training to personnel with assigned security roles."),
    ("AU-1", "Audit and Accountability Policy", "AU - Audit and Accountability", "P1", "low", "Develop, document, and disseminate an audit and accountability policy."),
    ("AU-2", "Event Logging", "AU - Audit and Accountability", "P1", "low", "Identify events that the system is capable of logging in support of the audit function."),
    ("AU-3", "Content of Audit Records", "AU - Audit and Accountability", "P1", "low", "Ensure audit records contain sufficient information to establish what events occurred."),
    ("AU-6", "Audit Record Review, Analysis, and Reporting", "AU - Audit and Accountability", "P1", "moderate", "Review and analyze system audit records for indications of inappropriate activity."),
    ("AU-12", "Audit Record Generation", "AU - Audit and Accountability", "P1", "low", "Provide audit record generation capability for auditable events."),
    ("CA-1", "Assessment, Authorization, and Monitoring Policy", "CA - Assessment, Authorization, and Monitoring", "P1", "low", "Develop assessment, authorization, and monitoring policies."),
    ("CA-2", "Control Assessments", "CA - Assessment, Authorization, and Monitoring", "P2", "moderate", "Assess the security and privacy controls in the system."),
    ("CA-3", "Information Exchange", "CA - Assessment, Authorization, and Monitoring", "P1", "moderate", "Approve and manage the exchange of information between the system and other systems."),
    ("CM-1", "Configuration Management Policy", "CM - Configuration Management", "P1", "low", "Develop, document, and disseminate a configuration management policy."),
    ("CM-2", "Baseline Configuration", "CM - Configuration Management", "P1", "low", "Develop, document, and maintain a current baseline configuration of the system."),
    ("CM-6", "Configuration Settings", "CM - Configuration Management", "P1", "moderate", "Establish and document configuration settings for IT products using security configuration checklists."),
    ("CM-7", "Least Functionality", "CM - Configuration Management", "P1", "moderate", "Configure the system to provide only mission essential capabilities."),
    ("CM-8", "System Component Inventory", "CM - Configuration Management", "P1", "moderate", "Develop and document an inventory of system components."),
    ("CP-1", "Contingency Planning Policy", "CP - Contingency Planning", "P1", "low", "Develop, document, and disseminate a contingency planning policy."),
    ("CP-2", "Contingency Plan", "CP - Contingency Planning", "P1", "moderate", "Develop a contingency plan for the system that identifies essential mission functions."),
    ("CP-9", "System Backup", "CP - Contingency Planning", "P1", "moderate", "Conduct backups of user-level and system-level information."),
    ("IA-1", "Identification and Authentication Policy", "IA - Identification and Authentication", "P1", "low", "Develop, document, and disseminate identification and authentication policies."),
    ("IA-2", "Identification and Authentication (Organizational Users)", "IA - Identification and Authentication", "P1", "low", "Uniquely identify and authenticate organizational users."),
    ("IA-4", "Identifier Management", "IA - Identification and Authentication", "P1", "low", "Manage system identifiers by receiving authorization and issuing identifiers."),
    ("IA-5", "Authenticator Management", "IA - Identification and Authentication", "P1", "low", "Manage system authenticators by verifying identity before distribution."),
    ("IA-8", "Identification and Authentication (Non-Organizational Users)", "IA - Identification and Authentication", "P1", "moderate", "Uniquely identify and authenticate non-organizational users."),
    ("IR-1", "Incident Response Policy", "IR - Incident Response", "P1", "low", "Develop, document, and disseminate an incident response policy."),
    ("IR-2", "Incident Response Training", "IR - Incident Response", "P2", "moderate", "Provide incident response training to system users consistent with assigned roles."),
    ("IR-4", "Incident Handling", "IR - Incident Response", "P1", "moderate", "Implement an incident handling capability for incidents including preparation, detection, analysis, containment, eradication, and recovery."),
    ("IR-5", "Incident Monitoring", "IR - Incident Response", "P1", "moderate", "Track and document incidents on an ongoing basis."),
    ("IR-6", "Incident Reporting", "IR - Incident Response", "P1", "moderate", "Require personnel to report suspected incidents to the organizational incident response capability."),
    ("MA-1", "Maintenance Policy", "MA - Maintenance", "P1", "low", "Develop, document, and disseminate a system maintenance policy."),
    ("MA-2", "Controlled Maintenance", "MA - Maintenance", "P2", "moderate", "Schedule, document, and review records of maintenance and repairs on system components."),
    ("MP-1", "Media Protection Policy", "MP - Media Protection", "P1", "low", "Develop, document, and disseminate a media protection policy."),
    ("MP-2", "Media Access", "MP - Media Protection", "P1", "low", "Restrict access to digital and non-digital media to authorized individuals."),
    ("PE-1", "Physical and Environmental Protection Policy", "PE - Physical and Environmental Protection", "P1", "low", "Develop, document, and disseminate a physical and environmental protection policy."),
    ("PE-2", "Physical Access Authorizations", "PE - Physical and Environmental Protection", "P1", "low", "Develop, approve, and maintain a list of individuals with authorized access to the facility."),
    ("PE-3", "Physical Access Control", "PE - Physical and Environmental Protection", "P1", "low", "Enforce physical access authorizations at entry/exit points to the facility."),
    ("PL-1", "Planning Policy", "PL - Planning", "P1", "low", "Develop, document, and disseminate a planning policy."),
    ("PL-2", "System Security and Privacy Plans", "PL - Planning", "P1", "low", "Develop security and privacy plans for the system that describe the controls in place."),
    ("PS-1", "Personnel Security Policy", "PS - Personnel Security", "P1", "low", "Develop, document, and disseminate a personnel security policy."),
    ("PS-3", "Personnel Screening", "PS - Personnel Security", "P1", "low", "Screen individuals prior to authorizing access to the system."),
    ("RA-1", "Risk Assessment Policy", "RA - Risk Assessment", "P1", "low", "Develop, document, and disseminate a risk assessment policy."),
    ("RA-3", "Risk Assessment", "RA - Risk Assessment", "P1", "moderate", "Conduct a risk assessment to identify threats and vulnerabilities."),
    ("RA-5", "Vulnerability Monitoring and Scanning", "RA - Risk Assessment", "P1", "moderate", "Monitor and scan for vulnerabilities in the system."),
    ("SA-1", "System and Services Acquisition Policy", "SA - System and Services Acquisition", "P1", "low", "Develop, document, and disseminate a system and services acquisition policy."),
    ("SA-4", "Acquisition Process", "SA - System and Services Acquisition", "P1", "moderate", "Include security and privacy requirements in the acquisition process."),
    ("SC-1", "System and Communications Protection Policy", "SC - System and Communications Protection", "P1", "low", "Develop, document, and disseminate a system and communications protection policy."),
    ("SC-7", "Boundary Protection", "SC - System and Communications Protection", "P1", "moderate", "Monitor and control communications at the external managed interfaces to the system."),
    ("SC-8", "Transmission Confidentiality and Integrity", "SC - System and Communications Protection", "P1", "moderate", "Protect the confidentiality and integrity of transmitted information."),
    ("SC-12", "Cryptographic Key Establishment and Management", "SC - System and Communications Protection", "P1", "moderate", "Establish and manage cryptographic keys using automated mechanisms with supporting procedures."),
    ("SC-13", "Cryptographic Protection", "SC - System and Communications Protection", "P1", "moderate", "Implement cryptographic mechanisms to prevent unauthorized disclosure and modification of CUI."),
    ("SC-28", "Protection of Information at Rest", "SC - System and Communications Protection", "P1", "moderate", "Protect the confidentiality and integrity of information at rest."),
    ("SI-1", "System and Information Integrity Policy", "SI - System and Information Integrity", "P1", "low", "Develop, document, and disseminate a system and information integrity policy."),
    ("SI-2", "Flaw Remediation", "SI - System and Information Integrity", "P1", "low", "Identify, report, and correct system flaws."),
    ("SI-3", "Malicious Code Protection", "SI - System and Information Integrity", "P1", "low", "Implement malicious code protection mechanisms at entry and exit points."),
    ("SI-4", "System Monitoring", "SI - System and Information Integrity", "P1", "moderate", "Monitor the system to detect attacks, indicators of potential attacks, and unauthorized connections."),
    ("SI-5", "Security Alerts, Advisories, and Directives", "SI - System and Information Integrity", "P1", "moderate", "Receive system security alerts, advisories, and directives from external organizations on an ongoing basis."),
    ("SR-1", "Supply Chain Risk Management Policy", "SR - Supply Chain Risk Management", "P1", "moderate", "Develop a supply chain risk management policy and procedures."),
]


class Command(BaseCommand):
    help = "Seed security compliance frameworks and NIST 800-53 controls"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Clear existing frameworks and controls before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            ctrl_del, _ = SecurityControl.objects.all().delete()
            fw_del, _ = SecurityFramework.objects.all().delete()
            self.stdout.write(f"Cleared {fw_del} frameworks and {ctrl_del} controls")

        fw_created = 0
        for fw_data in FRAMEWORKS:
            _, created = SecurityFramework.objects.update_or_create(
                name=fw_data["name"],
                version=fw_data["version"],
                defaults={
                    "description": fw_data["description"],
                    "control_families": fw_data["control_families"],
                    "is_active": True,
                },
            )
            if created:
                fw_created += 1

        # Seed NIST 800-53 controls
        nist_fw = SecurityFramework.objects.filter(name="NIST SP 800-53").first()
        ctrl_created = 0
        if nist_fw:
            for ctrl_id, title, family, priority, baseline, desc in NIST_CONTROLS:
                _, created = SecurityControl.objects.update_or_create(
                    framework=nist_fw,
                    control_id=ctrl_id,
                    defaults={
                        "title": title,
                        "family": family,
                        "priority": priority,
                        "baseline_impact": baseline,
                        "description": desc,
                        "implementation_guidance": "",
                    },
                )
                if created:
                    ctrl_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Frameworks: {fw_created} created ({len(FRAMEWORKS)} total). "
            f"Controls: {ctrl_created} created ({len(NIST_CONTROLS)} total)."
        ))
