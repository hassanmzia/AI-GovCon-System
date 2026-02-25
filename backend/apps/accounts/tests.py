"""Tests for accounts app: JWT auth endpoints and user management."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AuthTokenTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
            role=User.Role.CAPTURE_MANAGER,
        )

    def test_obtain_token_success(self):
        resp = self.client.post(
            "/api/auth/token/", {"username": "testuser", "password": "TestPass123!"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_obtain_token_wrong_password(self):
        resp = self.client.post(
            "/api/auth/token/", {"username": "testuser", "password": "WrongPass"}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtain_token_nonexistent_user(self):
        resp = self.client.post(
            "/api/auth/token/", {"username": "nobody", "password": "whatever"}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_authenticated(self):
        resp = self.client.post(
            "/api/auth/token/", {"username": "testuser", "password": "TestPass123!"}
        )
        token = resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["username"], "testuser")
        self.assertEqual(me.data["role"], User.Role.CAPTURE_MANAGER)

    def test_me_endpoint_unauthenticated(self):
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        resp = self.client.post(
            "/api/auth/token/", {"username": "testuser", "password": "TestPass123!"}
        )
        refresh = resp.data["refresh"]
        refresh_resp = self.client.post("/api/auth/token/refresh/", {"refresh": refresh})
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_resp.data)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(
            "/api/auth/token/", {"username": "testuser", "password": "TestPass123!"}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class UserModelTests(TestCase):
    def test_create_user_default_role(self):
        user = User.objects.create_user(
            username="viewer1", email="viewer@example.com", password="pass"
        )
        self.assertEqual(user.role, User.Role.VIEWER)
        self.assertFalse(user.is_mfa_enabled)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_str(self):
        user = User.objects.create_user(
            username="capture1", email="c@example.com", password="p",
            role=User.Role.CAPTURE_MANAGER,
        )
        self.assertIn("capture1", str(user))
        self.assertIn("Capture Manager", str(user))
