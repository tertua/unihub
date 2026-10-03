from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

REGISTER_URL = "/api/v1/auth/register/"
TOKEN_URL = "/api/v1/auth/token/"
REFRESH_URL = "/api/v1/auth/token/refresh/"
ME_URL = "/api/v1/auth/me/"

# Passes Django's default validators (length, similarity, common/numeric).
PASSWORD = "Hub-Learning-2026!"


class RegisterTests(APITestCase):
    def test_register_student_returns_201_and_hashes_password(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "alice", "password": PASSWORD, "role": "student"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "student")
        self.assertNotIn("password", response.data)

        user = User.objects.get(username="alice")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertTrue(user.has_usable_password())

    def test_register_lecturer_is_allowed(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "dr_budi", "password": PASSWORD, "role": "lecturer"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "lecturer")

    def test_register_rejects_admin_role(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "root", "password": PASSWORD, "role": "admin"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)
        self.assertFalse(User.objects.filter(username="root").exists())

    def test_register_rejects_duplicate_username(self):
        User.objects.create_user(username="alice", password=PASSWORD)

        response = self.client.post(
            REGISTER_URL,
            {"username": "alice", "password": PASSWORD, "role": "student"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_register_rejects_duplicate_student_id_number(self):
        User.objects.create_user(
            username="alice", password=PASSWORD, student_id_number="2026001"
        )

        response = self.client.post(
            REGISTER_URL,
            {
                "username": "bob",
                "password": PASSWORD,
                "role": "student",
                "student_id_number": "2026001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("student_id_number", response.data)

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "alice", "password": "123", "role": "student"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(username="alice").exists())

    def test_register_requires_password(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "alice", "role": "student"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)


class TokenTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", password=PASSWORD, role="student"
        )

    def test_login_returns_jwt_pair(self):
        response = self.client.post(
            TOKEN_URL,
            {"username": "alice", "password": PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            TOKEN_URL,
            {"username": "alice", "password": "wrong-password-123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)

    def test_refresh_returns_new_access_token(self):
        tokens = self.client.post(
            TOKEN_URL,
            {"username": "alice", "password": PASSWORD},
            format="json",
        ).data

        response = self.client.post(
            REFRESH_URL,
            {"refresh": tokens["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_rejects_invalid_token(self):
        response = self.client.post(
            REFRESH_URL,
            {"refresh": "not-a-real-token"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ModelTests(APITestCase):
    def test_superuser_is_forced_to_admin_role(self):
        # createsuperuser leaves the model default (student) behind.
        user = User.objects.create_superuser(username="root", password=PASSWORD)

        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role, User.Role.ADMIN)


class MeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password=PASSWORD,
            role="student",
            student_id_number="2026001",
            study_program="Teknik Informatika",
        )
        self.access = self.client.post(
            TOKEN_URL,
            {"username": "alice", "password": PASSWORD},
            format="json",
        ).data["access"]

    def auth(self, token=None):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token or self.access}")

    def test_me_requires_authentication(self):
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_rejects_garbage_token(self):
        self.auth("garbage-token")

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_own_profile(self):
        self.auth()

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "alice")
        self.assertEqual(response.data["role"], "student")
        self.assertEqual(response.data["student_id_number"], "2026001")
        self.assertEqual(response.data["study_program"], "Teknik Informatika")

    def test_me_patch_updates_profile(self):
        self.auth()

        response = self.client.patch(
            ME_URL,
            {"study_program": "Sistem Informasi", "first_name": "Alice"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.study_program, "Sistem Informasi")
        self.assertEqual(self.user.first_name, "Alice")

    def test_me_patch_cannot_change_identity_fields(self):
        self.auth()

        response = self.client.patch(
            ME_URL,
            {
                "role": "admin",
                "username": "hacker",
                "lecturer_id_number": "1987001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "student")
        self.assertEqual(self.user.username, "alice")
        self.assertIsNone(self.user.lecturer_id_number)
