import json
import urllib.error
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from . import drive
from .models import Material
from .serializers import MAX_UPLOAD_SIZE_BYTES, MaterialSerializer

User = get_user_model()

TOKEN_URL = "/api/v1/auth/token/"
MATERIAL_LIST_URL = "/api/v1/material/"
DRIVE_BROWSE_URL = "/api/v1/drive/"
PAGE_SIZE = 20

DRIVE_FILE_URL = "https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345/view"
DRIVE_FILE_ID = "1AbCdEfGhIjKlMnOpQrStUvWxYz012345"
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1FoLdErIdXyZ0123456789ab"
DRIVE_FOLDER_ID = "1FoLdErIdXyZ0123456789ab"
FOLDER_MIME = "application/vnd.google-apps.folder"


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


class LinkMaterialTestCase(MaterialTestCase):
    """Shared setup for link materials: creates a Drive-link row directly."""

    def create_link_material(self, owner=None, title="Lecture recording",
                             source_url=DRIVE_FILE_URL):
        return Material.objects.create(
            title=title,
            course="CS101",
            source_url=source_url,
            drive_file_id=DRIVE_FILE_ID,
            owner=owner or self.lecturer,
        )


class XorValidationTests(LinkMaterialTestCase):
    """Exactly one of `file` / `source_url` must be present, create and update."""

    def test_file_only_returns_201(self):
        self.auth("lecturer")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Slides", "file": pdf_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["source_type"], "file")

    def test_link_only_returns_201(self):
        self.auth("lecturer")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Recording", "source_url": DRIVE_FILE_URL},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["source_type"], "link")
        self.assertEqual(response.data["drive_file_id"], DRIVE_FILE_ID)
        self.assertTrue(response.data["embed_url"].endswith("/preview"))

    def test_neither_source_returns_400(self):
        self.auth("lecturer")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Nothing"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("source_url", response.data)

    def test_both_sources_return_400(self):
        self.auth("lecturer")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Both", "file": pdf_upload(), "source_url": DRIVE_FILE_URL},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("source_url", response.data)

    def test_patch_file_material_adding_link_returns_400(self):
        material = self.create_material()
        self.auth("lecturer")

        response = self.client.patch(
            material_detail_url(material.pk),
            {"source_url": DRIVE_FILE_URL},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("source_url", response.data)

    def test_patch_link_material_clearing_only_source_returns_400(self):
        material = self.create_link_material()
        self.auth("lecturer")

        response = self.client.patch(
            material_detail_url(material.pk),
            {"source_url": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        material.refresh_from_db()
        self.assertEqual(material.source_url, DRIVE_FILE_URL)

    def test_patch_link_material_to_different_link_updates_id(self):
        material = self.create_link_material()
        other_id = "1ZzYyXxWwVvUuTtSsRrQqPpOoNnMm"
        other_url = f"https://drive.google.com/file/d/{other_id}/view"
        self.auth("lecturer")

        response = self.client.patch(
            material_detail_url(material.pk),
            {"source_url": other_url},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        material.refresh_from_db()
        self.assertEqual(material.drive_file_id, other_id)


class DriveHostValidationTests(LinkMaterialTestCase):
    """The serializer is the gatekeeper: only Drive hosts with a real ID pass."""

    def _post(self, url):
        self.auth("lecturer")
        return self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Link", "source_url": url},
            format="json",
        )

    def test_non_drive_host_returns_400(self):
        response = self._post(
            "https://example.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345/view"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_substring_host_trap_returns_400(self):
        response = self._post(
            "https://evil.example.com/drive.google.com/file/d/"
            "1AbCdEfGhIjKlMnOpQrStUvWxYz012345/view"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_id_returns_400(self):
        response = self._post("https://drive.google.com/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_too_short_id_returns_400(self):
        response = self._post("https://drive.google.com/open?id=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_drive_link_returns_201(self):
        response = self._post(DRIVE_FILE_URL)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class DriveIdExtractionTests(LinkMaterialTestCase):
    """IDs are extracted from every supported path and normalized on save."""

    def _post_and_fetch(self, url):
        self.auth("lecturer")
        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Link", "source_url": url},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Material.objects.get(pk=response.data["id"])

    def test_file_path_canonicalized(self):
        material = self._post_and_fetch(DRIVE_FILE_URL)
        self.assertEqual(material.source_url, DRIVE_FILE_URL)
        self.assertEqual(material.drive_file_id, DRIVE_FILE_ID)

    def test_open_query_canonicalized_to_file_view(self):
        material = self._post_and_fetch(
            f"https://drive.google.com/open?id={DRIVE_FILE_ID}"
        )
        self.assertEqual(material.source_url, DRIVE_FILE_URL)
        self.assertEqual(material.drive_file_id, DRIVE_FILE_ID)

    def test_folder_path_canonicalized(self):
        material = self._post_and_fetch(DRIVE_FOLDER_URL)
        self.assertEqual(material.source_url, DRIVE_FOLDER_URL)
        self.assertEqual(material.drive_file_id, DRIVE_FOLDER_ID)

    def test_docs_document_canonicalized_to_file_view(self):
        material = self._post_and_fetch(
            f"https://docs.google.com/document/d/{DRIVE_FILE_ID}/edit"
        )
        self.assertEqual(material.source_url, DRIVE_FILE_URL)

    def test_docs_spreadsheet_canonicalized_to_file_view(self):
        material = self._post_and_fetch(
            f"https://docs.google.com/spreadsheets/d/{DRIVE_FILE_ID}/edit"
        )
        self.assertEqual(material.source_url, DRIVE_FILE_URL)

    def test_http_host_is_accepted(self):
        material = self._post_and_fetch(
            f"http://drive.google.com/file/d/{DRIVE_FILE_ID}/view"
        )
        self.assertEqual(material.drive_file_id, DRIVE_FILE_ID)

    def test_folder_link_has_no_embed(self):
        self.auth("lecturer")
        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Folder", "source_url": DRIVE_FOLDER_URL},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["source_type"], "link")
        self.assertIsNone(response.data["embed_url"])


class SerializerOutputTests(LinkMaterialTestCase):
    """The response exposes the exact fields the frontend consumes."""

    def test_file_material_output(self):
        material = self.create_material()
        self.auth("student")

        response = self.client.get(material_detail_url(material.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source_type"], "file")
        self.assertIsNone(response.data["source_url"])
        self.assertIsNone(response.data["embed_url"])
        self.assertEqual(response.data["drive_file_id"], "")

    def test_link_material_output_without_api_key(self):
        material = self.create_link_material()
        self.auth("student")

        response = self.client.get(material_detail_url(material.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source_type"], "link")
        self.assertTrue(response.data["embed_url"])
        self.assertIsNone(response.data["drive_name"])
        self.assertIsNone(response.data["drive_mime_type"])


class PermissionsUnchangedTests(LinkMaterialTestCase):
    """Link materials keep the same permission model as file materials."""

    def test_student_link_create_returns_403(self):
        self.auth("student")

        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Recording", "source_url": DRIVE_FILE_URL},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_link_create_returns_401(self):
        response = self.client.post(
            MATERIAL_LIST_URL,
            {"title": "Recording", "source_url": DRIVE_FILE_URL},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_can_list_and_read_link_material(self):
        material = self.create_link_material()
        self.auth("student")

        listing = self.client.get(MATERIAL_LIST_URL)
        detail = self.client.get(material_detail_url(material.pk))

        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)

    def test_student_patch_and_delete_link_material_return_403(self):
        material = self.create_link_material()
        self.auth("student")

        patch = self.client.patch(
            material_detail_url(material.pk),
            {"description": "changed"},
            format="json",
        )
        delete = self.client.delete(material_detail_url(material.pk))

        self.assertEqual(patch.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete.status_code, status.HTTP_403_FORBIDDEN)


class DriveModuleTests(SimpleTestCase):
    """Pure unit tests for the credential-optional Drive module (no DB, no net)."""

    def test_parse_returns_none_for_empty_and_bare_id(self):
        self.assertIsNone(drive.parse_drive_url(""))
        self.assertIsNone(drive.parse_drive_url(DRIVE_FILE_ID))

    def test_parse_returns_none_for_non_drive_host(self):
        self.assertIsNone(
            drive.parse_drive_url(f"https://example.com/file/d/{DRIVE_FILE_ID}/view")
        )

    def test_canonical_embed_download_for_file(self):
        ref = drive.parse_drive_url(DRIVE_FILE_URL)
        self.assertEqual(drive.canonical_url(ref), DRIVE_FILE_URL)
        self.assertEqual(
            drive.embed_url(ref),
            f"https://drive.google.com/file/d/{DRIVE_FILE_ID}/preview",
        )
        self.assertEqual(
            drive.download_url(ref),
            f"https://drive.google.com/uc?export=download&id={DRIVE_FILE_ID}",
        )

    def test_canonical_embed_download_for_folder(self):
        ref = drive.parse_drive_url(DRIVE_FOLDER_URL)
        self.assertEqual(drive.canonical_url(ref), DRIVE_FOLDER_URL)
        self.assertIsNone(drive.embed_url(ref))
        self.assertIsNone(drive.download_url(ref))

    def test_is_drive_file_id_uses_shared_charset(self):
        self.assertTrue(drive.is_drive_file_id(DRIVE_FILE_ID))
        self.assertFalse(drive.is_drive_file_id("materials/2026/01/legacy.pdf"))
        self.assertFalse(drive.is_drive_file_id(""))

    @override_settings(GOOGLE_DRIVE_API_KEY="")
    def test_fetch_metadata_without_key_makes_no_call(self):
        with mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            result = drive.fetch_metadata(DRIVE_FILE_ID)

        self.assertIsNone(result)
        urlopen.assert_not_called()


def _fake_response(payload, headers=None):
    """A minimal context-manager HTTP response for patched urlopen."""
    body = json.dumps(payload).encode("utf-8")
    response = mock.MagicMock()
    response.read.return_value = body
    response.headers = headers or {}
    response.__enter__ = lambda self: self
    response.__exit__ = lambda self, *args: False
    return response


class TokenMintingTests(SimpleTestCase):
    """Service-account token minting — urlopen always patched, never real."""

    def setUp(self):
        super().setUp()
        drive._token_cache.clear()

    def tearDown(self):
        drive._token_cache.clear()
        super().tearDown()

    @override_settings(GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="ZmFrZQ==")
    def test_happy_path_returns_token_and_signs_rs256(self):
        with mock.patch.object(
            drive, "_service_account_info",
            return_value={"client_email": "sa@example.com", "private_key": "KEY"},
        ), mock.patch("materials.drive.jwt.encode", return_value="assertion") as encode, \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_response(
                {"access_token": "tok", "expires_in": 3600}
            )
            token = drive.get_access_token()

        self.assertEqual(token, "tok")
        self.assertEqual(encode.call_args.kwargs["algorithm"], "RS256")
        self.assertEqual(urlopen.call_count, 1)

    @override_settings(GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="ZmFrZQ==")
    def test_cache_reuse_avoids_second_call(self):
        with mock.patch.object(
            drive, "_service_account_info",
            return_value={"client_email": "sa@example.com", "private_key": "KEY"},
        ), mock.patch("materials.drive.jwt.encode", return_value="assertion"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_response(
                {"access_token": "tok", "expires_in": 3600}
            )
            first = drive.get_access_token()
            second = drive.get_access_token()

        self.assertEqual(first, second)
        self.assertEqual(urlopen.call_count, 1)

    @override_settings(GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="ZmFrZQ==")
    def test_http_error_propagates_and_caches_nothing(self):
        with mock.patch.object(
            drive, "_service_account_info",
            return_value={"client_email": "sa@example.com", "private_key": "KEY"},
        ), mock.patch("materials.drive.jwt.encode", return_value="assertion"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = urllib.error.HTTPError(
                "https://oauth2.googleapis.com/token", 400, "bad", {}, None
            )
            with self.assertRaises(urllib.error.HTTPError):
                drive.get_access_token()

        self.assertNotIn("access_token", drive._token_cache)

    @override_settings(GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="")
    def test_unconfigured_makes_no_call(self):
        with mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            info = drive._service_account_info()

        self.assertEqual(info, {})
        urlopen.assert_not_called()


class ResumableUploadTests(SimpleTestCase):
    """Resumable upload flow — urlopen patched, session URL + PUT asserted."""

    def setUp(self):
        super().setUp()
        drive._token_cache.clear()

    def tearDown(self):
        drive._token_cache.clear()
        super().tearDown()

    def test_happy_path_returns_id_and_puts_to_session_url(self):
        session_url = "https://upload.example/session"
        with mock.patch("materials.drive.get_access_token", return_value="tok"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = [
                _fake_response({}, headers={"Location": session_url}),
                _fake_response({"id": "newDriveId0123456789"}),
            ]
            file_id = drive.upload_file(
                filename="notes.pdf", data=b"bytes", folder_id="folder1234567890"
            )

        self.assertEqual(file_id, "newDriveId0123456789")
        init_req = urlopen.call_args_list[0].args[0]
        put_req = urlopen.call_args_list[1].args[0]
        self.assertIn("supportsAllDrives=true", init_req.full_url)
        self.assertEqual(put_req.get_method(), "PUT")
        self.assertEqual(put_req.full_url, session_url)

    def test_http_error_propagates(self):
        with mock.patch("materials.drive.get_access_token", return_value="tok"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = urllib.error.HTTPError(
                "https://example", 500, "boom", {}, None
            )
            with self.assertRaises(urllib.error.HTTPError):
                drive.upload_file(
                    filename="notes.pdf", data=b"bytes", folder_id="folder1234567890"
                )


class StorageSelectionTests(SimpleTestCase):
    """STORAGES resolves to Drive only when creds + a target are both present."""

    def test_unconfigured_uses_filesystem_storage(self):
        with override_settings(
            GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="",
            GOOGLE_DRIVE_FOLDER_ID="",
            GOOGLE_DRIVE_SHARED_DRIVE_ID="",
        ):
            from django.core.files.storage import storages

            self.assertEqual(
                storages["default"].__class__.__name__, "FileSystemStorage"
            )

    def test_configured_with_creds_and_folder_uses_drive_storage(self):
        # Mirror the settings-time selection expression on the four vars.
        with override_settings(
            STORAGES={
                "default": {"BACKEND": "materials.storage.GoogleDriveStorage"},
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
                },
            }
        ):
            from django.core.files.storage import storages

            self.assertEqual(
                storages["default"].__class__.__name__, "GoogleDriveStorage"
            )


class DriveStorageBackendTests(SimpleTestCase):
    """The backend's name-based branching keeps legacy rows working, no network."""

    def setUp(self):
        from materials.storage import GoogleDriveStorage

        self.storage = GoogleDriveStorage()

    def test_url_for_drive_id_is_canonical_view(self):
        self.assertEqual(
            self.storage.url(DRIVE_FILE_ID),
            f"https://drive.google.com/file/d/{DRIVE_FILE_ID}/view",
        )

    def test_url_for_legacy_local_name_is_media_url(self):
        from django.conf import settings

        self.assertTrue(
            self.storage.url("materials/2026/01/legacy.pdf").startswith(
                settings.MEDIA_URL
            )
        )

    def test_exists_is_false(self):
        self.assertFalse(self.storage.exists(DRIVE_FILE_ID))

    def test_open_and_size_raise(self):
        with self.assertRaises(NotImplementedError):
            self.storage.open(DRIVE_FILE_ID)
        with self.assertRaises(NotImplementedError):
            self.storage.size(DRIVE_FILE_ID)


class FileMaterialEmbedUrlTests(LinkMaterialTestCase):
    """File materials on Drive storage expose a preview embed (P14)."""

    def test_file_material_with_drive_id_name_has_embed(self):
        material = Material.objects.create(
            title="Stored on Drive",
            course="CS101",
            file=DRIVE_FILE_ID,
            owner=self.lecturer,
        )
        self.auth("student")

        response = self.client.get(material_detail_url(material.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source_type"], "file")
        self.assertTrue(response.data["embed_url"].endswith("/preview"))

    def test_file_material_with_legacy_name_has_no_embed(self):
        material = self.create_material()
        self.auth("student")

        response = self.client.get(material_detail_url(material.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["embed_url"])


class DriveBrowseEndpointTests(LinkMaterialTestCase):
    """GET /api/v1/drive/ — 401 anonymous, 503 unconfigured, 200/502 when set."""

    def test_anonymous_returns_401(self):
        response = self.client.get(DRIVE_BROWSE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="")
    def test_unconfigured_returns_503_with_zero_outbound_calls(self):
        self.auth("student")
        with mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            response = self.client.get(DRIVE_BROWSE_URL)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(
            response.data["detail"], "Drive integration is not configured."
        )
        urlopen.assert_not_called()

    @override_settings(
        GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="ZmFrZQ==",
        GOOGLE_DRIVE_FOLDER_ID="rootFolder012345678",
        GOOGLE_DRIVE_SHARED_DRIVE_ID="",
    )
    def test_configured_returns_folder_and_file_entries(self):
        self.auth("student")
        page = {
            "files": [
                {"id": "folderXyz0123456789", "name": "Notes", "mimeType": FOLDER_MIME},
                {"id": DRIVE_FILE_ID, "name": "week1.pdf", "mimeType": "application/pdf"},
            ]
        }
        with mock.patch("materials.drive.get_access_token", return_value="tok"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_response(page)
            response = self.client.get(DRIVE_BROWSE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["configured"])
        self.assertEqual(len(response.data["results"]), 2)
        folder, file_entry = response.data["results"]
        self.assertTrue(folder["isFolder"])
        self.assertIn("/drive/folders/", folder["url"])
        self.assertFalse(file_entry["isFolder"])
        self.assertTrue(file_entry["url"].endswith("/view"))
        self.assertFalse(response.data["truncated"])

    @override_settings(
        GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="ZmFrZQ==",
        GOOGLE_DRIVE_FOLDER_ID="rootFolder012345678",
        GOOGLE_DRIVE_SHARED_DRIVE_ID="",
    )
    def test_parent_param_is_used_in_query(self):
        self.auth("student")
        parent_id = "subFolder0123456789"
        with mock.patch("materials.drive.get_access_token", return_value="tok"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_response({"files": []})
            response = self.client.get(DRIVE_BROWSE_URL, {"parent": parent_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sent_url = urlopen.call_args.args[0].full_url
        self.assertIn(f"'{parent_id}'", urllib.parse.unquote(sent_url))
        self.assertEqual(response.data["parent"], parent_id)

    @override_settings(
        GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="ZmFrZQ==",
        GOOGLE_DRIVE_FOLDER_ID="rootFolder012345678",
        GOOGLE_DRIVE_SHARED_DRIVE_ID="",
    )
    def test_next_page_token_sets_truncated(self):
        self.auth("student")
        with mock.patch("materials.drive.get_access_token", return_value="tok"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_response(
                {"files": [], "nextPageToken": "tok2"}
            )
            response = self.client.get(DRIVE_BROWSE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["truncated"])

    @override_settings(
        GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="ZmFrZQ==",
        GOOGLE_DRIVE_FOLDER_ID="rootFolder012345678",
        GOOGLE_DRIVE_SHARED_DRIVE_ID="",
    )
    def test_drive_error_returns_502(self):
        self.auth("student")
        with mock.patch("materials.drive.get_access_token", return_value="tok"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = urllib.error.HTTPError(
                "https://www.googleapis.com", 500, "boom", {}, None
            )
            response = self.client.get(DRIVE_BROWSE_URL)

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.data["detail"], "Drive API error.")


class DriveBrowseServiceTests(SimpleTestCase):
    """Pure unit tests for the browse service helpers (no real network)."""

    def test_is_folder_mime(self):
        self.assertTrue(drive.is_folder_mime(FOLDER_MIME))
        self.assertFalse(drive.is_folder_mime("application/pdf"))

    @override_settings(GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="")
    def test_is_configured_false_with_no_creds(self):
        with mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            self.assertFalse(drive.is_configured())
        urlopen.assert_not_called()

    @override_settings(GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="ZmFrZQ==")
    def test_is_configured_true_with_creds(self):
        self.assertTrue(drive.is_configured())

    @override_settings(
        GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="ZmFrZQ==",
        GOOGLE_DRIVE_FOLDER_ID="rootFolder012345678",
        GOOGLE_DRIVE_SHARED_DRIVE_ID="",
    )
    def test_list_children_targets_configured_folder(self):
        with mock.patch("materials.drive.get_access_token", return_value="tok"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_response({"files": []})
            parent, results, truncated = drive.list_children("")

        sent = urllib.parse.unquote_plus(urlopen.call_args.args[0].full_url)
        self.assertIn("'rootFolder012345678' in parents", sent)
        self.assertNotIn("corpora=drive", sent)
        self.assertEqual(parent, "rootFolder012345678")
        self.assertEqual(results, [])
        self.assertFalse(truncated)

    @override_settings(
        GOOGLE_DRIVE_SERVICE_ACCOUNT_B64="ZmFrZQ==",
        GOOGLE_DRIVE_FOLDER_ID="",
        GOOGLE_DRIVE_SHARED_DRIVE_ID="sharedDrive0123456789",
    )
    def test_list_children_shared_drive_params_without_folder(self):
        with mock.patch("materials.drive.get_access_token", return_value="tok"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_response({"files": []})
            parent, results, truncated = drive.list_children("")

        sent = urllib.parse.unquote(urlopen.call_args.args[0].full_url)
        self.assertIn("driveId=sharedDrive0123456789", sent)
        self.assertIn("corpora=drive", sent)
        self.assertNotIn("in parents", sent)
        self.assertIsNone(parent)


class DeleteFileBestEffortTests(SimpleTestCase):
    """`drive.delete_file` never raises: a Drive-side failure is swallowed."""

    def _delete(self, side_effect):
        with mock.patch("materials.drive.get_access_token", return_value="tok"), \
             mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = side_effect
            result = drive.delete_file(DRIVE_FILE_ID)
        return result, urlopen

    def test_success_returns_none_and_calls_once(self):
        result, urlopen = self._delete(None)

        self.assertIsNone(result)
        self.assertEqual(urlopen.call_count, 1)

    def test_http_404_is_swallowed(self):
        result, _ = self._delete(
            urllib.error.HTTPError("https://www.googleapis.com", 404, "Not Found", {}, None)
        )
        self.assertIsNone(result)

    def test_http_500_is_swallowed(self):
        result, _ = self._delete(
            urllib.error.HTTPError("https://www.googleapis.com", 500, "boom", {}, None)
        )
        self.assertIsNone(result)

    def test_url_error_is_swallowed(self):
        result, _ = self._delete(urllib.error.URLError("unreachable"))
        self.assertIsNone(result)

    def test_token_mint_failure_is_swallowed(self):
        # The token exchange is the first network hop of a delete; if it fails
        # the row is already gone, so it must not resurface as a 500.
        with mock.patch(
            "materials.drive.get_access_token", side_effect=RuntimeError("no token")
        ), mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            result = drive.delete_file(DRIVE_FILE_ID)

        self.assertIsNone(result)
        urlopen.assert_not_called()


class MaterialDeleteToleranceTests(MaterialTestCase):
    """Regression: a Drive delete failure must not 500 an already-deleted row."""

    def test_lecturer_delete_succeeds_when_drive_delete_fails(self):
        material = Material.objects.create(
            title="Stored on Drive",
            course="CS101",
            file=DRIVE_FILE_ID,
            owner=self.lecturer,
        )
        self.auth("lecturer")

        with mock.patch(
            "materials.storage.drive.delete_file",
            side_effect=urllib.error.HTTPError(
                "https://www.googleapis.com", 500, "boom", {}, None
            ),
        ):
            response = self.client.delete(material_detail_url(material.pk))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Material.objects.filter(pk=material.pk).exists())


class FileReplacementTests(MaterialTestCase):
    """PATCH replacing `file` deletes the previous object instead of orphaning it."""

    def test_patch_replacing_file_deletes_old_object(self):
        material = self.create_material()
        old_path = material.file.path
        self.assertTrue(material.file.storage.exists(material.file.name))
        self.auth("lecturer")

        response = self.client.patch(
            material_detail_url(material.pk),
            {"title": "Updated", "file": pdf_upload("replacement.pdf")},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        material.refresh_from_db()
        self.assertNotEqual(material.file.path, old_path)
        self.assertFalse(material.file.storage.exists(old_path))

    def test_metadata_only_patch_keeps_file(self):
        material = self.create_material()
        stored_name = material.file.name
        self.auth("lecturer")

        response = self.client.patch(
            material_detail_url(material.pk),
            {"description": "notes"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        material.refresh_from_db()
        self.assertEqual(material.file.name, stored_name)

    def test_storage_delete_failure_does_not_break_patch(self):
        material = self.create_material()
        self.auth("lecturer")

        with mock.patch(
            "django.core.files.storage.FileSystemStorage.delete",
            side_effect=OSError("disk error"),
        ):
            response = self.client.patch(
                material_detail_url(material.pk),
                {"file": pdf_upload("replacement.pdf")},
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SourceXorConstraintTests(MaterialTestCase):
    """The DB backstops the serializer's exactly-one-source rule."""

    def test_both_sources_violate_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Material.objects.create(
                title="Both",
                file=DRIVE_FILE_ID,
                source_url=DRIVE_FILE_URL,
                owner=self.lecturer,
            )

    def test_neither_source_violates_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Material.objects.create(title="Neither", owner=self.lecturer)

    def test_file_only_row_is_accepted(self):
        material = Material.objects.create(
            title="File only", file=DRIVE_FILE_ID, owner=self.lecturer
        )
        self.assertIsNotNone(material.pk)

    def test_link_only_row_is_accepted(self):
        material = Material.objects.create(
            title="Link only",
            source_url=DRIVE_FILE_URL,
            drive_file_id=DRIVE_FILE_ID,
            owner=self.lecturer,
        )
        self.assertIsNotNone(material.pk)


class MetadataCacheTests(SimpleTestCase):
    """B4: successful Drive metadata lookups are cached; failures never are."""

    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        cache.clear()
        super().tearDown()

    @override_settings(GOOGLE_DRIVE_API_KEY="fake-key")
    def test_cache_hit_avoids_second_outbound_call(self):
        with mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_response(
                {"name": "week1.pdf", "mimeType": "application/pdf"}
            )
            first = drive.fetch_metadata(DRIVE_FILE_ID)
            second = drive.fetch_metadata(DRIVE_FILE_ID)

        self.assertEqual(first, {"name": "week1.pdf", "mime_type": "application/pdf"})
        self.assertEqual(second, first)
        self.assertEqual(urlopen.call_count, 1)

    @override_settings(GOOGLE_DRIVE_API_KEY="fake-key")
    def test_failure_is_not_cached(self):
        with mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = [
                urllib.error.HTTPError("https://www.googleapis.com", 503, "boom", {}, None),
                _fake_response({"name": "week1.pdf", "mimeType": "application/pdf"}),
            ]
            first = drive.fetch_metadata(DRIVE_FILE_ID)
            second = drive.fetch_metadata(DRIVE_FILE_ID)

        self.assertIsNone(first)
        self.assertEqual(second, {"name": "week1.pdf", "mime_type": "application/pdf"})
        self.assertEqual(urlopen.call_count, 2)

    @override_settings(GOOGLE_DRIVE_API_KEY="")
    def test_unconfigured_makes_no_call_and_writes_no_cache(self):
        with mock.patch("materials.drive.urllib.request.urlopen") as urlopen:
            first = drive.fetch_metadata(DRIVE_FILE_ID)
            second = drive.fetch_metadata(DRIVE_FILE_ID)

        self.assertIsNone(first)
        self.assertIsNone(second)
        urlopen.assert_not_called()
        self.assertIsNone(cache.get(drive._metadata_cache_key(DRIVE_FILE_ID)))


class SerializerMetadataSingleFetchTests(LinkMaterialTestCase):
    """The two drive_* fields resolve one metadata fetch per object."""

    @override_settings(GOOGLE_DRIVE_API_KEY="fake-key")
    def test_two_drive_fields_fetch_once(self):
        cache.clear()
        material = self.create_link_material()
        with mock.patch(
            "materials.drive.fetch_metadata",
            return_value={"name": "week1.pdf", "mime_type": "application/pdf"},
        ) as fetch:
            data = MaterialSerializer(material).data

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(data["drive_name"], "week1.pdf")
        self.assertEqual(data["drive_mime_type"], "application/pdf")
        cache.clear()
