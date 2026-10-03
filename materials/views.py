from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from .models import Material
from .permissions import IsLecturerOrAdmin
from .serializers import MaterialSerializer


class MaterialListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/v1/material/ — list+search (auth) and upload (lecturer/admin)."""

    queryset = Material.objects.select_related("owner")
    serializer_class = MaterialSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ("title", "description")
    ordering_fields = ("created_at", "updated_at", "title")
    ordering = ("-created_at",)

    def get_permissions(self):
        # Reads are open to any authenticated user; writes are role-gated.
        if self.request.method == "POST":
            return [IsLecturerOrAdmin()]
        return [permissions.IsAuthenticated()]


class MaterialDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/PUT/DELETE /api/v1/material/{id}/."""

    queryset = Material.objects.select_related("owner")
    serializer_class = MaterialSerializer
    # JSONParser lets metadata-only PATCH/PUT through without a file re-upload.
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsLecturerOrAdmin()]
        return [permissions.IsAuthenticated()]
