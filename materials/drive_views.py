"""Browse endpoint: list a Shared Drive folder's children for the file picker.

Read-only and thin (AGENTS.md §6): all Drive logic lives in `materials/drive.py`
(`list_children`). The only URL wiring for this app besides the material
resource; included at the singular `/api/v1/drive/` segment.
"""

import urllib.error

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import drive
from .serializers import DriveBrowseResponseSerializer


class DriveBrowseView(APIView):
    """GET /api/v1/drive/ — list Shared Drive folder children for the picker.

    Read-only: it never mutates Drive and creates no material. Returns 503 when
    the Drive integration is unconfigured (zero outbound calls in that case);
    a Drive API error becomes 502 rather than a fake empty list.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="parent",
                description="Drive folder id to list; omit for the configured root.",
                required=False,
                type=str,
            )
        ],
        responses={200: DriveBrowseResponseSerializer},
    )
    def get(self, request):
        if not drive.is_configured():
            return Response(
                {"detail": "Drive integration is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        parent = request.query_params.get("parent") or ""
        try:
            resolved_parent, results, truncated = drive.list_children(parent)
        except urllib.error.HTTPError:
            # The caller asked to see a folder and did not get it: fail honestly
            # instead of returning an empty (lying) list.
            return Response(
                {"detail": "Drive API error."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        payload = {
            "configured": True,
            "parent": resolved_parent,
            "results": results,
            "truncated": truncated,
        }
        return Response(DriveBrowseResponseSerializer(payload).data)
