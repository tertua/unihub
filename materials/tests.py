from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Material
from .serializers import MAX_UPLOAD_SIZE_BYTES

User = get_user_model()

TOKEN_URL = "/api/v1/auth/token/"
MATERIAL_LIST_URL = "/api/v1/material/"
PAGE_SIZE = 20


def material_detail_url(pk):
    return f"/api/v1/material/{pk}/"


def pdf_upload(name="lecture.pdf"):
    """Minimal bytes carrying the declared content type of a real PDF."""
    return SimpleUploadedFile(name, b"%PDF-1.4 minimal", content_type="application/pdf")


class MaterialTestCase(APITestCase):
    """Shared setup: JWT helper plus the three roles the API distinguishes."""

    def setUp(self):
        self.lecturer = User.objects.create_user(
            username="lecturer", password="Str0ng-Passw0rd!", role="lecturer"
        )
        self.student = User.objects.create_user(
            username="student", password="Str0ng-Passw0rd!", role="student"
        )
        self.admin = User.objects.create_user(
            username="admin", password="Str0ng-Passw0rd!", role="admin"
        )

    def token_for(self, username):
        return self.client.post(
            TOKEN_URL,
            {"username": username, "password": "Str0ng-Passw0rd!"},
            format="json",
        ).data["access"]

    def auth(self, username):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_for(username)}")

    def create_material(self, owner=None, title="Lecture slides"):
        return Material.objects.create(
            title=title,
            course="CS101",
            file=pdf_upload(),
            owner=owner or self.lecturer,
        )


class PermissionTests(MaterialTestCase):
    def test_lecturer_upload_returns_201(self):
        self.auth("lecturer")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Lecture slides", "file": pdf_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_upload_returns_403(self):
        self.auth("student")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Lecture slides", "file": pdf_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_upload_returns_401(self):
        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Lecture slides", "file": pdf_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_can_list_materials(self):
        self.create_material()
        self.auth("student")

        response = self.client.get(MATERIAL_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_can_read_detail(self):
        material = self.create_material()
        self.auth("student")

        response = self.client.get(material_detail_url(material.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_patch_returns_403(self):
        material = self.create_material()
        self.auth("student")

        response = self.client.patch(
            material_detail_url(material.pk),
            {"description": "changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_delete_returns_403(self):
        material = self.create_material()
        self.auth("student")

        response = self.client.delete(material_detail_url(material.pk))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_detail_returns_401(self):
        material = self.create_material()

        response = self.client.get(material_detail_url(material.pk))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UploadValidationTests(MaterialTestCase):
    def test_missing_file_returns_400(self):
        self.auth("lecturer")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "No file"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_missing_title_returns_400(self):
        self.auth("lecturer")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"file": pdf_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_blank_title_returns_400(self):
        self.auth("lecturer")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "   ", "file": pdf_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_disallowed_extension_returns_400(self):
        self.auth("lecturer")
        upload = SimpleUploadedFile(
            "malware.exe", b"MZ", content_type="application/octet-stream"
        )

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Bad file", "file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_oversized_file_returns_400(self):
        self.auth("lecturer")
        oversized = SimpleUploadedFile(
            "huge.pdf",
            b"0" * (MAX_UPLOAD_SIZE_BYTES + 1),
            content_type="application/pdf",
        )

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Too big", "file": oversized},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_valid_pdf_sets_owner_to_requester(self):
        self.auth("lecturer")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Lecture slides", "file": pdf_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"], self.lecturer.pk)
        self.assertTrue(
            Material.objects.filter(pk=response.data["id"], owner=self.lecturer).exists()
        )


class ListSearchTests(MaterialTestCase):
    def test_pagination_returns_count_and_page(self):
        for index in range(PAGE_SIZE + 1):
            self.create_material(title=f"Material {index}")
        self.auth("student")

        response = self.client.get(MATERIAL_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], PAGE_SIZE + 1)
        self.assertEqual(len(response.data["results"]), PAGE_SIZE)

    def test_search_matches_title(self):
        self.create_material(title="Quantum mechanics")
        self.create_material(title="Linear algebra")
        self.auth("student")

        response = self.client.get(MATERIAL_LIST_URL, {"search": "Quantum"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Quantum mechanics")

    def test_search_matches_description(self):
        material = self.create_material(title="Week 3")
        material.description = "Introduction to thermodynamics"
        material.save()
        self.create_material(title="Week 4")
        self.auth("student")

        response = self.client.get(MATERIAL_LIST_URL, {"search": "thermodynamics"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], material.pk)

    def test_search_without_match_returns_empty_results(self):
        self.create_material(title="Quantum mechanics")
        self.auth("student")

        response = self.client.get(MATERIAL_LIST_URL, {"search": "biology"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])


class DetailUpdateDeleteTests(MaterialTestCase):
    def test_lecturer_patch_updates_metadata(self):
        material = self.create_material()
        self.auth("lecturer")

        response = self.client.patch(
            material_detail_url(material.pk),
            {"description": "Updated notes", "course": "CS202"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        material.refresh_from_db()
        self.assertEqual(material.description, "Updated notes")
        self.assertEqual(material.course, "CS202")

    def test_admin_patch_updates_metadata(self):
        material = self.create_material()
        self.auth("admin")

        response = self.client.patch(
            material_detail_url(material.pk),
            {"description": "Admin edit"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        material.refresh_from_db()
        self.assertEqual(material.description, "Admin edit")

    def test_lecturer_delete_returns_204(self):
        material = self.create_material()
        self.auth("lecturer")

        response = self.client.delete(material_detail_url(material.pk))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Material.objects.filter(pk=material.pk).exists())

    def test_patch_cannot_change_owner(self):
        material = self.create_material(owner=self.lecturer)
        self.auth("lecturer")

        response = self.client.patch(
            material_detail_url(material.pk),
            {"owner": self.student.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        material.refresh_from_db()
        self.assertEqual(material.owner, self.lecturer)
