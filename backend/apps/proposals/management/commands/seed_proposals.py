"""Seed realistic proposal data with sections, review cycles, and templates."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.deals.models import Deal
from apps.proposals.models import (
    Proposal,
    ProposalSection,
    ProposalTemplate,
    ReviewCycle,
)


TEMPLATES = [
    {
        "name": "Standard Federal Proposal (L/M/N)",
        "description": "Standard 3-volume proposal structure following FAR 15.2 format with Technical, Management, and Past Performance volumes plus Price volume.",
        "is_default": True,
        "volumes": [
            {
                "volume_name": "Volume I - Technical Approach",
                "sections": [
                    {"name": "Executive Summary", "description": "High-level overview of proposed solution and key differentiators", "page_limit": 3},
                    {"name": "Technical Understanding", "description": "Demonstrate understanding of agency requirements and mission context", "page_limit": 5},
                    {"name": "Technical Approach", "description": "Detailed solution architecture, methodology, and implementation plan", "page_limit": 15},
                    {"name": "Staffing Plan", "description": "Key personnel qualifications, organizational chart, and staffing approach", "page_limit": 8},
                    {"name": "Transition Plan", "description": "Approach for transitioning from incumbent, knowledge transfer, and Phase-In", "page_limit": 5},
                    {"name": "Quality Assurance", "description": "Quality management approach, metrics, and continuous improvement processes", "page_limit": 4},
                    {"name": "Risk Management", "description": "Risk identification, mitigation strategies, and contingency planning", "page_limit": 3},
                    {"name": "Security Approach", "description": "Cybersecurity framework, compliance approach, and security controls", "page_limit": 4},
                ],
            },
            {
                "volume_name": "Volume II - Management Approach",
                "sections": [
                    {"name": "Management Philosophy", "description": "Organizational management approach and governance structure", "page_limit": 3},
                    {"name": "Program Management", "description": "Program management methodology, reporting, and stakeholder communication", "page_limit": 5},
                    {"name": "Contract Management", "description": "Contract administration, deliverable management, and performance monitoring", "page_limit": 3},
                    {"name": "Communication Plan", "description": "Stakeholder engagement, status reporting, and escalation procedures", "page_limit": 3},
                ],
            },
            {
                "volume_name": "Volume III - Past Performance",
                "sections": [
                    {"name": "Past Performance Summary", "description": "Overview of relevant contract experience demonstrating capability", "page_limit": 2},
                    {"name": "Contract Reference 1", "description": "Detailed past performance reference with relevance mapping", "page_limit": 3},
                    {"name": "Contract Reference 2", "description": "Detailed past performance reference with relevance mapping", "page_limit": 3},
                    {"name": "Contract Reference 3", "description": "Detailed past performance reference with relevance mapping", "page_limit": 3},
                ],
            },
            {
                "volume_name": "Volume IV - Price/Cost",
                "sections": [
                    {"name": "Pricing Narrative", "description": "Basis of estimate, pricing methodology, and cost assumptions", "page_limit": 5},
                    {"name": "Rate Justification", "description": "Labor rate justification and market comparisons", "page_limit": 3},
                ],
            },
        ],
    },
    {
        "name": "IDIQ Task Order Response",
        "description": "Streamlined task order response for IDIQ vehicles like OASIS+, Alliant 2, or CIO-SP3.",
        "is_default": False,
        "volumes": [
            {
                "volume_name": "Technical Volume",
                "sections": [
                    {"name": "Technical Approach", "description": "Solution approach tailored to task order requirements", "page_limit": 10},
                    {"name": "Key Personnel", "description": "Proposed key personnel with qualifications and availability", "page_limit": 5},
                    {"name": "Management Approach", "description": "Task order management, performance metrics, and reporting", "page_limit": 5},
                    {"name": "Transition/Phase-In", "description": "30/60/90 day transition plan with minimal disruption", "page_limit": 3},
                ],
            },
            {
                "volume_name": "Past Performance",
                "sections": [
                    {"name": "Relevant Experience", "description": "Past performance on similar task orders or programs", "page_limit": 5},
                ],
            },
            {
                "volume_name": "Price Volume",
                "sections": [
                    {"name": "Price Narrative", "description": "Pricing approach and basis of estimate for task order scope", "page_limit": 3},
                ],
            },
        ],
    },
]


# Sample section content for a realistic proposal
SECTION_CONTENT = {
    "Executive Summary": {
        "ai_draft": """Our team brings over 15 years of proven experience delivering mission-critical IT modernization solutions to federal agencies. We understand that the Department of Homeland Security requires a partner who can not only modernize legacy systems but do so while maintaining zero downtime for mission-critical operations.

