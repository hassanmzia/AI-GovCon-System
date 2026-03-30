"""Seed competitor profiles and market intelligence for the Marketing page."""

from datetime import date

from django.core.management.base import BaseCommand

from apps.research.models import CompetitorProfile, MarketIntelligence


COMPETITORS = [
    {
        "name": "Booz Allen Hamilton",
        "cage_code": "17038",
        "duns_number": "006928857",
        "website": "https://www.boozallen.com",
        "naics_codes": ["541512", "541330", "541611", "541519", "518210"],
        "contract_vehicles": ["STARS III", "Alliant 2", "CIO-SP3", "OASIS"],
        "key_personnel": [
            {"name": "Horacio Rozanski", "title": "CEO"},
            {"name": "Kristine Martin Anderson", "title": "Chief Growth Officer"},
        ],
        "revenue_range": "$8B - $10B",
        "employee_count": 33000,
        "past_performance_summary": "Deep expertise in defense, intelligence, and civil agencies. Strong AI/ML and cyber capabilities. Major contracts with DoD, DHS, and IC.",
        "strengths": [
            "Deep DoD and IC relationships",
            "Advanced AI/ML and analytics capabilities",
            "Large cleared workforce (TS/SCI)",
            "Strong cybersecurity practice",
            "Agile transformation expertise",
        ],
        "weaknesses": [
            "Higher labor rates than mid-tier competitors",
            "Slower decision-making due to size",
            "Less competitive on small business set-asides",
        ],
        "win_rate": 0.42,
    },
    {
        "name": "Leidos",
        "cage_code": "1XAQ7",
        "duns_number": "078846011",
        "website": "https://www.leidos.com",
        "naics_codes": ["541512", "541330", "541715", "561210", "541511"],
        "contract_vehicles": ["OASIS", "Alliant 2", "SEWP V", "GSA IT 70"],
        "key_personnel": [
            {"name": "Tom Bell", "title": "CEO"},
            {"name": "Roy Stevens", "title": "President, Defense Group"},
        ],
        "revenue_range": "$14B - $16B",
        "employee_count": 47000,
        "past_performance_summary": "Broad portfolio spanning defense, health, civil, and intelligence. Acquired Dynetics for space/missile defense. Strong systems integration.",
        "strengths": [
            "Largest pure-play IT services provider",
            "Strong health IT presence (VA, DHA)",
            "Deep systems integration expertise",
            "Extensive SETA and advisory work",
        ],
        "weaknesses": [
            "Integration challenges from acquisitions",
            "Perception as legacy contractor in some areas",
            "Less agile than smaller competitors",
        ],
        "win_rate": 0.38,
    },
    {
        "name": "SAIC",
        "cage_code": "4L767",
        "duns_number": "078271766",
        "website": "https://www.saic.com",
        "naics_codes": ["541512", "541330", "541611", "541519", "561210"],
        "contract_vehicles": ["OASIS", "Alliant 2", "CIO-SP3", "STARS III"],
        "key_personnel": [
            {"name": "Toni Townes-Whitley", "title": "CEO"},
            {"name": "Michelle OHara", "title": "CFO"},
        ],
        "revenue_range": "$7B - $8B",
        "employee_count": 26000,
        "past_performance_summary": "Strong IT modernization and cloud migration practice. Major NASA and Army contracts. Growing space and intelligence portfolio.",
        "strengths": [
            "IT modernization and cloud migration leader",
            "Strong NASA and Army relationships",
            "Competitive pricing structure",
            "Growing digital engineering practice",
        ],
        "weaknesses": [
            "Less brand recognition than top-tier competitors",
            "Smaller cyber practice compared to peers",
            "Limited international presence",
        ],
        "win_rate": 0.35,
    },
    {
        "name": "Peraton",
        "cage_code": "3RLZ3",
        "duns_number": "117501806",
        "website": "https://www.peraton.com",
        "naics_codes": ["541512", "541330", "517919", "541519", "541715"],
        "contract_vehicles": ["OASIS", "CIO-SP3", "SEWP V"],
        "key_personnel": [
            {"name": "Stu Shea", "title": "CEO"},
            {"name": "John Coleman", "title": "COO"},
        ],
        "revenue_range": "$7B - $8B",
        "employee_count": 18000,
        "past_performance_summary": "Formed from merger of Perspecta, Northrop Grumman IT, and DECO. Strong signals intelligence, satellite, and cyber operations.",
        "strengths": [
            "Deep intelligence community penetration",
            "Strong signals and space capabilities",
            "Large cleared workforce",
            "Aggressive M&A growth strategy",
        ],
        "weaknesses": [
            "Still integrating multiple acquisitions",
            "Less competitive in civilian agencies",
            "Private equity ownership may limit investment",
        ],
        "win_rate": 0.40,
    },
    {
        "name": "ManTech International",
        "cage_code": "79066",
        "duns_number": "080155794",
        "website": "https://www.mantech.com",
        "naics_codes": ["541512", "541330", "541611", "541519"],
        "contract_vehicles": ["OASIS", "Alliant 2", "CIO-SP3"],
        "key_personnel": [
            {"name": "Matt Tait", "title": "CEO"},
        ],
        "revenue_range": "$2.5B - $3B",
        "employee_count": 10000,
        "past_performance_summary": "Strong in cyber, intelligence, and federal IT. Acquired by Carlyle Group. Deep FBI and DoD relationships.",
        "strengths": [
            "Tier-1 cyber operations and offensive security",
            "Strong FBI and law enforcement relationships",
            "Agile mid-tier competitor",
            "High employee retention in cleared roles",
        ],
        "weaknesses": [
            "Smaller scale limits large program bids",
            "Limited health IT presence",
            "Narrower NAICS coverage than larger competitors",
        ],
        "win_rate": 0.36,
    },
    {
        "name": "CGI Federal",
        "cage_code": "1YYG7",
        "duns_number": "150116326",
        "website": "https://www.cgi.com/us/en-us/federal",
        "naics_codes": ["541512", "541511", "541519", "518210", "541611"],
        "contract_vehicles": ["CIO-SP3", "SEWP V", "GSA IT 70", "OASIS"],
        "key_personnel": [
            {"name": "Stephanie Mango", "title": "President, CGI Federal"},
        ],
        "revenue_range": "$1.5B - $2B",
        "employee_count": 5500,
        "past_performance_summary": "Strong presence in financial systems, benefits, and health IT. Major VA, CMS, and Treasury contracts.",
        "strengths": [
            "Financial systems and ERP expertise",
            "Strong VA and CMS presence",
            "Global delivery model reduces costs",
            "IP-based solutions (Advantage ERP, COTS)",
        ],
        "weaknesses": [
            "Limited cleared workforce for DoD/IC",
            "Perception as foreign-owned (Canadian parent)",
            "Smaller U.S. footprint than peers",
        ],
        "win_rate": 0.33,
    },
    {
        "name": "Deloitte Consulting",
        "cage_code": "1EH27",
        "duns_number": "002776218",
        "website": "https://www2.deloitte.com/us/en/pages/public-sector/topics/government-consulting.html",
        "naics_codes": ["541611", "541512", "541330", "541618", "541219"],
        "contract_vehicles": ["OASIS", "Alliant 2", "GSA STARS III"],
        "key_personnel": [
            {"name": "Mike Canning", "title": "U.S. Government & Public Services Leader"},
        ],
        "revenue_range": "$3B - $4B",
        "employee_count": 15000,
        "past_performance_summary": "Premium advisory and consulting. Strong in transformation, organizational change, and strategy. Major DoD and civilian agency engagements.",
        "strengths": [
            "Premium brand and strategic advisory",
            "Strong organizational transformation practice",
            "Deep agency leadership relationships",
            "Cross-industry innovation transfer",
        ],
        "weaknesses": [
            "Highest labor rates in the market",
            "Organizational conflict of interest (OCI) concerns",
            "Less technical depth in systems engineering",
        ],
        "win_rate": 0.30,
    },
    {
        "name": "Accenture Federal Services",
        "cage_code": "3A9P3",
        "duns_number": "826442782",
        "website": "https://www.accenture.com/us-en/industries/afs-index",
        "naics_codes": ["541512", "541511", "541611", "541519", "518210"],
        "contract_vehicles": ["OASIS", "Alliant 2", "CIO-SP3", "SEWP V"],
        "key_personnel": [
            {"name": "John Goodman", "title": "CEO, Accenture Federal Services"},
        ],
        "revenue_range": "$3B - $4B",
        "employee_count": 13000,
        "past_performance_summary": "Strong cloud, digital, and platform modernization. Growing DoD and DHS portfolio. Known for commercial technology transfer.",
        "strengths": [
            "Cloud and digital transformation leader",
            "Commercial tech transfer to government",
            "Strong platform and low-code capabilities",
            "Rapid scaling through global resources",
        ],
        "weaknesses": [
            "OCI concerns on advisory engagements",
            "Higher rates than traditional GovCon firms",
            "Perception of commercial-first approach",
        ],
        "win_rate": 0.34,
    },
]

