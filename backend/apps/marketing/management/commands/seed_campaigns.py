"""Seed marketing campaigns for the Marketing page."""

from datetime import date

from django.core.management.base import BaseCommand

from apps.marketing.models import MarketingCampaign


CAMPAIGNS = [
    {
        "name": "FY2026 Cloud Modernization Awareness",
        "description": "Multi-channel campaign targeting CIOs and CTOs at civilian agencies undergoing cloud migration. Highlights our FedRAMP authorized platform and Cloud Smart migration methodology.",
        "channel": "webinar",
        "status": "active",
        "target_audience": "Federal CIOs, CTOs, and IT Directors at civilian agencies",
        "start_date": "2026-01-15",
        "end_date": "2026-06-30",
        "budget": "45000.00",
        "goals": [
            "Generate 50 qualified leads from target agencies",
            "Establish thought leadership in cloud migration",
            "Secure 5 capability briefings with agency decision-makers",
        ],
        "metrics": {
            "registrations": 320,
            "attendees": 185,
            "qualified_leads": 32,
            "briefings_scheduled": 3,
        },
    },
    {
        "name": "Zero Trust Solutions - DoD Campaign",
        "description": "Targeted outreach to DoD components implementing zero trust architectures per CISA maturity model. Showcases our ZTA assessment framework and implementation accelerator.",
        "channel": "direct_outreach",
        "status": "active",
        "target_audience": "DoD CISOs, ISSMs, and Cybersecurity Program Managers",
        "start_date": "2026-02-01",
        "end_date": "2026-09-30",
        "budget": "75000.00",
        "goals": [
            "Schedule 20 ZTA assessment demonstrations",
            "Win 3 ZTA implementation task orders",
            "Build pipeline of $15M in ZTA opportunities",
        ],
        "metrics": {
            "outreach_sent": 150,
            "responses": 42,
            "demos_scheduled": 12,
            "pipeline_value": 8500000,
        },
    },
    {
        "name": "OASIS+ Teaming Partner Recruitment",
        "description": "Campaign to recruit and onboard strategic teaming partners for OASIS+ task order competitions. Focus on complementary capabilities in AI/ML, cyber, and health IT.",
        "channel": "trade_show",
        "status": "active",
        "target_audience": "Small and mid-tier GovCon firms with complementary capabilities",
        "start_date": "2026-03-01",
        "end_date": "2026-08-31",
        "budget": "35000.00",
        "goals": [
            "Identify 15 potential teaming partners",
            "Execute 8 teaming agreements",
            "Submit 5 joint proposals on OASIS+ task orders",
        ],
        "metrics": {
            "partners_identified": 18,
            "ndas_signed": 10,
            "teaming_agreements": 4,
            "joint_proposals": 2,
        },
    },
    {
        "name": "AI/ML Capabilities Showcase - Federal Health",
        "description": "Email and webinar campaign demonstrating AI/ML applications in federal health agencies. Covers predictive analytics, clinical decision support, and fraud detection.",
        "channel": "email",
        "status": "planning",
        "target_audience": "HHS, VA, and DHA health IT leaders",
        "start_date": "2026-04-15",
        "end_date": "2026-07-31",
        "budget": "25000.00",
        "goals": [
            "Build email list of 500 health IT contacts",
            "Achieve 25% open rate on campaign emails",
            "Generate 20 qualified health IT leads",
        ],
        "metrics": {},
    },
    {
        "name": "GovCon Industry Day Presence - Q1 2026",
        "description": "Coordinated attendance and presentation at Q1 industry days including DHS Industry Day, Army IT Day, and NASA SEWP Conference.",
        "channel": "trade_show",
        "status": "completed",
        "target_audience": "Agency program managers and contracting officers",
        "start_date": "2025-10-01",
        "end_date": "2025-12-31",
        "budget": "60000.00",
        "goals": [
            "Attend 6 industry day events",
            "Deliver 3 panel presentations",
            "Collect 200 business cards from key contacts",
        ],
        "metrics": {
            "events_attended": 6,
            "presentations": 3,
            "contacts_collected": 245,
            "follow_up_meetings": 18,
            "pipeline_generated": 12000000,
        },
    },
    {
        "name": "Cyber Awareness Month Social Media Push",
        "description": "Social media content campaign during National Cybersecurity Awareness Month highlighting our security capabilities, certifications, and thought leadership.",
        "channel": "social_media",
        "status": "completed",
        "target_audience": "Federal cybersecurity community on LinkedIn and Twitter/X",
        "start_date": "2025-10-01",
        "end_date": "2025-10-31",
        "budget": "8000.00",
        "goals": [
            "Publish 20 cybersecurity-themed posts",
            "Achieve 50,000 impressions across platforms",
            "Gain 200 new LinkedIn followers",
        ],
        "metrics": {
            "posts_published": 22,
            "total_impressions": 67000,
            "new_followers": 312,
            "engagement_rate": 4.2,
            "website_visits": 1850,
        },
    },
]


class Command(BaseCommand):
    help = "Seed marketing campaigns"

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for data in CAMPAIGNS:
            for date_field in ("start_date", "end_date"):
                val = data.get(date_field)
                if isinstance(val, str):
                    data[date_field] = date.fromisoformat(val)
            _, was_created = MarketingCampaign.objects.update_or_create(
                name=data["name"],
                defaults=data,
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Campaigns: {created} created, {updated} updated"
            )
        )