Our proposed solution leverages a cloud-native microservices architecture deployed on AWS GovCloud, fully compliant with FedRAMP High and aligned with CISA's Zero Trust Maturity Model. We will deliver a phased migration approach that reduces operational risk while accelerating time-to-value.

**Key Differentiators:**
- Proven track record: Successfully migrated 3 similar federal systems with zero unplanned downtime
- Cleared workforce: 100% of proposed key personnel hold active TS/SCI clearances
- Accelerated delivery: Our proprietary migration framework reduces typical timelines by 30%
- Cost savings: Our approach delivers 22% lifecycle cost reduction through cloud optimization

We are committed to a seamless transition, maintaining full operational capability throughout the migration, and delivering measurable improvements within the first 90 days of contract award.""",
        "human_content": "",
        "final_content": "",
        "status": "ai_drafted",
        "word_count": 172,
    },
    "Technical Understanding": {
        "ai_draft": """DHS currently operates a heterogeneous IT environment comprising legacy on-premises systems, partial cloud deployments, and custom-built applications supporting border security, cybersecurity, and immigration processing missions. The current infrastructure faces several critical challenges:

1. **Scalability Limitations**: Peak processing periods (e.g., seasonal immigration surges) cause system degradation
2. **Security Posture Gaps**: Legacy systems cannot support zero trust architecture requirements per EO 14028
3. **Operational Inefficiency**: Manual processes and system silos result in duplicated effort across components
4. **Compliance Burden**: Maintaining ATO across disparate systems consumes 40% of ISSO staff capacity

We recognize that modernization must proceed without disrupting the 24/7 operational tempo of DHS component agencies. Our approach addresses each of these challenges through a systematic, risk-managed transformation that prioritizes mission continuity above all else.

Our team has direct experience with DHS component systems through prior contracts with CBP and ICE, giving us unique insight into the operational requirements, data classification challenges, and stakeholder dynamics of this modernization effort.""",
        "human_content": """DHS currently operates a complex IT environment that supports critical national security missions across multiple component agencies. Our team has spent the past three months conducting deep analysis of the current state architecture, interviewing stakeholders, and mapping dependencies.

The key challenges we've identified include scalability during peak operational periods, security gaps that prevent full zero trust implementation, and operational inefficiencies from system fragmentation.

Our understanding is informed by direct experience on DHS programs including our CBP Modernization contract (2022-2025) and ICE Case Management System integration (2023-present). This gives us unique insight into both the technical landscape and the mission-critical nature of every system change.""",
        "final_content": "",
        "status": "in_review",
        "word_count": 245,
    },
    "Technical Approach": {
        "ai_draft": """## 1. Solution Architecture Overview

Our proposed solution implements a cloud-native microservices architecture on AWS GovCloud (US-East), designed for FedRAMP High authorization and full zero trust compliance.

### 1.1 Architecture Principles
- **Cloud-Native First**: All new services built as containerized microservices using Kubernetes (EKS)
- **API-Driven Integration**: RESTful and event-driven APIs enable seamless interoperability
- **Zero Trust by Design**: Every service-to-service communication authenticated and encrypted
- **Resilience Engineering**: Multi-AZ deployment with automated failover and self-healing

### 1.2 Core Technology Stack
| Layer | Technology | Justification |
|-------|-----------|---------------|
| Compute | AWS EKS (Kubernetes) | Container orchestration at scale |
| Data | Amazon RDS (PostgreSQL), DynamoDB | Relational + NoSQL for diverse workloads |
| Messaging | Amazon MSK (Kafka) | Event-driven architecture backbone |
| Security | AWS KMS, Secrets Manager, IAM | Encryption and identity management |
| Monitoring | Datadog Federal, CloudWatch | Comprehensive observability |

### 1.3 Migration Strategy

We employ a 4-phase migration approach:

**Phase 1: Assessment & Planning (Months 1-2)**
- Complete application portfolio analysis using our proprietary Migration Readiness Assessment tool
- Classify applications into 6Rs: Rehost, Replatform, Refactor, Repurchase, Retire, Retain
- Develop detailed migration runbooks for each application

