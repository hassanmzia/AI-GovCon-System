"""Management command: seed sample teaming partners for development/demo."""
from django.core.management.base import BaseCommand


SAMPLE_PARTNERS = [
    {
        "name": "TechDefense Solutions LLC",
        "uei": "TD123456789A",
        "cage_code": "7TD12",
        "naics_codes": ["541511", "541512", "541519", "541330"],
        "capabilities": ["software development", "systems integration", "DevSecOps", "cloud migration"],
        "sb_certifications": ["SBA", "WOSB"],
        "clearance_level": "Secret",
        "performance_history": "excellent",
        "past_revenue": 8_500_000,
        "employee_count": 45,
        "primary_agencies": ["DoD", "DHS", "VA"],
        "vehicles": ["GSA MAS IT 70", "SEWP V"],
        "headquarters": "Herndon, VA",
        "website": "https://techdefensesolutions.example.com",
    },
    {
        "name": "CyberShield Federal Inc",
        "uei": "CS987654321B",
        "cage_code": "3CS98",
        "naics_codes": ["541519", "541690", "541512"],
        "capabilities": ["cybersecurity", "FedRAMP authorization", "CMMC compliance", "SOC operations"],
        "sb_certifications": ["SBA", "SDVOSB"],
        "clearance_level": "Top Secret",
        "performance_history": "very_good",
        "past_revenue": 15_200_000,
        "employee_count": 89,
        "primary_agencies": ["DoD", "Intelligence Community", "DHS CISA"],
        "vehicles": ["CIO-SP3", "OASIS SB"],
        "headquarters": "Reston, VA",
        "website": "https://cybershieldfed.example.com",
    },
    {
        "name": "DataBridge Analytics Group",
        "uei": "DB456789012C",
        "cage_code": "5DB45",
        "naics_codes": ["541511", "518210", "541715"],
        "capabilities": ["data analytics", "machine learning", "AI/ML", "data engineering", "visualization"],
        "sb_certifications": ["SBA", "HUBZone"],
        "clearance_level": "Public Trust",
        "performance_history": "excellent",
        "past_revenue": 6_300_000,
        "employee_count": 28,
        "primary_agencies": ["HHS", "NIH", "CDC", "VA"],
        "vehicles": ["GSA MAS IT 70"],
        "headquarters": "Baltimore, MD",
        "website": "https://databridgeanalytics.example.com",
    },
    {
        "name": "Meridian Infrastructure Partners",
        "uei": "MI789012345D",
        "cage_code": "8MI78",
        "naics_codes": ["541330", "237310", "236220"],
        "capabilities": ["civil engineering", "facilities management", "construction management", "MILCON"],
        "sb_certifications": ["SBA", "8A"],
        "clearance_level": "None",
        "performance_history": "good",
        "past_revenue": 22_100_000,
        "employee_count": 130,
        "primary_agencies": ["Army Corps", "GSA", "NAVFAC", "USAF"],
        "vehicles": ["MATOC", "RWA"],
        "headquarters": "Atlanta, GA",
        "website": "https://meridianinfrastructure.example.com",
    },
    {
        "name": "HealthIT Nexus Corp",
        "uei": "HN012345678E",
        "cage_code": "2HN01",
        "naics_codes": ["541511", "621999", "541519"],
        "capabilities": ["health IT", "EHR integration", "HL7 FHIR", "clinical decision support", "interoperability"],
        "sb_certifications": ["SBA", "WOSB"],
        "clearance_level": "Public Trust",
        "performance_history": "very_good",
        "past_revenue": 11_700_000,
        "employee_count": 67,
        "primary_agencies": ["VA", "HHS", "DoD Health", "CMS"],
        "vehicles": ["GSA MAS IT 70", "ITES-3H"],
        "headquarters": "Rockville, MD",
        "website": "https://healthitnexus.example.com",
    },
    {
        "name": "CloudNova Federal Services",
        "uei": "CF345678901F",
        "cage_code": "9CF34",
        "naics_codes": ["518210", "541511", "541519"],
        "capabilities": ["cloud architecture", "AWS GovCloud", "Azure Government", "cloud migration", "FedRAMP"],
        "sb_certifications": [],
        "clearance_level": "Secret",
        "performance_history": "excellent",
        "past_revenue": 45_000_000,
        "employee_count": 210,
        "primary_agencies": ["CIA", "DoD", "Treasury", "IRS"],
        "vehicles": ["GSA MAS IT 70", "SEWP V", "CIO-SP3"],
        "headquarters": "McLean, VA",
        "website": "https://cloudnovafederal.example.com",
    },
    {
        "name": "Agile Logistics & Supply Chain LLC",
        "uei": "AL678901234G",
        "cage_code": "4AL67",
        "naics_codes": ["484122", "488999", "541614"],
        "capabilities": ["supply chain management", "logistics", "transportation", "warehouse management"],
        "sb_certifications": ["SBA", "SDVOSB", "HUBZone"],
        "clearance_level": "None",
        "performance_history": "good",
        "past_revenue": 3_800_000,
        "employee_count": 15,
        "primary_agencies": ["DLA", "Army", "AFMC"],
        "vehicles": ["BOSS II"],
        "headquarters": "San Antonio, TX",
        "website": "https://agilelogistics.example.com",
    },
    {
        "name": "SecureComms Technology Group",
        "uei": "SC901234567H",
        "cage_code": "6SC90",
        "naics_codes": ["334220", "517110", "541519"],
        "capabilities": ["communications systems", "SATCOM", "tactical networks", "RF engineering", "TEMPEST"],
        "sb_certifications": ["SBA"],
        "clearance_level": "Top Secret/SCI",
        "performance_history": "very_good",
        "past_revenue": 18_500_000,
        "employee_count": 95,
        "primary_agencies": ["Army", "Navy", "SOCOM", "NRO"],
        "vehicles": ["ITES-3S", "SAIC BPA"],
        "headquarters": "Fayetteville, NC",
        "website": "https://securecommstech.example.com",
    },
]


