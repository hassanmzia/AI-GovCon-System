import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create the initial admin user from environment variables or arguments"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default=os.environ.get("ADMIN_USERNAME", "admin"),
            help="Username for the admin user (default: ADMIN_USERNAME env var or 'admin')",
        )
        parser.add_argument(
            "--email",
            type=str,
            default=os.environ.get("ADMIN_EMAIL", ""),
            help="Email for the admin user (default: ADMIN_EMAIL env var)",
        )
        parser.add_argument(
            "--password",
            type=str,
            default=os.environ.get("ADMIN_PASSWORD", ""),
            help="Password for the admin user (default: ADMIN_PASSWORD env var)",
        )
        parser.add_argument(
            "--first-name",
            type=str,
            default=os.environ.get("ADMIN_FIRST_NAME", ""),
            help="First name (default: ADMIN_FIRST_NAME env var)",
        )
        parser.add_argument(
            "--last-name",
            type=str,
            default=os.environ.get("ADMIN_LAST_NAME", ""),
            help="Last name (default: ADMIN_LAST_NAME env var)",
        )

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"]
        first_name = options.get("first_name", "")
        last_name = options.get("last_name", "")

        if not email:
            self.stderr.write(
                self.style.ERROR(
                    "Email is required. Provide --email or set ADMIN_EMAIL env var."
                )
            )
            return

        if not password:
            self.stderr.write(
                self.style.ERROR(
                    "Password is required. Provide --password or set ADMIN_PASSWORD env var."
                )
            )
            return

        existing_by_username = User.objects.filter(username=username).first()
        existing_by_email = User.objects.filter(email=email).first()

        if existing_by_username or existing_by_email:
            user = existing_by_username or existing_by_email
            self.stdout.write(
                self.style.WARNING(
                    f'Admin user already exists: "{user.username}" (role: {user.get_role_display()})'
                )
            )
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created admin user "{user.username}"'
            )
        )
        self.stdout.write(f"  Email: {user.email}")
        self.stdout.write(f"  Role: {user.get_role_display()}")
        self.stdout.write(f"  Staff: {user.is_staff}")
        self.stdout.write(f"  Superuser: {user.is_superuser}")