MARKET_INTELLIGENCE = [
    {
        "category": "budget_trends",
        "title": "FY2026 Defense Budget Increases IT Modernization Funding by 12%",
        "summary": "The FY2026 NDAA allocates an additional $8.2B for IT modernization across DoD, with emphasis on zero trust architecture, cloud migration, and AI/ML integration.",
        "detail": {
            "total_it_budget": "$52.3B",
            "yoy_increase": "12%",
            "top_priorities": ["Zero Trust", "Cloud Migration", "AI/ML", "Cyber Operations"],
            "key_programs": ["JADC2", "CDAO initiatives", "Service-specific cloud programs"],
        },
        "impact_assessment": "Significant opportunity for cloud and cybersecurity contractors. Zero trust mandates create new requirements across all DoD components.",
        "affected_naics": ["541512", "541519", "518210"],
        "affected_agencies": ["Department of Defense", "DISA", "Cyber Command"],
        "published_date": "2026-02-15",
    },
    {
        "category": "policy_changes",
        "title": "OMB M-24-18 Mandates AI Governance for All Federal Agencies",
        "summary": "New OMB memorandum requires all CFO Act agencies to establish AI governance boards, inventory AI use cases, and implement risk management frameworks by Q4 FY2026.",
        "detail": {
            "compliance_deadline": "September 30, 2026",
            "key_requirements": [
                "AI governance board establishment",
                "Complete AI use case inventory",
                "Risk management framework implementation",
                "Bias testing and monitoring",
            ],
            "affected_agencies_count": 24,
        },
        "impact_assessment": "Creates immediate demand for AI governance consulting, risk assessment tools, and compliance support. Agencies will need help inventorying existing AI use cases.",
        "affected_naics": ["541512", "541611", "541519"],
        "affected_agencies": ["All CFO Act Agencies", "OMB", "GSA AI CoE"],
        "published_date": "2026-01-20",
    },
    {
        "category": "technology_shifts",
        "title": "Federal Cloud Smart 2.0 Pushes Multi-Cloud and Edge Computing",
        "summary": "GSA and OMB release updated Cloud Smart guidance emphasizing multi-cloud strategies, edge computing for field operations, and FedRAMP High automation.",
        "detail": {
            "key_changes": [
                "Multi-cloud mandated for mission-critical workloads",
                "Edge computing framework for field agencies",
                "FedRAMP continuous monitoring automation",
                "Cloud-native application development standards",
            ],
            "market_size": "$18B by 2028",
        },
        "impact_assessment": "Multi-cloud requirements benefit vendors with expertise across AWS GovCloud, Azure Government, and Google Cloud Platform. Edge computing opens new opportunities for IoT and tactical deployments.",
        "affected_naics": ["541512", "518210", "541519"],
        "affected_agencies": ["GSA", "All Federal Agencies", "FedRAMP PMO"],
        "published_date": "2026-03-01",
    },
    {
        "category": "procurement_patterns",
        "title": "DoD Shifts to OASIS+ for Large IT Services Acquisitions",
        "summary": "DoD CIO directs all components to prioritize OASIS+ for IT services above $10M, reducing use of agency-specific BPAs and standalone contracts.",
        "detail": {
            "threshold": "$10M+",
            "affected_domains": ["IT Services", "Management Consulting", "Engineering"],
            "transition_timeline": "FY2026-2027",
            "exceptions": ["Classified programs", "Urgent operational needs"],
        },
        "impact_assessment": "Firms without OASIS+ positions face significant competitive disadvantage. Teaming arrangements with OASIS+ holders become critical for sub-tier firms.",
        "affected_naics": ["541512", "541330", "541611"],
        "affected_agencies": ["Department of Defense", "GSA", "Service Components"],
        "published_date": "2026-02-28",
    },
    {
        "category": "workforce_trends",
        "title": "Federal Cyber Workforce Gap Reaches 40,000 Unfilled Positions",
        "summary": "OPM reports 40,000+ unfilled cybersecurity positions across federal agencies, driving increased reliance on contractor support and managed security services.",
        "detail": {
            "unfilled_positions": 40000,
            "most_impacted_agencies": ["DoD", "DHS", "VA", "Treasury"],
            "critical_roles": ["Incident Response", "Cloud Security", "Zero Trust Architecture", "Penetration Testing"],
            "contractor_growth_rate": "18% YoY",
        },
        "impact_assessment": "Significant opportunity for managed security service providers and cybersecurity staffing. Cleared cyber professionals command 25-40% premiums over commercial equivalents.",
        "affected_naics": ["541512", "541519", "561320"],
        "affected_agencies": ["OPM", "CISA", "DoD CIO", "All Federal Agencies"],
        "published_date": "2026-03-10",
    },
    {
        "category": "budget_trends",
        "title": "VA Digital Modernization Receives $4.1B in FY2026",
        "summary": "Veterans Affairs secures $4.1B for continued EHR modernization, telehealth expansion, and benefits processing automation.",
        "detail": {
            "ehr_modernization": "$2.1B",
            "telehealth": "$850M",
            "benefits_automation": "$650M",
            "cybersecurity": "$500M",
        },
        "impact_assessment": "Major opportunity in health IT, EHR integration, and telehealth platforms. Oracle Health (formerly Cerner) ecosystem partners particularly well-positioned.",
        "affected_naics": ["541512", "541511", "621999"],
        "affected_agencies": ["Department of Veterans Affairs", "VHA", "VBA"],
        "published_date": "2026-01-30",
    },
    {
        "category": "technology_shifts",
        "title": "CISA Publishes Zero Trust Maturity Model v3.0",
        "summary": "CISA releases updated Zero Trust Maturity Model with mandatory implementation milestones for all federal agencies through FY2028.",
        "detail": {
            "maturity_levels": ["Traditional", "Initial", "Advanced", "Optimal"],
            "pillars": ["Identity", "Devices", "Networks", "Applications", "Data"],
            "fy2026_target": "Initial maturity across all pillars",
            "fy2028_target": "Advanced maturity for high-impact systems",
        },
        "impact_assessment": "Agencies at Traditional level must rapidly implement identity-centric security, microsegmentation, and continuous diagnostics. Creates $6B+ addressable market through FY2028.",
        "affected_naics": ["541512", "541519", "518210"],
        "affected_agencies": ["CISA", "All Federal Agencies", "OMB"],
        "published_date": "2026-03-15",
    },
    {
        "category": "procurement_patterns",
        "title": "NASA SEWP VI Contract Vehicle Expected Q3 FY2026",
        "summary": "NASA announces SEWP VI solicitation timeline with expanded scope to include AI/ML platforms, quantum computing services, and enhanced cybersecurity tools.",
        "detail": {
            "expected_release": "Q3 FY2026",
            "estimated_ceiling": "$50B",
            "new_categories": ["AI/ML Platforms", "Quantum Computing", "Edge Computing", "Zero Trust Tools"],
            "competition_level": "Full and open for Groups A-D",
        },
        "impact_assessment": "Critical contract vehicle for IT product resellers and solution providers. Early positioning and capability demonstration will be key to winning slots.",
        "affected_naics": ["541512", "423430", "334111", "511210"],
        "affected_agencies": ["NASA", "All Federal Agencies"],
        "published_date": "2026-02-20",
    },
]


class Command(BaseCommand):
    help = "Seed competitor profiles and market intelligence data"

    def handle(self, *args, **options):
        self._seed_competitors()
        self._seed_market_intelligence()

    def _seed_competitors(self):
        created = 0
        updated = 0
        for data in COMPETITORS:
            _, was_created = CompetitorProfile.objects.update_or_create(
                name=data["name"],
                defaults=data,
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Competitors: {created} created, {updated} updated"
            )
        )

    def _seed_market_intelligence(self):
        created = 0
        updated = 0
        for data in MARKET_INTELLIGENCE:
            pub_date = data.get("published_date")
            if isinstance(pub_date, str):
                data["published_date"] = date.fromisoformat(pub_date)
            _, was_created = MarketIntelligence.objects.update_or_create(
                title=data["title"],
                defaults=data,
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Market intelligence: {created} created, {updated} updated"
            )
        )
