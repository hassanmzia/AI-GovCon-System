"""Seed standard GovCon labor category rate cards."""
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.pricing.models import RateCard


RATE_CARDS = [
    # (labor_category, gsa_equivalent, internal_rate, gsa_rate, proposed_rate,
    #  market_low, market_median, market_high, education, experience_years, clearance)
    ("Program Manager", "Program Manager", 195, 210, 205, 175, 200, 240, "Master's", 15, "Secret"),
    ("Senior Program Manager", "Senior Program Manager", 225, 245, 240, 210, 235, 275, "Master's", 20, "TS/SCI"),
    ("Project Manager", "Project Manager", 155, 170, 165, 140, 160, 195, "Bachelor's", 10, "Secret"),
    ("Senior Systems Engineer", "Senior Systems Engineer", 185, 200, 195, 170, 190, 225, "Master's", 12, "Secret"),
    ("Systems Engineer", "Systems Engineer", 145, 155, 150, 130, 148, 175, "Bachelor's", 7, "Secret"),
    ("Senior Software Engineer", "Senior Software Developer", 175, 190, 185, 160, 180, 215, "Bachelor's", 10, "Secret"),
    ("Software Engineer", "Software Developer", 135, 145, 140, 120, 138, 165, "Bachelor's", 5, ""),
    ("Junior Software Engineer", "Junior Software Developer", 95, 105, 100, 85, 98, 120, "Bachelor's", 2, ""),
    ("Cloud Architect", "Cloud Solutions Architect", 200, 220, 215, 185, 210, 250, "Master's", 12, "Secret"),
    ("DevSecOps Engineer", "DevOps/DevSecOps Engineer", 165, 180, 175, 150, 170, 200, "Bachelor's", 8, "Secret"),
    ("Data Scientist", "Data Scientist/Analyst", 170, 185, 180, 155, 175, 210, "Master's", 8, ""),
    ("AI/ML Engineer", "AI/ML Engineer", 185, 200, 195, 165, 188, 230, "Master's", 8, "Secret"),
    ("Cybersecurity Analyst", "Information Security Analyst", 150, 165, 160, 135, 155, 185, "Bachelor's", 7, "Secret"),
    ("Senior Cybersecurity Engineer", "Senior Info Security Engineer", 185, 200, 195, 170, 190, 225, "Master's", 12, "TS/SCI"),
    ("Security Engineer", "Security Engineer", 155, 170, 165, 140, 158, 190, "Bachelor's", 7, "Secret"),
    ("Network Engineer", "Network Engineer", 140, 150, 145, 125, 142, 170, "Bachelor's", 7, "Secret"),
    ("Database Administrator", "Database Administrator", 135, 145, 140, 120, 138, 165, "Bachelor's", 7, ""),
    ("Business Analyst", "Business Analyst", 125, 135, 130, 110, 128, 155, "Bachelor's", 5, ""),
    ("Senior Business Analyst", "Senior Business Analyst", 155, 170, 165, 140, 160, 190, "Master's", 10, "Secret"),
    ("Technical Writer", "Technical Writer", 95, 105, 100, 80, 95, 120, "Bachelor's", 5, ""),
    ("QA Analyst", "Quality Assurance Analyst", 110, 120, 115, 95, 112, 135, "Bachelor's", 5, ""),
    ("QA Engineer", "Quality Assurance Engineer", 130, 140, 135, 115, 132, 160, "Bachelor's", 7, ""),
    ("Help Desk Specialist", "Help Desk / Tier I Support", 65, 72, 70, 55, 65, 85, "Associate's", 2, ""),
    ("Help Desk Tier II", "Help Desk / Tier II Support", 85, 95, 90, 75, 88, 105, "Bachelor's", 4, ""),
    ("System Administrator", "System Administrator", 120, 130, 125, 105, 122, 150, "Bachelor's", 5, "Secret"),
    ("Senior System Administrator", "Senior System Administrator", 150, 165, 160, 135, 155, 185, "Bachelor's", 10, "TS/SCI"),
    ("Enterprise Architect", "Enterprise Architect", 210, 230, 225, 195, 220, 260, "Master's", 15, "TS/SCI"),
    ("Solutions Architect", "Solutions Architect", 190, 210, 205, 175, 200, 240, "Master's", 12, "Secret"),
    ("Scrum Master", "Agile Coach / Scrum Master", 140, 150, 145, 125, 142, 170, "Bachelor's", 7, ""),
    ("UX/UI Designer", "UX/UI Designer", 125, 135, 130, 110, 128, 155, "Bachelor's", 5, ""),
    ("Data Engineer", "Data Engineer", 155, 170, 165, 140, 158, 190, "Bachelor's", 7, ""),
    ("Subject Matter Expert", "Subject Matter Expert", 200, 220, 215, 180, 205, 250, "Master's", 15, "Secret"),
    ("Capture Manager", "Capture Manager", 175, 190, 185, 160, 180, 215, "Master's", 12, "Secret"),
    ("Proposal Manager", "Proposal Manager", 145, 160, 155, 130, 150, 180, "Bachelor's", 10, ""),
    ("Configuration Manager", "Configuration Manager", 125, 135, 130, 110, 128, 155, "Bachelor's", 7, "Secret"),
]


class Command(BaseCommand):
    help = "Seed standard GovCon labor category rate cards"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing rate cards before seeding",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            deleted, _ = RateCard.objects.all().delete()
            self.stdout.write(f"Deleted {deleted} existing rate cards")

        created = 0
        updated = 0
        for row in RATE_CARDS:
            (cat, gsa_eq, internal, gsa, proposed, mkt_low, mkt_med, mkt_high,
             edu, exp_yrs, clearance) = row
            _, was_created = RateCard.objects.update_or_create(
                labor_category=cat,
                defaults={
                    "gsa_equivalent": gsa_eq,
                    "gsa_sin": "",
                    "internal_rate": Decimal(str(internal)),
                    "gsa_rate": Decimal(str(gsa)),
                    "proposed_rate": Decimal(str(proposed)),
                    "market_low": Decimal(str(mkt_low)),
                    "market_median": Decimal(str(mkt_med)),
                    "market_high": Decimal(str(mkt_high)),
                    "education_requirement": edu,
                    "experience_years": exp_yrs,
                    "clearance_required": clearance,
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Rate cards: {created} created, {updated} updated")
        )