**Phase 2: Foundation (Months 2-4)**
- Establish AWS GovCloud landing zone with multi-account structure
- Implement CI/CD pipelines with security scanning gates
- Deploy zero trust network architecture (ZTNA)

**Phase 3: Migration Execution (Months 4-12)**
- Execute migration waves of 3-5 applications per sprint
- Automated testing and validation at each stage
- Parallel run period for critical systems (minimum 30 days)

**Phase 4: Optimization (Months 12-14)**
- Performance tuning and cost optimization
- Knowledge transfer to government staff
- Establish steady-state operations and SLA monitoring""",
        "human_content": "",
        "final_content": "",
        "status": "ai_drafted",
        "word_count": 850,
    },
    "Staffing Plan": {
        "ai_draft": """## Key Personnel

### Program Manager - Sarah Chen, PMP, CISSP
- 18 years of federal IT program management experience
- Led $120M DHS modernization program (2020-2024)
- Active TS/SCI clearance
- PMP, CISSP, AWS Solutions Architect Professional certified

### Technical Lead - Dr. James Rodriguez
- 15 years of cloud architecture and migration experience
- Designed and deployed 12 FedRAMP High cloud environments
- Active TS clearance
- AWS DevOps Professional, Kubernetes Administrator (CKA)

### Security Architect - Maria Thompson, CISSP, CISM
- 12 years of federal cybersecurity experience
- Implemented zero trust architectures for 3 federal agencies
- Active TS/SCI clearance
- CISSP, CISM, CompTIA CASP+ certified

## Organizational Structure

Our team is organized into four functional areas reporting to the Program Manager:
1. **Cloud Engineering** (8 engineers) - Infrastructure and migration execution
2. **Application Development** (6 developers) - Refactoring and API development
3. **Security & Compliance** (4 specialists) - Ongoing ATO and zero trust
4. **Program Operations** (3 staff) - PMO, reporting, and quality assurance""",
        "human_content": "",
        "final_content": "",
        "status": "ai_drafted",
        "word_count": 420,
    },
    "Transition Plan": {
        "ai_draft": "",
        "human_content": "",
        "final_content": "",
        "status": "not_started",
        "word_count": 0,
    },
    "Quality Assurance": {
        "ai_draft": "",
        "human_content": "",
        "final_content": "",
        "status": "not_started",
        "word_count": 0,
    },
    "Risk Management": {
        "ai_draft": """## Risk Management Framework

We employ a structured risk management approach aligned with PMBOK and NIST SP 800-30:

### Risk Identification & Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| Data loss during migration | Low | Critical | Automated backup verification, parallel run, rollback procedures |
| Schedule delay from legacy complexity | Medium | High | 30% schedule buffer, sprint-based flexibility |
| Key personnel turnover | Low | High | Cross-training, knowledge base, 2-deep staffing |
| Security incident during transition | Low | Critical | Continuous monitoring, incident response team on standby |
| Vendor lock-in | Medium | Medium | Multi-cloud compatible design patterns, infrastructure as code |

### Risk Monitoring Process
- Weekly risk register review at PMO level
- Monthly risk board with government stakeholders
- Automated risk indicators from CI/CD pipeline metrics
- Quarterly risk posture assessment with updated mitigation plans""",
        "human_content": "",
        "final_content": "",
        "status": "ai_drafted",
        "word_count": 310,
    },
    "Security Approach": {
        "ai_draft": "",
        "human_content": "",
        "final_content": "",
        "status": "not_started",
        "word_count": 0,
    },
    "Management Philosophy": {
        "ai_draft": """Our management philosophy centers on three pillars: Transparency, Agility, and Accountability.

**Transparency**: We believe the government should never be surprised. Our real-time dashboards, weekly status reports, and open-door policy ensure full visibility into program health, risks, and progress.

**Agility**: We employ a hybrid Agile/traditional project management approach that provides the structure and oversight federal programs require while maintaining the flexibility to adapt to evolving requirements. Our two-week sprint cycles allow us to demonstrate progress continuously.

