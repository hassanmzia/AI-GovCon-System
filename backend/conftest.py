import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    from apps.accounts.models import User

    def _create_user(username="testuser", email="test@example.com", password="TestPass123!", role="viewer", **kwargs):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            **kwargs,
        )
        return user

    return _create_user


@pytest.fixture
def authenticated_client(api_client, create_user):
    user = create_user()
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, create_user):
    user = create_user(username="admin", email="admin@example.com", role="admin")
    api_client.force_authenticate(user=user)
    return api_client
