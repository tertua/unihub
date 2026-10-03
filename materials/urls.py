from django.urls import path

from .views import MaterialDetailView, MaterialListCreateView

urlpatterns = [
    path("", MaterialListCreateView.as_view(), name="material-list"),
    path("<int:pk>/", MaterialDetailView.as_view(), name="material-detail"),
]