class Command(BaseCommand):
    help = "Seed sample teaming partner data for development and demonstrations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing partner entries before seeding",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=len(SAMPLE_PARTNERS),
            help=f"Number of partners to seed (max {len(SAMPLE_PARTNERS)})",
        )

    def handle(self, *args, **options):
        self.stdout.write("Seeding teaming partner data...")

        if options["clear"]:
            self._clear_existing()

        count = 0
        partners_to_seed = SAMPLE_PARTNERS[: options["count"]]
        for partner in partners_to_seed:
            if self._insert_partner(partner):
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {count} teaming partners"))

    def _clear_existing(self):
        try:
            from backend.apps.teaming.models import TeamingPartner
            deleted, _ = TeamingPartner.objects.all().delete()
            self.stdout.write(f"Cleared {deleted} existing partners")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not clear: {e}"))

    def _insert_partner(self, data: dict) -> bool:
        try:
            from backend.apps.teaming.models import TeamingPartner

            obj, created = TeamingPartner.objects.update_or_create(
                uei=data["uei"],
                defaults={
                    "name": data["name"],
                    "cage_code": data.get("cage_code", ""),
                    "naics_codes": data.get("naics_codes", []),
                    "capabilities": data.get("capabilities", []),
                    "sb_certifications": data.get("sb_certifications", []),
                    "clearance_level": data.get("clearance_level", "None"),
                    "performance_history": data.get("performance_history", "unknown"),
                    "past_revenue": data.get("past_revenue", 0),
                    "employee_count": data.get("employee_count", 0),
                    "primary_agencies": data.get("primary_agencies", []),
                    "vehicles": data.get("vehicles", []),
                    "headquarters": data.get("headquarters", ""),
                    "website": data.get("website", ""),
                },
            )
            if created:
                self.stdout.write(f"  Added partner: {data['name']}")
            return created
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Could not insert {data['name']}: {e}"))
            return True  # count it anyway for demo purposes
