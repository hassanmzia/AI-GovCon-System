"""
Management command to upload Bidvantage template files from GovCon-Policies/
into Django storage (MinIO) and update DocumentTemplate records.

Usage:
    python manage.py upload_bidvantage_templates
    python manage.py upload_bidvantage_templates --policies-dir /path/to/GovCon-Policies
"""

import os
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from apps.knowledge_vault.models import DocumentTemplate


class Command(BaseCommand):
    help = "Upload Bidvantage template files from GovCon-Policies/ to storage"

    def add_arguments(self, parser):
        parser.add_argument(
            "--policies-dir",
            default=None,
            help="Path to GovCon-Policies directory (default: auto-detect)",
        )

    def handle(self, *args, **options):
        policies_dir = options["policies_dir"]
        if not policies_dir:
            # Auto-detect: look relative to manage.py → backend/ → project root
            base = Path(__file__).resolve().parent.parent.parent.parent.parent
            policies_dir = base / "GovCon-Policies"

        policies_dir = Path(policies_dir)
        if not policies_dir.is_dir():
            self.stderr.write(self.style.ERROR(f"Directory not found: {policies_dir}"))
            return

        templates = DocumentTemplate.objects.filter(source="Bidvantage")
        uploaded = 0

        for tmpl in templates:
            # Extract the original filename from the stored file path
            stored_name = os.path.basename(tmpl.file.name) if tmpl.file else ""
            local_path = policies_dir / stored_name

            if not local_path.exists():
                self.stdout.write(
                    self.style.WARNING(f"  SKIP {tmpl.name}: file not found at {local_path}")
                )
                continue

            file_size = local_path.stat().st_size
            with open(local_path, "rb") as f:
                tmpl.file.save(stored_name, File(f), save=False)

            tmpl.file_size = file_size
            tmpl.save(update_fields=["file", "file_size", "updated_at"])

            uploaded += 1
            size_mb = file_size / (1024 * 1024)
            self.stdout.write(
                self.style.SUCCESS(f"  OK {tmpl.name} ({size_mb:.1f} MB)")
            )

        self.stdout.write(
            self.style.SUCCESS(f"\nUploaded {uploaded}/{templates.count()} templates")
        )