**Accountability**: Every deliverable has a named owner, every metric has a target, and every commitment has a deadline. Our governance structure ensures clear escalation paths and rapid decision-making.""",
        "human_content": "",
        "final_content": "",
        "status": "ai_drafted",
        "word_count": 120,
    },
    "Program Management": {
        "ai_draft": "",
        "human_content": "",
        "final_content": "",
        "status": "not_started",
        "word_count": 0,
    },
    "Contract Management": {
        "ai_draft": "",
        "human_content": "",
        "final_content": "",
        "status": "not_started",
        "word_count": 0,
    },
    "Communication Plan": {
        "ai_draft": "",
        "human_content": "",
        "final_content": "",
        "status": "not_started",
        "word_count": 0,
    },
    "Past Performance Summary": {
        "ai_draft": """Our team has a strong track record of delivering IT modernization and cloud migration programs for federal agencies. Below we highlight three directly relevant contracts that demonstrate our capability to execute the DHS modernization program successfully.

Each reference was selected based on relevance to the current requirement in terms of:
- Technical scope (cloud migration, modernization)
- Agency complexity (multi-component, high security)
- Contract size and structure (similar magnitude and type)
- Recency (all within the past 5 years)

All contracts were completed on time and within budget, with customer satisfaction ratings of "Exceptional" or "Very Good" on all CPARS evaluations.""",
        "human_content": "",
        "final_content": "",
        "status": "ai_drafted",
        "word_count": 108,
    },
    "Contract Reference 1": {
        "ai_draft": """**Contract Title**: CBP Cloud Modernization Program
**Agency**: U.S. Customs and Border Protection (CBP)
**Contract Number**: HSHQDC-20-C-00142
**Period of Performance**: October 2020 – September 2024
**Contract Value**: $87.5M (CPFF)
**Key Personnel**: Sarah Chen (Program Manager)

**Relevance**: This contract involved modernizing CBP's legacy case management and traveler processing systems to AWS GovCloud, directly analogous to the current DHS requirement.

**Scope & Achievements**:
- Migrated 47 applications from on-premises data centers to AWS GovCloud
- Achieved FedRAMP High ATO in 6 months (vs. typical 12-18 months)
- Reduced infrastructure costs by 34% through right-sizing and reserved instances
- Implemented zero trust architecture across all migrated systems
- Zero unplanned downtime during migration of 24/7 operational systems
- 99.99% availability achieved during steady-state operations

