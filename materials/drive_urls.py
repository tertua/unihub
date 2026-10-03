from django.urls import path

from .drive_views import DriveBrowseView

app_name = "drive"

urlpatterns = [
    path("", DriveBrowseView.as_view(), name="drive-browse"),
]
