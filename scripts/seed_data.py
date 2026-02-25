#!/usr/bin/env python
"""Seed initial data for development."""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
django.setup()

from apps.accounts.models import User, UserProfile  # noqa: E402


def create_demo_users():
    """Create demo users with different roles."""
    demo_users = [
        {"username": "admin", "email": "admin@dealmanager.ai", "role": "admin",
         "first_name": "System", "last_name": "Admin"},
        {"username": "exec", "email": "exec@dealmanager.ai", "role": "executive",
         "first_name": "Jane", "last_name": "Executive"},
        {"username": "capture", "email": "capture@dealmanager.ai", "role": "capture_manager",
         "first_name": "John", "last_name": "Capture"},
        {"username": "proposal", "email": "proposal@dealmanager.ai", "role": "proposal_manager",
         "first_name": "Sarah", "last_name": "Proposal"},
        {"username": "pricing", "email": "pricing@dealmanager.ai", "role": "pricing_manager",
         "first_name": "Mike", "last_name": "Pricing"},
        {"username": "writer", "email": "writer@dealmanager.ai", "role": "writer",
         "first_name": "Emily", "last_name": "Writer"},
        {"username": "reviewer", "email": "reviewer@dealmanager.ai", "role": "reviewer",
         "first_name": "David", "last_name": "Reviewer"},
    ]

    for data in demo_users:
        role = data.pop("role")
        user, created = User.objects.get_or_create(
            username=data["username"],
            defaults={**data, "role": role},
        )
        if created:
            user.set_password("DemoPass123!")
            user.role = role
            user.save()
            print(f"  Created user: {user.username} ({role})")
        else:
            print(f"  User already exists: {user.username}")


def main():
    print("Seeding demo data...")
    print("\n--- Users ---")
    create_demo_users()
    print("\nDone! All demo users have password: DemoPass123!")


if __name__ == "__main__":
    main()