**CPARS Rating**: Exceptional (Overall)""",
        "human_content": "",
        "final_content": "",
        "status": "ai_drafted",
        "word_count": 160,
    },
    "Contract Reference 2": {
        "ai_draft": "",
        "human_content": "",
        "final_content": "",
        "status": "not_started",
        "word_count": 0,
    },
    "Contract Reference 3": {
        "ai_draft": "",
        "human_content": "",
        "final_content": "",
        "status": "not_started",
        "word_count": 0,
    },
    "Pricing Narrative": {
        "ai_draft": "",
        "human_content": "",
        "final_content": "",
        "status": "not_started",
        "word_count": 0,
    },
    "Rate Justification": {
        "ai_draft": "",
        "human_content": "",
        "final_content": "",
        "status": "not_started",
        "word_count": 0,
    },
}


class Command(BaseCommand):
    help = "Seed proposal templates, sample proposals with sections, and review cycles"

    def handle(self, *args, **options):
        self._seed_templates()
        self._seed_proposals()

    def _seed_templates(self):
        created = 0
        for tpl_data in TEMPLATES:
            _, was_created = ProposalTemplate.objects.update_or_create(
                name=tpl_data["name"],
                defaults=tpl_data,
            )
            if was_created:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(f"Proposal templates: {created} created, {len(TEMPLATES) - created} updated")
        )

    def _seed_proposals(self):
        deals = Deal.objects.all()[:3]
        if not deals:
            self.stdout.write(self.style.WARNING("No deals found — skipping proposal seeding"))
            return

        template = ProposalTemplate.objects.filter(is_default=True).first()
        if not template:
            self.stdout.write(self.style.WARNING("No default template — skipping proposal seeding"))
            return

        proposals_created = 0
        sections_created = 0
        reviews_created = 0

        now = timezone.now()

        for i, deal in enumerate(deals):
            if Proposal.objects.filter(deal=deal).exists():
                self.stdout.write(f"  Deal '{deal}' already has proposals — skipping")
                continue

            # Vary the proposal status per deal
            if i == 0:
                prop_status = "red_team"
                prop_title = f"{deal.title or deal.name} - Technical Proposal"
            elif i == 1:
                prop_status = "draft"
                prop_title = f"{deal.title or deal.name} - Proposal Response"
            else:
                prop_status = "pink_team"
                prop_title = f"{deal.title or deal.name} - OASIS+ Task Order Response"

            win_themes = [
                "Proven DHS modernization experience with zero-downtime migration track record",
                "100% cleared workforce with deep agency domain expertise",
                "30% faster delivery through proprietary migration framework",
                "22% lifecycle cost reduction via cloud-native optimization",
            ] if i == 0 else [
                "Deep agency domain expertise and mission understanding",
                "Agile delivery methodology tailored to federal requirements",
                "Strong small business and teaming partner network",
            ]

            discriminators = [
                "Proprietary Migration Readiness Assessment tool reduces planning by 40%",
                "Only vendor with 3 successful DHS cloud migrations at this scale",
                "Integrated AI/ML capability for predictive system health monitoring",
            ] if i == 0 else [
                "FedRAMP High authorized platform available Day 1",
                "Key personnel with direct agency program experience",
            ]

            exec_summary = SECTION_CONTENT["Executive Summary"]["ai_draft"] if i == 0 else ""

            compliance_pct = 78.5 if i == 0 else (0.0 if i == 1 else 45.0)
            total_reqs = 42 if i == 0 else (0 if i == 1 else 28)
            compliant = int(total_reqs * compliance_pct / 100)

            proposal = Proposal.objects.create(
                deal=deal,
                template=template,
                title=prop_title,
                version=1 if i != 0 else 2,
                status=prop_status,
                solicitation_number=f"HSHQDC-26-R-{10042 + i:05d}",
                project_title=prop_title,
                issuing_agency="Department of Homeland Security" if i == 0 else "General Services Administration",
                submission_date=now + timedelta(days=30 + i * 15),
                evaluation_method="best_value" if i == 0 else "lpta",
                contract_type="cpff" if i == 0 else "t_and_m",
                win_themes=win_themes,
                discriminators=discriminators,
                executive_summary=exec_summary,
                total_requirements=total_reqs,
                compliant_count=compliant,
                compliance_percentage=compliance_pct,
                submission_method="portal",
                submission_portal_url="https://sam.gov",
            )
            proposals_created += 1

            # Create sections from template
            for vol_data in template.volumes:
                vol_name = vol_data["volume_name"]
                for order, sec_data in enumerate(vol_data["sections"]):
                    sec_name = sec_data["name"]
                    content = SECTION_CONTENT.get(sec_name, {})

                    # For non-first proposals, make everything not_started
                    if i != 0:
                        content = {"ai_draft": "", "human_content": "", "final_content": "", "status": "not_started", "word_count": 0}

                    sec_num_prefix = vol_name.split(" ")[0].replace("Volume", "").strip() or "1"
                    try:
                        vol_idx = ["I", "II", "III", "IV", "V"].index(sec_num_prefix) + 1
                    except ValueError:
                        vol_idx = 1

                    ProposalSection.objects.create(
                        proposal=proposal,
                        volume=vol_name,
                        section_number=f"L.{vol_idx}.{order + 1}",
                        title=sec_name,
                        order=order,
                        ai_draft=content.get("ai_draft", ""),
                        human_content=content.get("human_content", ""),
                        final_content=content.get("final_content", ""),
                        status=content.get("status", "not_started"),
                        word_count=content.get("word_count", 0),
                        page_limit=sec_data.get("page_limit"),
                    )
                    sections_created += 1

            # Create review cycles for the first proposal
            if i == 0:
                ReviewCycle.objects.create(
                    proposal=proposal,
                    review_type="pink",
                    status="completed",
                    scheduled_date=now - timedelta(days=21),
                    completed_date=now - timedelta(days=18),
                    overall_score=72.5,
                    summary="Pink team identified several areas for improvement in the technical approach. Executive summary needs stronger discriminators. Staffing plan approved with minor comments. 14 action items generated, 12 resolved.",
                )
                ReviewCycle.objects.create(
                    proposal=proposal,
                    review_type="red",
                    status="in_progress",
                    scheduled_date=now - timedelta(days=3),
                    overall_score=None,
                    summary="",
                )
                reviews_created += 2
            elif i == 2:
                ReviewCycle.objects.create(
                    proposal=proposal,
                    review_type="pink",
                    status="scheduled",
                    scheduled_date=now + timedelta(days=7),
                )
                reviews_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Proposals: {proposals_created} created, {sections_created} sections, {reviews_created} review cycles"
            )
        )
