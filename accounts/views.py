from rest_framework import generics, permissions

from .serializers import MeSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — public, roles limited to student/lecturer."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/auth/me/ — the profile of the token's owner."""

    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Always the requester: there is no user id in the URL to tamper with.
        return self.request.user
