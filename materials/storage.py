"""Django storage backend that writes Material files to a Google Shared Drive.

The stored name is the Drive file ID (P13). Selection is credential-gated in
settings (P11); when unconfigured, settings pick FileSystemStorage instead, so
this class is only active in a properly configured environment.
"""

from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from . import drive


@deconstructible
class GoogleDriveStorage(Storage):
    """Uploads bytes to Drive and returns the Drive file ID as the name."""

    def save(self, name, content, max_length=None):
        """Resumable-upload `content` to Drive; return the new file id."""
        data = content.read()
        file_id = drive.upload_file(
            filename=name,
            data=data,
            folder_id=settings.GOOGLE_DRIVE_FOLDER_ID,
            shared_drive_id=settings.GOOGLE_DRIVE_SHARED_DRIVE_ID,
        )
        return file_id  # stored name == Drive file id (P13)

    def url(self, name):
        # Drive id -> canonical view URL; legacy local path -> local media URL.
        if drive.is_drive_file_id(name):
            return drive.file_view_url(name)
        return settings.MEDIA_URL + name.lstrip("/")

    def exists(self, name):
        # Write-only use: we never need to probe Drive. Returning False is the
        # honest "not tracked here" answer and avoids a per-call network hit (P12).
        return False

    def delete(self, name):
        if drive.is_drive_file_id(name):
            drive.delete_file(name)
            return
        # Legacy local name: nothing to do on Drive.
        return None

    def open(self, name, mode="rb"):
        raise NotImplementedError(
            "GoogleDriveStorage.open is intentionally unimplemented: nothing in "
            "the API or admin reads file bytes back — files are opened from Drive "
            "directly by the browser. See docs/adr/003-google-shared-drive-storage.md."
        )

    def size(self, name):
        raise NotImplementedError(
            "GoogleDriveStorage.size is intentionally unimplemented: size is not "
            "exposed by the Material API; Drive metadata is the source of truth. "
            "See docs/adr/003-google-shared-drive-storage.md."
        )
