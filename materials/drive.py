"""Google Drive integration service module.

Pure helpers that parse/normalize Drive URLs and build canonical view/embed/
download URLs, plus optional metadata enrichment and — from the storage phase —
service-account token minting, resumable upload, and a read-only folder listing
for the in-app browser.

Credential-optional by design (graceful degradation is mandatory): with no
credentials configured, parse/normalize/URL-building all work with **zero
outbound calls**, `fetch_metadata` returns `None`, and callers that need a
token (upload, browse) must check `is_configured()` first and make no call when
it is `False`.

The module reads `settings.GOOGLE_DRIVE_*` lazily (inside functions) so
`override_settings` works cleanly in tests.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Literal

import jwt

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# --- Token minting (service account, OAuth2 JWT-bearer) ---------------------

_TOKEN_SCOPE = "https://www.googleapis.com/auth/drive"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_TOKEN_MARGIN_SECONDS = 300  # refresh at exp - 5 min
_TOKEN_GRANT = "urn:ietf:params:oauth:grant-type:jwt-bearer"

_UPLOAD_ENDPOINT = "https://www.googleapis.com/upload/drive/v3/files"

_FOLDER_MIME = "application/vnd.google-apps.folder"
_LIST_FIELDS = "nextPageToken, files(id, name, mimeType)"
_LIST_ENDPOINT = "https://www.googleapis.com/drive/v3/files"
_BROWSE_PAGE_SIZE = 100

# Metadata enrichment is best-effort and cheap to recompute; 5 minutes matches
# the token-refresh margin and keeps a renamed/moved file self-healing quickly
# while sparing a list page plus the following detail view a second fetch.
_METADATA_TTL_SECONDS = 300

# In-process cache: {"access_token": str, "expires_at": float (epoch seconds)}
_token_cache: dict = {}

# Drive IDs are ~33 chars; a 10-char floor safely rejects `?id=abc` while
# staying permissive for shorter (older) IDs.
_ID_CHARSET = r"[A-Za-z0-9_-]{10,}"
DRIVE_ID_RE = re.compile(rf"^{_ID_CHARSET}$")

_ALLOWED_HOSTS = {"drive.google.com", "docs.google.com"}

# Ordered: specific document paths before generic ones.
_PATH_PATTERNS = (
    re.compile(rf"^/(?:[a-z]+/)?file/d/(?P<id>{_ID_CHARSET})"),
    re.compile(rf"^/document/d/(?P<id>{_ID_CHARSET})"),
    re.compile(rf"^/spreadsheets/d/(?P<id>{_ID_CHARSET})"),
    re.compile(rf"^/presentation/d/(?P<id>{_ID_CHARSET})"),
)
_FOLDER_PATTERNS = (
    re.compile(rf"^/(?:drive/)?folders/(?P<id>{_ID_CHARSET})"),
)
_OPEN_PATTERNS = (
    re.compile(rf"^/open$"),
    re.compile(rf"^/uc$"),
)

DriveKind = Literal["file", "folder"]


@dataclass(frozen=True)
class DriveRef:
    """A parsed Drive identity: the file/folder id plus what kind it is."""

    file_id: str
    kind: DriveKind


def _normalized_host(netloc: str) -> str:
    host = netloc.lower().split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def parse_drive_url(raw: str) -> DriveRef | None:
    """Parse a Drive URL into a `DriveRef`, or `None` when not a Drive link.

    Accepts only the allow-listed hosts (`drive.google.com`, `docs.google.com`,
    case-insensitive, optional `www.`, https or http). Returns `None` for any
    other host or any URL whose ID cannot be recognized.
    """
    if not raw or not isinstance(raw, str):
        return None
    try:
        parts = urllib.parse.urlsplit(raw.strip())
    except ValueError:
        return None
    if parts.scheme not in ("http", "https"):
        return None
    if _normalized_host(parts.netloc) not in _ALLOWED_HOSTS:
        return None

    path = parts.path

    # Query-based IDs: /open?id=... and /uc?id=...
    if any(pattern.match(path) for pattern in _OPEN_PATTERNS):
        query = urllib.parse.parse_qs(parts.query)
        candidate = (query.get("id") or [""])[0]
        if DRIVE_ID_RE.match(candidate):
            return DriveRef(file_id=candidate, kind="file")

    for pattern in _FOLDER_PATTERNS:
        match = pattern.match(path)
        if match:
            return DriveRef(file_id=match.group("id"), kind="folder")

    for pattern in _PATH_PATTERNS:
        match = pattern.match(path)
        if match:
            return DriveRef(file_id=match.group("id"), kind="file")

    return None


def canonical_url(ref: DriveRef) -> str:
    """Canonical, normalized URL for a parsed reference."""
    if ref.kind == "folder":
        return folder_view_url(ref.file_id)
    return file_view_url(ref.file_id)


def embed_url(ref: DriveRef) -> str | None:
    """Embeddable preview URL, or `None` when Drive has no reliable embed."""
    if ref.kind == "file":
        return file_embed_url(ref.file_id)
    return None


def download_url(ref: DriveRef) -> str | None:
    """Direct-download URL for a file, or `None` for a folder."""
    if ref.kind == "file":
        return f"https://drive.google.com/uc?export=download&id={ref.file_id}"
    return None


def is_drive_file_id(name: str) -> bool:
    """True when `name` looks like a Drive id (not a legacy local path)."""
    return bool(name) and DRIVE_ID_RE.match(name) is not None


def file_view_url(file_id: str) -> str:
    return f"https://drive.google.com/file/d/{file_id}/view"


def file_embed_url(file_id: str) -> str:
    return f"https://drive.google.com/file/d/{file_id}/preview"


def folder_view_url(folder_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"


def is_configured() -> bool:
    """True when the service account is present (can mint a Drive token).

    The storage/upload and browse paths need a *token* (service account), not
    the optional API key. Unconfigured -> callers must make zero outbound calls
    and render an honest "not configured" state.
    """
    return bool(settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_B64)


def _metadata_cache_key(file_id: str) -> str:
    """Namespaced, stable cache key for one Drive file's metadata."""
    return f"drive_meta:{file_id}"


