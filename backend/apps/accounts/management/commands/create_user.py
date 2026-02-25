from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Create a new user with specified role"

    def add_arguments(self, parser):
        parser.add_argument(
            "username",
            type=str,
            help="Username for the new user",
        )
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email address for the user",
        )
        parser.add_argument(
            "--password",
            type=str,
            required=True,
            help="Password for the user",
        )
        parser.add_argument(
            "--first-name",
            type=str,
            default="",
            help="First name of the user",
        )
        parser.add_argument(
            "--last-name",
            type=str,
            default="",
            help="Last name of the user",
        )
        parser.add_argument(
            "--role",
            type=str,
            default="viewer",
            choices=[
                "admin",
                "executive",
                "capture_manager",
                "proposal_manager",
                "pricing_manager",
                "writer",
                "reviewer",
                "contracts_manager",
                "viewer",
            ],
            help="Role for the user (default: viewer)",
        )
        parser.add_argument(
            "--is-staff",
            action="store_true",
            help="Make the user a staff member",
        )
        parser.add_argument(
            "--is-superuser",
            action="store_true",
            help="Make the user a superuser (Django admin)",
        )

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"]
        first_name = options.get("first_name", "")
        last_name = options.get("last_name", "")
        role = options["role"]
        is_staff = options.get("is_staff", False)
        is_superuser = options.get("is_superuser", False)

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists')

        if User.objects.filter(email=email).exists():
            raise CommandError(f'Email "{email}" is already in use')

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created user "{username}" with role "{role}"'
            )
        )
        self.stdout.write(f"  Email: {email}")
        self.stdout.write(f"  Name: {first_name} {last_name}".strip())
