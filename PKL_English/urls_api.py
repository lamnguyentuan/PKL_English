from django.urls import path, include

urlpatterns = [
    path("study/", include("study.api.urls")),
    path("users/", include("users.api.urls")),
    path("speaking/", include("speaking.api.urls")),
]