def fetch_metadata(file_id: str) -> dict | None:
    """Best-effort metadata lookup for `file_id`, or `None`.

    Only runs when an API key is configured; every failure is swallowed so a
    dead Google endpoint can never break a read. Successful lookups are cached
    for `_METADATA_TTL_SECONDS`; failures are **never** cached, so a transient
    outage cannot pin `None` for the whole TTL. Returns
    `{"name": ..., "mime_type": ...}`.
    """
    api_key = settings.GOOGLE_DRIVE_API_KEY
    # Unconfigured must stay zero-network and zero-cache (hard contract).
    if not api_key or not file_id:
        return None

    cache_key = _metadata_cache_key(file_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = (
        "https://www.googleapis.com/drive/v3/files/"
        f"{urllib.parse.quote(file_id)}?fields=name,mimeType&key="
        f"{urllib.parse.quote(api_key)}"
    )
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    result = {
        "name": payload.get("name"),
        "mime_type": payload.get("mimeType"),
    }
    # Cache successes only: a failure must not be pinned for the whole TTL.
    cache.set(cache_key, result, _METADATA_TTL_SECONDS)
    return result


def _service_account_info() -> dict:
    """Decode `settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_B64` (lazy read)."""
    raw = settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_B64
    if not raw:
        return {}
    return json.loads(base64.b64decode(raw).decode("utf-8"))


def _build_assertion(info: dict) -> str:
    now = int(time.time())
    claims = {
        "iss": info["client_email"],
        "scope": _TOKEN_SCOPE,
        "aud": _TOKEN_ENDPOINT,
        "iat": now,
        "exp": now + 3600,
    }
    # RS256 requires the `cryptography` backend (declared in requirements).
    return jwt.encode(claims, info["private_key"], algorithm="RS256")


def get_access_token() -> str:
    """Return a cached or freshly minted service-account access token.

    Caches until `expires_at` (with a 5-minute margin). Reads settings lazily so
    `override_settings` works in tests.
    """
    cached = _token_cache.get("access_token")
    if cached and time.time() < _token_cache.get("expires_at", 0):
        return cached
    info = _service_account_info()
    assertion = _build_assertion(info)
    body = urllib.parse.urlencode({
        "grant_type": _TOKEN_GRANT,
        "assertion": assertion,
    }).encode("ascii")
    req = urllib.request.Request(
        _TOKEN_ENDPOINT,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    token = payload["access_token"]
    _token_cache["access_token"] = token
    _token_cache["expires_at"] = (
        time.time() + int(payload.get("expires_in", 3600)) - _TOKEN_MARGIN_SECONDS
    )
    return token


def _authorized_request(url, *, method, data=None, headers=None):
    headers = dict(headers or {})
    headers["Authorization"] = f"Bearer {get_access_token()}"
    return urllib.request.Request(url, data=data, headers=headers, method=method)


def upload_file(filename, data: bytes, folder_id: str, shared_drive_id: str = "") -> str:
    """Resumable-upload `data` to `folder_id`; return the new Drive file id.

    Resumable (not simple/multipart) because simple uploads cap at 5 MB and our
    validated max is 20 MB (docs/adr/003-google-shared-drive-storage.md).
    """
    metadata = {"name": os.path.basename(filename), "parents": [folder_id]}
    init = _authorized_request(
        f"{_UPLOAD_ENDPOINT}?uploadType=resumable&supportsAllDrives=true",
        method="POST",
        data=json.dumps(metadata).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=UTF-8"},
    )
    with urllib.request.urlopen(init, timeout=10) as resp:
        session_url = resp.headers["Location"]
    put = _authorized_request(
        session_url,
        method="PUT",
        data=data,
        headers={"Content-Length": str(len(data))},
    )
    with urllib.request.urlopen(put, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["id"]


def delete_file(file_id: str) -> None:
    """Delete a Drive file by id (Shared-Drive aware), best-effort.

    The row deletion has already succeeded by the time Django's FileField
    post-delete signal reaches us, so nothing here may raise: a 404/410 means
    the object is already gone (goal reached), any other transport/HTTP error
    is transient, and a failed token mint is the same kind of outage. Every
    failure is logged and swallowed.
    """
    try:
        req = _authorized_request(
            f"https://www.googleapis.com/drive/v3/files/{file_id}?supportsAllDrives=true",
            method="DELETE",
        )
        urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as error:
        if error.code in (404, 410):
            logger.info("Drive file %s already gone (HTTP %s).", file_id, error.code)
        else:
            logger.warning(
                "Drive delete failed for %s (HTTP %s); left as-is.", file_id, error.code
            )
    except (urllib.error.URLError, OSError) as error:
        logger.warning("Drive delete unreachable for %s (%s); left as-is.", file_id, error)
    except Exception as error:
        # Token minting and friends: still best-effort, but never silent.
        logger.warning("Drive delete skipped for %s (%s); left as-is.", file_id, error)


def is_folder_mime(mime_type: str) -> bool:
    """True for a Drive folder mimeType (single source of truth)."""
    return mime_type == _FOLDER_MIME


def list_children(folder_id: str = ""):
    """List one Drive folder's children for the browse picker.

    Returns `(parent_id, results, truncated)`:

    - `folder_id` empty -> the configured root (`GOOGLE_DRIVE_FOLDER_ID`, else
      `None` when only `GOOGLE_DRIVE_SHARED_DRIVE_ID` is set -> Shared Drive root).
    - `results` is a list of dicts: {id, name, mimeType, isFolder, url}.
    - `truncated` is True when Drive returned a `nextPageToken` we did not follow.

    A Drive API error propagates as `HTTPError` (the view maps it to 502); it is
    intentionally NOT swallowed like `fetch_metadata` — a browse miss must be
    honest, not a fake empty folder. The caller MUST have checked
    `is_configured()` first; this function mints a token (network).
    """
    parent = folder_id or settings.GOOGLE_DRIVE_FOLDER_ID or None
    params = {
        "pageSize": str(_BROWSE_PAGE_SIZE),
        "fields": _LIST_FIELDS,
        "orderBy": "folder,name",
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
        "q": f"'{parent}' in parents and trashed=false" if parent else "trashed=false",
    }
    shared_drive_id = settings.GOOGLE_DRIVE_SHARED_DRIVE_ID
    if shared_drive_id:
        params["driveId"] = shared_drive_id
        params["corpora"] = "drive"
    url = f"{_LIST_ENDPOINT}?{urllib.parse.urlencode(params)}"
    req = _authorized_request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    results = [
        {
            "id": f["id"],
            "name": f.get("name", ""),
            "mimeType": f.get("mimeType", ""),
            "isFolder": is_folder_mime(f.get("mimeType", "")),
            "url": (
                folder_view_url(f["id"])
                if is_folder_mime(f.get("mimeType", ""))
                else file_view_url(f["id"])
            ),
        }
        for f in payload.get("files", [])
    ]
    return parent, results, bool(payload.get("nextPageToken"))
